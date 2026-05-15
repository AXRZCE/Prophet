"""
guardrails.py — Prophet quality enforcement for divergence and seed quality.

- High-divergence detection: flags sim-market gaps >0.30
- Seed guardrails: required fields for price/culture/narrative events
- Applies warnings and exclusion flags before calibration runs.

Author: ClawBot + Akshar
Date: May 15, 2026
"""

import re
from typing import Dict, Optional, List


# ── High-Divergence Detection ──

def check_divergence(sim_forecast: float, market_price: float) -> Dict:
    """
    Check if simulation forecast diverges significantly from market price.

    Returns:
        {"high": bool, "extreme": bool, "gap": float, "action": str}
    """
    gap = abs(sim_forecast - market_price)
    result = {"high": False, "extreme": False, "gap": round(gap, 4), "action": "ok"}

    if gap > 0.50:
        result["extreme"] = True
        result["high"] = True
        result["action"] = "exclude_from_edge_claims_until_review"
    elif gap > 0.30:
        result["high"] = True
        result["action"] = "requires_rerun_and_manual_review"

    return result


# ── Seed Guardrails ──

REQUIRED_PRICE_FIELDS = [
    "current spot price",
    "threshold price",
    "distance to threshold",
    "time remaining",
    "required move %",
    "recent volatility",
    "market YES price",
    "volume",
    "liquidity",
    "source timestamp",
]

REQUIRED_CULTURE_FIELDS = [
    "confirmed facts",
    "official hints",
    "credible leaks",
    "weak rumors",
    "fan speculation",
    "market signal",
]

REQUIRED_NARRATIVE_FIELDS = [
    "resolution rules",
    "market snapshot",
    "current public narrative",
    "stakeholders",
    "incentives",
    "credible catalysts",
    "counterarguments",
    "known unknowns",
    "source list",
    "source timestamps",
]


def classify_event_type(market_title: str, category: str = "") -> str:
    """Classify event as price, culture, or narrative."""
    title_lower = market_title.lower()
    cat_lower = (category or "").lower()

    # Price/threshold patterns
    price_patterns = [
        r"\$\d+", r"above\s+\d+", r"below\s+\d+", r"between\s+\d",
        r"price\s+of", r"close\s+at", r"close\s+above",
        r"approval\s+rating\s+(above|below|between)",
        r"^\d+\.?\d*\s*%",
    ]
    for pat in price_patterns:
        if re.search(pat, title_lower):
            return "price"

    # Culture/rumor patterns
    culture_patterns = [
        r"(featured|feat\.|collab|album|song|artist|movie|netflix|survivor|eliminat)",
        r"(will.*announce|will.*release|will.*drop|will.*launch.*(album|song))",
    ]
    for pat in culture_patterns:
        if re.search(pat, title_lower):
            return "culture"

    # Default: narrative
    return "narrative"


def check_seed_quality(seed_doc_text: str, market_title: str, category: str = "") -> Dict:
    """
    Check if seed document contains required fields for its event type.

    Returns:
        {"type": str, "quality": str, "missing_fields": [...], "warnings": [...]}
    """
    event_type = classify_event_type(market_title, category)
    required = {
        "price": REQUIRED_PRICE_FIELDS,
        "culture": REQUIRED_CULTURE_FIELDS,
        "narrative": REQUIRED_NARRATIVE_FIELDS,
    }.get(event_type, REQUIRED_NARRATIVE_FIELDS)

    doc_lower = seed_doc_text.lower()
    missing = []

    # Check narrative/structural fields
    for field in required:
        # Simple substring match for field presence
        search_term = field.replace(" %", "").replace("?", "").replace("  ", " ")
        keywords = search_term.split()
        # Check if at least one keyword from the field appears near structured content
        found = any(kw in doc_lower for kw in keywords)
        if not found:
            missing.append(field)

    warnings = []
    quality = "ok"

    if len(missing) > len(required) * 0.5:
        quality = "low"
        warnings.append(f"Missing {len(missing)}/{len(required)} required fields for {event_type} event")
    elif len(missing) > 0:
        quality = "partial"
        warnings.append(f"Missing {len(missing)}/{len(required)} fields: {missing[:3]}...")

    # Specific price event: check if current price is present
    if event_type == "price":
        # Look for a dollar amount or price reference
        has_price = bool(re.search(r'\$\d[\d,.]*', doc_lower) or re.search(r'\d+\.?\d*\s*(usd|usd/lb|dollars)', doc_lower))
        if not has_price:
            quality = "insufficient_numeric_context"
            warnings.append("CRITICAL: No price value found in seed. Do not run simulation.")

    if event_type == "culture":
        # Warn about rumor-heavy seeds
        rumor_count = sum(1 for word in ["rumor", "speculation", "alleged", "could", "might", "possibly", "maybe"] if word in doc_lower)
        if rumor_count >= 5:
            warnings.append("Seed is rumor/speculation-heavy. Max forecast cap at 0.70 recommended.")

    return {
        "type": event_type,
        "quality": quality,
        "missing_fields": missing,
        "warnings": warnings,
        "should_skip": quality == "insufficient_numeric_context",
    }


# ── Post-Forecast Quality Check ──

def post_forecast_check(
    sim_forecast: float,
    market_price: float,
    seed_quality: Dict,
    event_type: str,
) -> Dict:
    """
    Combined post-forecast quality check.

    Returns: {"pass": bool, "flags": [...], "actions": [...]}
    """
    flags = []
    actions = []

    # Divergence check
    div = check_divergence(sim_forecast, market_price)
    if div["extreme"]:
        flags.append(f"EXTREME_DIVERGENCE: gap={div['gap']:.3f}")
        actions.append("exclude_from_edge_claims_until_review")
    elif div["high"]:
        flags.append(f"HIGH_DIVERGENCE: gap={div['gap']:.3f}")
        actions.append("requires_rerun_and_manual_review")

    # Market price copy check
    if abs(sim_forecast - market_price) < 0.01:
        flags.append("MARKET_PRICE_COPY: forecast=market")
        actions.append("exclude_from_scoring")

    # Culture overconfidence
    if event_type == "culture" and sim_forecast > 0.70:
        flags.append(f"CULTURE_OVERCONFIDENCE: forecast={sim_forecast:.2f} on culture event")
        actions.append("downgrade_confidence")

    # Seed quality warnings
    if seed_quality.get("should_skip"):
        flags.append("SEED_INSUFFICIENT: missing critical numeric context")
        actions.append("do_not_score")

    return {
        "pass": "extreme" not in [a for a in actions if "extreme" in a or "skip" in a or "do_not" in a],
        "flags": flags,
        "actions": list(set(actions)),
    }
