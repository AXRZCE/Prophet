"""
market_scanner.py — Polymarket event discovery for Prophet Phase 1.

Uses Polymarket's Gamma API (public, no auth). Browser-like headers required.
Fetches events by tag, extracts nested market prices, applies Phase 1 filters.

Filters:
  - Binary YES/NO only
  - Volume > $50K
  - Probability between 15% and 85%
  - Exclude sports, elections, macro, celebrity (blocked keywords)
  - Prefer crypto/regulatory/company narrative events

Hard rule: Market snapshot captured at simulation trigger time, not discovery time.
            This module DISCOVERS events. logger.py creates the snapshot at trigger time.

Author: ClawBot + Akshar
Date: May 12, 2026
Version: v0.2
"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone
import re

from typing import Dict, List, Optional


GAMMA_API = os.environ.get("POLYMARKET_GAMMA_URL", "https://gamma-api.polymarket.com")

# Phase 1 filters
MIN_VOLUME_USD = 50_000
MIN_PROBABILITY = 0.15
MAX_PROBABILITY = 0.85
MIN_DAYS_TO_RESOLVE = 7
MAX_DAYS_TO_RESOLVE = 60

# Tags to search for Phase 1 categories
DISCOVERY_TAGS = ["crypto", "technology", "business", "regulation"]

# Blocked keywords (Phase 1)
BLOCKED_KEYWORDS = [
    "sports", "nba", "nfl", "mlb", "premier league", "champions league",
    "soccer", "hockey", "tennis", "boxing", "ufc", "fifa", "world cup",
    "election", "senate", "congress", "governor", "president", "nominee",
    "cpi", "inflation", "gdp", "unemployment", "fed rate", "fomc",
    "celebrity", "kardashian", "meme", "esports", "lol", "valorant",
]

# Phase 1 category keywords
CATEGORY_KEYWORDS = {
    "crypto_protocol": [r"\bcrypto\b", r"\bblockchain\b", r"\bprotocol\b", r"\bupgrade\b", r"\bfork\b", r"\bethereum\b", r"\bsolana\b", r"\bmainnet\b", r"\btestnet\b"],
    "crypto_regulatory": [r"\bsec\b", r"\betf\b", r"\bapproval\b", r"\bregulation\b", r"\bcompliance\b", r"\bcftc\b", r"\bxrp\b", r"\blawsuit\b"],
    "company_product": [r"\brevenue\b", r"\barr\b", r"\bearnings\b", r"\blaunch\b", r"\bproduct\b", r"\bmerger\b", r"\bacquisition\b", r"\bipo\b", r"\bvaluation\b", r"\bmarket cap\b", r"\bsubscriber\b"],
    "ai_narrative": [r"\bai\b", r"\bartificial intelligence\b", r"\bgpt\b", r"\bclaude\b", r"\bllm\b", r"\banthropic\b", r"\bopenai\b", r"\bdeepseek\b", r"\bgemini\b", r"\bbenchmark\b"],
}


def _api(path: str, params: dict = None) -> dict:
    """Call Polymarket Gamma API."""
    url = f"{GAMMA_API}{path}"
    if params:
        parts = []
        for k, v in params.items():
            if isinstance(v, list):
                for vv in v:
                    parts.append(f"{k}={vv}")
            else:
                parts.append(f"{k}={v}")
        url += "?" + "&".join(parts)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://polymarket.com",
        "Referer": "https://polymarket.com/",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}"}
    except Exception as e:
        return {"error": str(e)}



def _parse_json_str(val):
    """Polymarket returns some fields as JSON strings, not parsed lists."""
    if isinstance(val, str) and val.startswith('['):
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            pass
    return val if isinstance(val, list) else []

def _match_category(title: str, tags: List[str] = None) -> Optional[str]:
    """Classify an event using word-boundary regex matching."""
    text = (title + " " + " ".join(tags or [])).lower()
    for category, patterns in CATEGORY_KEYWORDS.items():
        if any(re.search(p, text) for p in patterns):
            return category
    return None


def _is_blocked(title: str) -> bool:
    text = title.lower()
    for kw in BLOCKED_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", text):
            return True
    return False


def scan_markets(limit: int = 20) -> List[Dict]:
    """
    Scan Polymarket for candidate events matching Phase 1 criteria.

    Uses /markets endpoint with client-side filtering. Fetches up to
    200 markets sorted by volume and applies Phase 1 filters.

    Returns list of candidate event dicts for use with run_calibration.py.
    """
    candidates = []
    now = datetime.now(timezone.utc)
    seen = set()

    # Fetch markets — the main endpoint for binary YES/NO markets
    resp = _api("/markets", {
        "active": "true", "closed": "false",
        "limit": "200", "order": "volume", "ascending": "false",
    })

    if "error" in resp:
        print(f"Polymarket API error: {resp['error']}")
        return candidates

    markets_list = resp if isinstance(resp, list) else []

    for m in markets_list:
        if len(candidates) >= limit:
            break

        title = m.get("question", "")
        if not title or _is_blocked(title):
            continue

        # Parse prices (Polymarket returns these as JSON strings)
        prices = _parse_json_str(m.get("outcomePrices", []))
        outcomes = _parse_json_str(m.get("outcomes", []))

        # Binary YES/NO filter
        if len(prices) != 2 or outcomes not in (["Yes", "No"], ["YES", "NO"], ["yes", "no"]):
            continue

        try:
            price_yes = float(prices[0])
            price_no = float(prices[1])
        except (ValueError, TypeError):
            continue

        if price_yes < MIN_PROBABILITY or price_yes > MAX_PROBABILITY:
            continue

        # Volume filter
        volume = float(m.get("volumeNum", m.get("volume", 0)))
        if volume < MIN_VOLUME_USD:
            continue

        # Category match
        category = _match_category(title)
        if not category:
            continue

        # Deduplicate
        condition_id = m.get("conditionId", "")
        if condition_id in seen:
            continue
        seen.add(condition_id)

        # Resolution date
        end_date_str = m.get("endDate", "")
        res_date = None
        if end_date_str:
            try:
                res_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
                days_until = (res_date - now).days
                # Soft filter — log but don't reject yet for smoke test
                if days_until < MIN_DAYS_TO_RESOLVE or days_until > MAX_DAYS_TO_RESOLVE:
                    pass  # Still include for smoke test
            except (ValueError, TypeError):
                pass

        liquidity = float(m.get("liquidityNum", m.get("liquidity", 0)))
        resolution_criteria = m.get("resolutionSource", m.get("description", ""))
        slug = m.get("slug", "")

        candidates.append({
            "external_market_id": condition_id or m.get("id", ""),
            "market_title": title,
            "market_url": f"https://polymarket.com/event/{slug}" if slug else "",
            "category": category,
            "price_yes": round(price_yes, 4),
            "price_no": round(price_no, 4),
            "volume_usd": volume,
            "liquidity_usd": liquidity,
            "expected_resolution_time": res_date.isoformat() if res_date else None,
            "resolution_criteria": (resolution_criteria or "")[:500],
            "tags": [],
        })

    return candidates


def get_market_by_id(event_id: str) -> Optional[Dict]:
    """Fetch a single event by its condition ID or slug."""
    # Try events endpoint first
    resp = _api(f"/events/{event_id}")
    if "error" not in resp:
        e = resp if isinstance(resp, dict) else {}
        title = e.get("title", "")
        volume = float(e.get("volume", 0))
        liquidity = float(e.get("liquidity", 0))
        markets = e.get("markets", [])
        if markets:
            m = markets[0]
            prices = m.get("outcomePrices", [])
            price_yes = float(prices[0]) if prices else 0.5
            price_no = float(prices[1]) if len(prices) > 1 else 1.0 - price_yes
            tag_list = [t.get("label", "") if isinstance(t, dict) else str(t) for t in e.get("tags", [])]
            category = _match_category(title, tag_list) or "unknown"
            return {
                "external_market_id": event_id,
                "market_title": title,
                "market_url": f"https://polymarket.com/event/{e.get('slug', '')}",
                "category": category,
                "price_yes": round(price_yes, 4),
                "price_no": round(price_no, 4),
                "volume_usd": volume,
                "liquidity_usd": liquidity,
                "expected_resolution_time": e.get("endDate"),
                "resolution_criteria": m.get("resolutionSource", ""),
                "tags": tag_list,
            }
    return None
