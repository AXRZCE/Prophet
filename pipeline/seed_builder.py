"""
seed_builder.py — Construct standardized seed documents for Prophet Phase 1.

Searches for event context, assembles a structured markdown seed doc,
and scores quality. Priority chain:

  1. SearXNG (primary — localhost:8088)
  2. Source list fallback (manual URLs)

Seed quality labels:
  high   = 5+ relevant sources, clear resolution rules
  medium = 3-4 sources, mostly clear context
  low    = <3 sources or unclear narratives
  manual = human-edited seed (manual_edits=True required)

Hard rules:
  - Manual seed edits must be flagged as manual_edits=true.
  - seed_doc_hash must be stored and versioned.
  - Do not present manual input as automated data.

Author: ClawBot + Akshar
Date: May 12, 2026
Version: v0.1
"""

import hashlib
import json
import os
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, List, Optional


SEARXNG_URL = os.environ.get("SEARXNG_URL", "http://localhost:8088/search")
SEED_BUILDER_VERSION = "v0.1"


# --- Seed Document Template ---

SEED_TEMPLATE = """# Event Seed Document

**IMPORTANT LANGUAGE INSTRUCTION: All analysis, reports, and agent communication in this simulation MUST be written in English. Do NOT generate output in any other language.**

## Market Question
{market_question}

## Resolution Criteria
{resolution_criteria}

## Current Market State
- YES price: {price_yes}
- NO price: {price_no}
- Volume: ${volume_usd}
- Liquidity: ${liquidity_usd}
- Snapshot time: {snapshot_time}

## Key Facts
{key_facts}

## Timeline
{timeline}

## Stakeholders
| Stakeholder | Incentive | Likely Position |
|---|---|---|
{stakeholders}

## Current Narratives

### YES Narrative
{yes_narrative}

### NO Narrative
{no_narrative}

## Key Uncertainties
{key_uncertainties}

## Source List
{source_list}

## Seed Builder Notes
- Search method: {search_method}
- Manual edits: {manual_edits}
- Source count: {source_count}
- Seed hash: {seed_hash}
- Seed builder version: {seed_builder_version}
"""


def _search_searxng(query: str, count: int = 5) -> List[Dict]:
    """Search SearXNG for news articles."""
    params = urllib.parse.urlencode({
        "q": query,
        "format": "json",
        "categories": "news",
        "engines": "google,duckduckgo",
        "language": "en",
    })
    url = f"{SEARXNG_URL}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])[:count]
            return [{"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", r.get("snippet", ""))} for r in results]
    except Exception as e:
        print(f"SearXNG search failed: {e}")
        return []


def _classify_quality(source_count: int, has_clear_criteria: bool, has_narratives: bool) -> str:
    """Classify seed quality based on source richness."""
    if source_count >= 5 and has_clear_criteria and has_narratives:
        return "high"
    elif source_count >= 3:
        return "medium"
    else:
        return "low"


