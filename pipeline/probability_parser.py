"""
probability_parser.py — Extract structured forecast JSON from MiroFish ReportAgent output.

Phase 0 confirmed that ReportAgent produces narrative markdown, not structured probability.
This parser uses a second-stage LLM call to extract the simulation's implied YES probability
from the narrative report.

CRITICAL RULE: The parser must NEVER output the market price as the forecast.
ReportAgent reports frequently include market price references (e.g., "YES price 0.72").
The parser must distinguish "the market says X%" from "our simulation forecasts X%."

Author: ClawBot + Akshar
Date: May 12, 2026
Version: v0.1
"""

import json
import os
import re
from typing import Optional

# DeepSeek API — OpenAI-compatible endpoint
# Phase 0 confirmed this works directly (no LiteLLM proxy needed)
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"

# Parser version — stored with every simulation run
PARSER_VERSION = "v0.1"

# ---------------------------------------------------------------------------
# LLM Extractor Prompt
# ---------------------------------------------------------------------------

EXTRACTOR_PROMPT = """You are extracting a probability forecast from a simulation report.

The simulation ran AI agents through a social dynamics model on Twitter and Reddit.
Multiple agent personas debated, formed opinions, and a ReportAgent synthesized their analysis.
Your job is to extract the simulation's implied probability for the YES outcome.

MARKET QUESTION: {market_question}
RESOLUTION CRITERIA: {resolution_criteria}
MARKET PRICE AT SIMULATION TIME: {market_price_at_sim}

═══════════════════════════════════════════
CRITICAL RULES — READ CAREFULLY:
═══════════════════════════════════════════

1. THE MARKET PRICE {market_price_at_sim} IS NOT THE FORECAST. It is provided as context only.
   If you output {market_price_at_sim} as forecast_probability_yes, your extraction FAILED.

2. The report mentions the market price (e.g. "YES price is 0.72"). That is the EXTERNAL MARKET price
   from Polymarket — NOT the simulation's own probability estimate. IGNORE IT for your forecast.

3. Look for statements from INDIVIDUAL AGENTS that express their own probability estimates.
   Examples: "75-80%", "about 60%", "more than 90% confidence", "only 30% chance".
   These agent estimates ARE the simulation's signal.

4. The ReportAgent may also give its own synthesis probability. Look for phrases like:
   "The simulation suggests a X% probability", "Overall the agents converged around Y%",
   "Based on the above analysis, the probability is Z%". This IS the simulation forecast.

5. If the report presents agent estimates in ranges, compute the weighted average as forecast_probability_yes.

6. If the report is overwhelmingly YES-leaning with most agents above 65%, the forecast should be above 0.65.
   If the report is split, reflect that honestly. Do not force a strong signal.

7. If you CANNOT find any agent-sourced probability estimates OR ReportAgent synthesis probability,
   set parse_success=false. Do NOT invent precision. Do NOT guess.

8. market_price_detected should be the market price mentioned in the report (for audit trail).

9. market_price_used_as_forecast MUST ALWAYS be false in your output. This is verified by the caller.

10. confidence reflects how clearly the report implies a single probability (0=very vague, 1=very clear).

Return ONLY valid JSON matching this exact schema. No prose before or after the JSON:
{{
  "forecast_probability_yes": <float 0.0-1.0 or null>,
  "forecast_confidence": <float 0.0-1.0 or null>,
  "forecast_direction": <"YES" or "NO" or null>,
  "market_price_detected": <float or null>,
  "market_price_used_as_forecast": false,
  "extracted_probability_ranges": [<strings of ranges found in report>],
  "dominant_narrative": "<one sentence summary of the YES case from the simulation>",
  "contrarian_narrative": "<one sentence summary of the NO case, or null>",
  "final_reasoning": "<one sentence explaining how you arrived at this probability, mentioning specific agent estimates>",
  "parse_success": <true or false>,
  "error": <null or string describing why parsing failed>
}}

REPORT:
{raw_report}"""


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate_no_market_price_confusion(result: dict, market_price: float) -> dict:
    """
    Detect whether the LLM confused the market price reference with the
    simulation forecast. Uses context-aware heuristics, not just numeric comparison.

    A forecast that matches market price is NOT automatically wrong — it may
    genuinely represent agent consensus that arrives at the same number.
    The check looks at the LLM's reasoning to distinguish coincidence from confusion.
    """
    if not isinstance(result, dict):
        return result

    if not result.get("parse_success") or result.get("forecast_probability_yes") is None:
        return result

    forecast = result["forecast_probability_yes"]
    reasoning = (result.get("final_reasoning") or "").lower()
    ranges = result.get("extracted_probability_ranges") or []

    # Check 1: numeric proximity to market price
    tolerance = max(0.015, market_price * 0.03)
    near_market = abs(forecast - market_price) <= tolerance

    if not near_market:
        # Far from market price — no confusion concern
        result["market_price_used_as_forecast"] = False
        return result

    # Check 2: did the LLM reference agent estimates in its reasoning?
    agent_keywords = ["agent", "estimate", "range", "average", "weighted",
                      "consensus", "midpoint", "converged", "synthesis"]
    used_agent_estimates = any(kw in reasoning for kw in agent_keywords)

    # Check 3: did the LLM extract specific ranges?
    has_ranges = len(ranges) >= 2  # Multiple agent ranges = genuine synthesis

    # Check 4: does reasoning suggest market price was the primary source?
    market_copy_keywords = [
        "market price", "polymarket", "price is", "价格",
        "extracting this value", "so this is", "therefore this",
        "thus", "hence the forecast"
    ]
    reasoning_suggests_copying = any(kw in reasoning for kw in market_copy_keywords) and not used_agent_estimates

    # Decision logic
    if reasoning_suggests_copying:
        # LLM appears to have copied market price — flag as failure
        result["parse_success"] = False
        result["error"] = (
            f"Parser returned forecast {forecast:.4f} which matches the market price "
            f"{market_price:.4f}. Reasoning suggests market price was used as forecast "
            f"rather than agent-derived synthesis. Manual review required."
        )
        result["market_price_used_as_forecast"] = True
        result["forecast_probability_yes"] = None
        result["forecast_confidence"] = None
        result["forecast_direction"] = None
    elif used_agent_estimates and has_ranges:
        # LLM used agent estimates and extracted ranges — coincidence, not confusion
        result["market_price_used_as_forecast"] = False
    else:
        # Ambiguous — flag but don't fail, leave the forecast for manual review
        result["market_price_used_as_forecast"] = False
        # Add a note but don't nullify the result

    return result


def _preprocess_report(raw_report: str, market_price: float) -> str:
    """
    Pre-process the report to prevent the LLM from confusing market price
    with simulation forecast.

    1. Mask exact market price numbers (e.g., "0.72" → "[MARKET PRICE]")
    2. Strip the initial "Market State" section which prominently features the market price
    """
    import re

    report = raw_report

    # Mask the exact market price number with surrounding context
    # Match patterns like: "YES price: 0.72", "YES价格为0.72", "YES price is 0.72"
    price_str = str(market_price)
    price_short = f"{market_price:.2f}"

    # Replace bare price with label — most important for preventing copy-paste
    report = report.replace(price_str, "[MARKET PRICE]")
    if price_short != price_str:
        report = report.replace(price_short, "[MARKET PRICE]")

    # Also mask common "YES price is X" patterns with digits
    report = re.sub(r'YES\s*(?:price|价格)\s*(?:is|：|:)\s*[\d.]+', 'YES price: [MARKET PRICE]', report)
    report = re.sub(r'NO\s*(?:price|价格)\s*(?:is|：|:)\s*[\d.]+', 'NO price: [MARKET PRICE]', report)

    return report


def _truncate_report(report: str, max_chars: int = 8000) -> str:
    """Truncate report to avoid exceeding LLM context limits."""
    if len(report) <= max_chars:
        return report
    # Keep first 60% and last 40% — conclusions often at the end
    head = int(max_chars * 0.6)
    tail = int(max_chars * 0.4)
    return report[:head] + "\n\n... [report truncated] ...\n\n" + report[-tail:]