def build_seed(
    market_question: str,
    resolution_criteria: str,
    price_yes: float,
    price_no: float = None,
    volume_usd: float = 0,
    liquidity_usd: float = 0,
    key_facts: List[str] = None,
    timeline: str = "",
    yes_narrative: str = "",
    no_narrative: str = "",
    key_uncertainties: List[str] = None,
    source_urls: List[str] = None,
    manual_edits: bool = False,
    snapshot_time: str = "",
) -> Dict:
    """
    Build a standardized seed document from event metadata.

    Args:
        market_question: Exact Polymarket question
        resolution_criteria: Platform resolution rules
        price_yes: Current YES price
        price_no: Current NO price
        volume_usd: Market volume
        liquidity_usd: Market liquidity
        key_facts: List of key factual statements
        timeline: Markdown timeline text
        yes_narrative: Why YES may happen
        no_narrative: Why NO may happen
        key_uncertainties: List of uncertainty statements
        source_urls: List of source URLs used
        manual_edits: True if human-edited
        snapshot_time: ISO timestamp of market snapshot

    Returns:
        {
            "seed_doc_text": "...",
            "seed_doc_hash": "...",
            "source_urls": [...],
            "source_count": 3,
            "source_time_window": "last 7 days",
            "seed_quality": "high" | "medium" | "low" | "manual",
            "manual_edits": false,
            "seed_builder_version": "v0.1"
        }
    """
    if price_no is None:
        price_no = round(1.0 - price_yes, 4)
    if key_facts is None:
        key_facts = []
    if key_uncertainties is None:
        key_uncertainties = []
    if source_urls is None:
        source_urls = []

    source_count = len(source_urls)

    # Format source list
    source_list = "\n".join(f"- {url}" for url in source_urls) if source_urls else "- No sources listed"

    # Format facts
    facts_text = "\n".join(f"- {f}" for f in key_facts) if key_facts else "- [Auto-generated — search for current facts about this event]"

    # Format uncertainties
    uncertainties_text = "\n".join(f"- {u}" for u in key_uncertainties) if key_uncertainties else "- Resolution timing\n- External factors\n- Data availability"

    # Format stakeholder placeholder
    stakeholders_text = "| [Identify key stakeholders] | [What they want] | [YES or NO] |"

    # Format timeline
    timeline_text = timeline if timeline else "- [Add key dates and milestones]"

    # Quality classification
    has_clear_criteria = len(resolution_criteria) > 20
    has_narratives = len(yes_narrative) > 10 and len(no_narrative) > 10
    quality = _classify_quality(source_count, has_clear_criteria, has_narratives)
    if manual_edits:
        quality = "manual"

    search_method = "manual_urls" if manual_edits else "template_fill"

    # Build the seed document
    seed_doc = SEED_TEMPLATE.format(
        market_question=market_question,
        resolution_criteria=resolution_criteria,
        price_yes=price_yes,
        price_no=price_no,
        volume_usd=f"{volume_usd:,.0f}",
        liquidity_usd=f"{liquidity_usd:,.0f}",
        snapshot_time=snapshot_time or "auto-generated",
        key_facts=facts_text,
        timeline=timeline_text,
        stakeholders=stakeholders_text,
        yes_narrative=yes_narrative or "[To be filled — search for YES-case arguments]",
        no_narrative=no_narrative or "[To be filled — search for NO-case arguments]",
        key_uncertainties=uncertainties_text,
        source_list=source_list,
        search_method=search_method,
        manual_edits=str(manual_edits).lower(),
        source_count=source_count,
        seed_hash="pending",  # computed after
        seed_builder_version=SEED_BUILDER_VERSION,
    )

    # Compute final hash
    seed_hash = hashlib.sha256(seed_doc.encode()).hexdigest()[:16]
    seed_doc = seed_doc.replace("seed_hash: pending", f"seed_hash: {seed_hash}")

    return {
        "seed_doc_text": seed_doc,
        "seed_doc_hash": seed_hash,
        "source_urls": source_urls,
        "source_count": source_count,
        "source_time_window": "last 7 days",
        "seed_quality": quality,
        "manual_edits": manual_edits,
        "seed_builder_version": SEED_BUILDER_VERSION,
    }


def build_seed_from_search(
    market_question: str,
    resolution_criteria: str,
    price_yes: float,
    price_no: float = None,
    volume_usd: float = 0,
    liquidity_usd: float = 0,
    manual_edits: bool = False,
) -> Dict:
    """
    Build a seed document with SearXNG search enrichment.

    Searches for news articles, extracts key facts and source URLs,
    then assembles the seed doc.

    Args: Same as build_seed, minus the manual text fields.

    Returns: Same seed dict as build_seed.
    """
    # Search for context
    search_query = market_question[:200]  # Use market question as search
    results = _search_searxng(search_query)

    source_urls = [r["url"] for r in results if r.get("url")]
    key_facts = [r["snippet"][:200] for r in results if r.get("snippet")]
    timeline = ""  # SearXNG results don't give timeline — user fills if needed

    # Build basic narratives from search results
    yes_facts = [f for f in key_facts if any(kw in f.lower() for kw in ["will", "likely", "expected", "confirmed", "approved", "success"])]
    no_facts = [f for f in key_facts if any(kw in f.lower() for kw in ["risk", "delay", "uncertain", "challenge", "dispute", "fail"])]

    yes_narrative = "; ".join(yes_facts[:3]) if yes_facts else ""
    no_narrative = "; ".join(no_facts[:3]) if no_facts else ""

    return build_seed(
        market_question=market_question,
        resolution_criteria=resolution_criteria,
        price_yes=price_yes,
        price_no=price_no,
        volume_usd=volume_usd,
        liquidity_usd=liquidity_usd,
        key_facts=key_facts[:8],
        timeline=timeline,
        yes_narrative=yes_narrative,
        no_narrative=no_narrative,
        source_urls=source_urls[:8],
        manual_edits=manual_edits,
    )