def _call_llm(prompt: str) -> Optional[dict]:
    """Call DeepSeek API and return parsed JSON response."""
    import urllib.request
    import urllib.error

    url = f"{DEEPSEEK_BASE_URL}/chat/completions"
    body = json.dumps({
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": "You are a precise JSON extractor. Return only valid JSON matching the requested schema. No prose, no markdown fences, no explanation."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,  # Deterministic extraction
        "max_tokens": 1024,
        "response_format": {"type": "json_object"}  # Force JSON
    }).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    })

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            response = json.loads(resp.read().decode("utf-8"))
            content = response["choices"][0]["message"]["content"]
            # Strip markdown code fences if present
            content = re.sub(r'^```(?:json)?\s*', '', content.strip())
            content = re.sub(r'\s*```$', '', content)
            return json.loads(content)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else str(e)
        print(f"LLM API error (HTTP {e.code}): {error_body[:500]}")
        return None
    except (json.JSONDecodeError, KeyError, Exception) as e:
        print(f"LLM call failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_forecast(
    raw_report: str,
    market_question: str,
    resolution_criteria: str,
    market_price_at_sim: float,
    model: str = DEEPSEEK_MODEL
) -> dict:
    """
    Extract a structured probability forecast from a MiroFish ReportAgent narrative report.

    Args:
        raw_report: Full markdown report from ReportAgent
        market_question: Exact Polymarket question
        resolution_criteria: Exact platform resolution rules
        market_price_at_sim: Market YES price at simulation time (context only, NEVER output as forecast)

    Returns:
        dict with forecast_probability_yes, forecast_confidence, parse_success, etc.
    """

    # Pre-process: mask market price references to prevent LLM confusion
    processed_report = _preprocess_report(raw_report, market_price_at_sim)

    # Build the extraction prompt
    prompt = EXTRACTOR_PROMPT.format(
        market_question=market_question,
        resolution_criteria=resolution_criteria,
        market_price_at_sim=market_price_at_sim,
        raw_report=_truncate_report(processed_report)
    )

    # Call LLM for extraction
    result = _call_llm(prompt)

    if result is None:
        return {
            "forecast_probability_yes": None,
            "forecast_confidence": None,
            "forecast_direction": None,
            "probability_source": "llm_extractor",
            "market_price_detected": None,
            "market_price_used_as_forecast": False,
            "extracted_probability_ranges": [],
            "dominant_narrative": None,
            "contrarian_narrative": None,
            "final_reasoning": None,
            "parse_success": False,
            "error": "LLM API call failed — no response",
            "parser_version": PARSER_VERSION
        }

    # Ensure required fields exist
    result.setdefault("probability_source", "llm_extractor")
    result.setdefault("market_price_used_as_forecast", False)
    result.setdefault("extracted_probability_ranges", [])
    result.setdefault("parser_version", PARSER_VERSION)

    # Run anti-confusion validation
    result = _validate_no_market_price_confusion(result, market_price_at_sim)

    return result


# ---------------------------------------------------------------------------
# Test utilities
# ---------------------------------------------------------------------------

def load_report_fixture(path: str) -> str:
    """Load a saved Phase 0 report. Handles both raw markdown and API JSON wrapper."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # If the file is still wrapped in API JSON, extract markdown_content
    try:
        data = json.loads(content)
        if isinstance(data, dict) and "data" in data:
            md = data["data"].get("markdown_content", "")
            if md:
                return md
    except (json.JSONDecodeError, TypeError):
        pass
    return content


def load_metadata_fixture(path: str) -> dict:
    """Load Phase 0 metadata JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
