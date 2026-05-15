"""
kalshi_scanner.py — Read-only Kalshi market data source for Prophet Track B/C.

Purpose:
  - Market discovery (list open/closed/settled markets)
  - Market detail fetch
  - Price normalization (cents → probability 0-1)
  - Short-deadline candidate discovery (Track C)
  - Retrospective candidate discovery (Track B)
  - Resolution/status fetch

Scope: READ-ONLY. No trading, no auth for order placement, no wallet.
       All Kalshi results are reported separately from Polymarket.
       Track A remains Polymarket-only. Track B/C use Kalshi.

Price normalization rules (in priority order):
  1. Midpoint: (yes_bid + yes_ask) / 2 / 100
  2. yes_ask: yes_ask / 100
  3. last_price: last_price / 100
  4. Reject (price_source = unknown)

Author: ClawBot + Akshar
Date: May 13, 2026
Version: v0.1
"""

import json
import os
import urllib.request
import urllib.error
import urllib.parse
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional


# --- Configuration ---

KALSHI_API_BASE = os.environ.get(
    "KALSHI_API_BASE", "https://external-api.kalshi.com/trade-api/v2"
)

# Prophet category ← Kalshi category mapping
KALSHI_TO_PROPHET_CATEGORY = {
    "crypto": "crypto_protocol",
    "economics": "economic_policy",
    "politics": "economic_policy",           # regulatory/policy only
    "science & technology": "ai_narrative",
    "technology": "company_product",
    "entertainment": None,                    # excluded from Prophet
    "sports": None,
    "weather": None,
    "health": None,
    "culture": None,
}

# Blocked keywords (same as Polymarket scanner)
BLOCKED_KEYWORDS = [
    "sports", "nba", "nfl", "mlb", "premier league", "champions league",
    "soccer", "hockey", "tennis", "boxing", "ufc", "fifa", "world cup",
    "celebrity", "kardashian", "meme", "esports", "lol", "valorant",
    "oscar", "grammy", "emmy", "tony", "met gala",
]

# Narrative-friendly keywords for Track B retrospective
NARRATIVE_KEYWORDS = [
    r"\bai\b", r"\bartificial intelligence\b", r"\bgpt\b", r"\bclaude\b",
    r"\bllm\b", r"\banthropic\b", r"\bopenai\b", r"\bdeepseek\b", r"\bgemini\b",
    r"\bcrypto\b", r"\bblockchain\b", r"\bbitcoin\b", r"\bethereum\b",
    r"\betf\b", r"\bapproval\b", r"\bsec\b", r"\bregulation\b",
    r"\blaunch\b", r"\bmerger\b", r"\bacquisition\b", r"\bipo\b",
    r"\brevenue\b", r"\barr\b", r"\bmarket cap\b", r"\bvaluation\b",
    r"\btariff\b", r"\bfed\b", r"\brate\b",
]

# Track C acceptable categories (wider net, narrative false/partial)
TRACK_C_ACCEPTABLE = [
    "crypto", "economics", "politics", "science & technology",
    "technology", "weather", "sports",
]


def _api(path: str, params: dict = None) -> dict:
    """Call Kalshi public API (no auth). Returns parsed JSON."""
    url = f"{KALSHI_API_BASE}{path}"
    if params:
        parts = []
        for k, v in params.items():
            if v is not None:
                parts.append(f"{k}={urllib.parse.quote(str(v))}")
        if parts:
            url += "?" + "&".join(parts)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return {"error": f"HTTP {e.code}", "body": body[:500]}
    except Exception as e:
        return {"error": str(e)}


def _parse_kalshi_time(val) -> Optional[datetime]:
    """Parse Kalshi close_time (ISO 8601 string or Unix ms)."""
    if val is None:
        return None
    try:
        # ISO 8601 string
        if isinstance(val, str):
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        pass
    # Unix milliseconds (fallback)
    try:
        return datetime.fromtimestamp(float(val) / 1000.0, tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        return None


def _is_blocked(title: str) -> bool:
    """Check if a market title matches blocked keywords."""
    text = title.lower()
    for kw in BLOCKED_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", text):
            return True
    return False


def _is_narrative(title: str, subtitle: str = "") -> bool:
    """Check if a market title/subtitle suggests narrative content."""
    text = (title + " " + (subtitle or "")).lower()
    for pattern in NARRATIVE_KEYWORDS:
        if re.search(pattern, text):
            return True
    return False


def _map_category(kalshi_category: str) -> Optional[str]:
    """Map Kalshi category → Prophet category. Returns None if excluded."""
    cat_lower = (kalshi_category or "").strip().lower()
    return KALSHI_TO_PROPHET_CATEGORY.get(cat_lower)


class KalshiScanner:
    """
    Read-only Kalshi market data provider for Prophet Track B and Track C.

    NO trading. NO authentication for order placement.
    Pure market discovery, price normalization, and resolution fetch.
    """

    def __init__(self):
        self.base = KALSHI_API_BASE

    # ------------------------------------------------------------------
    # Price normalization
    # ------------------------------------------------------------------

    def normalize_price(self, market: dict) -> tuple:
        """
        Normalize Kalshi yes/no prices to 0-1 probability.

        Kalshi v2 API uses dollar-denominated fields:
          - yes_bid_dollars / yes_ask_dollars: bid/ask in $ (0-1)
          - last_price_dollars: last trade price in $ (0-1)

        Priority:
          1. Midpoint of yes_bid/yes_ask
          2. yes_ask
          3. last_price
          4. Unknown → reject

        Returns: (price_yes, price_no, price_source)
        """
        yes_bid = market.get("yes_bid_dollars") or market.get("yes_bid")
        yes_ask = market.get("yes_ask_dollars") or market.get("yes_ask")
        last_price = market.get("last_price_dollars") or market.get("last_price")

        def _to_prob(val):
            if val is None:
                return None
            try:
                v = float(val)
            except (ValueError, TypeError):
                return None
            # Values > 1.0 are in cents (legacy format), divide by 100
            return v / 100.0 if v > 1.0 else v

        bid = _to_prob(yes_bid)
        ask = _to_prob(yes_ask)
        last = _to_prob(last_price)

        # Priority 1: midpoint
        if bid is not None and ask is not None:
            price_yes = round((bid + ask) / 2.0, 4)
            return price_yes, round(1.0 - price_yes, 4), "midpoint"

        # Priority 2: yes_ask
        if ask is not None:
            return round(ask, 4), round(1.0 - ask, 4), "yes_ask"

        # Priority 3: last_price
        if last is not None:
            return round(last, 4), round(1.0 - last, 4), "last_price"

        # Priority 4: reject
        return 0.0, 0.0, "unknown"

    # ------------------------------------------------------------------
    # Normalize market → Prophet standard shape
    # ------------------------------------------------------------------

    def _is_binary_market(self, raw: dict) -> bool:
        """Check if market is binary YES/NO (not multi-outcome)."""
        title = (raw.get("title", "") or "").lower()
        subtitle = (raw.get("subtitle", "") or "").lower()
        yes_sub = (raw.get("yes_sub_title", "") or "").lower()

        # Multi-outcome signals: "yes X, yes Y, yes Z" pattern in title or subtitle
        # Count "yes " prefix occurrences in comma-separated title
        yes_prefix_count = len(re.findall(r'(?:^|,)\s*yes\s', title))
        if yes_prefix_count >= 2:
            return False
        
        # Check subtitle for multi-outcome
        yes_prefix_sub = len(re.findall(r'(?:^|,)\s*yes\s', subtitle))
        if yes_prefix_sub >= 2:
            return False

        # Explicit multi-outcome in yes_sub_title ("yes X, yes Y")
        if yes_sub:
            yes_prefix_sub2 = len(re.findall(r'(?:^|,)\s*yes\s', yes_sub))
            if yes_prefix_sub2 >= 2:
                return False

        return True

    def normalize_market(self, raw: dict, platform: str = "kalshi") -> dict:
        """
        Convert Kalshi raw market dict → Prophet standard shape.

        Returns None for non-binary (multi-outcome) markets.
        Output matches Polymarket scanner output for drop-in compatibility.
        """
        price_yes, price_no, price_source = self.normalize_price(raw)
        volume = float(raw.get("volume_fp", raw.get("volume", 0)))
        open_interest = float(raw.get("open_interest_fp", raw.get("open_interest", 0)))
        liquidity = max(open_interest, volume)

        ticker = raw.get("ticker", "")
        title = raw.get("title", "")
        subtitle = raw.get("subtitle", "")
        full_title = f"{title} — {subtitle}" if subtitle else title

        # Reject non-binary markets
        if not self._is_binary_market(raw):
            return None

        # Reject zero-volume or near-zero volume
        vol_raw = float(raw.get("volume_fp", raw.get("volume", 0)))
        open_int = float(raw.get("open_interest_fp", raw.get("open_interest", 0)))
        if vol_raw <= 0 and open_int <= 0:
            return None

        # Reject multi-event combos (KXMV prefix = multi-event, synthetic)
        ticker = raw.get("ticker", "")
        if ticker.startswith("KXMV") or ticker.startswith("KXMVE"):
            return None

        # Reject explicit sports/weather/entertainment categories
        kalshi_cat = (raw.get("category", "") or "").strip().lower()
        if kalshi_cat in ("sports", "weather", "entertainment", "health", "culture"):
            return None

        close_ts = raw.get("close_time")
        if close_ts is None:
            close_ts = raw.get("settlement_cutoff", raw.get("expected_resolution_date"))
        expected_resolution = _parse_kalshi_time(close_ts)

        status = raw.get("status", "unknown")
        kalshi_cat = raw.get("category", "")
        prophet_cat = _map_category(kalshi_cat) or "unknown"

        resolution_criteria = ""
        if raw.get("yes_sub_title"):
            resolution_criteria += f"YES: {raw['yes_sub_title']} "
        if raw.get("no_sub_title"):
            resolution_criteria += f"NO: {raw['no_sub_title']}"
        if raw.get("rules_primary"):
            resolution_criteria = raw["rules_primary"]

        # Build raw market data for future reference
        raw_market_data = {
            "yes_bid_dollars": raw.get("yes_bid_dollars"),
            "yes_ask_dollars": raw.get("yes_ask_dollars"),
            "last_price_dollars": raw.get("last_price_dollars"),
            "price_source": price_source,
            "volume_fp": raw.get("volume_fp"),
            "open_interest": open_interest,
            "event_ticker": raw.get("event_ticker", ""),
            "series_ticker": raw.get("series_ticker", ""),
            "subtitle": subtitle,
            "can_close_early": raw.get("can_close_early", False),
            "expected_expiration_time": raw.get("expected_expiration_time"),
            "result": raw.get("result"),
        }

        # Raw bid/ask/last in cents (for snapshot)
        def _raw_cents(val):
            try:
                return round(float(val), 4)
            except (ValueError, TypeError):
                return None

        return {
            "platform": platform,
            "external_market_id": ticker,
            "market_title": full_title[:500],
            "market_url": f"https://kalshi.com/markets/{ticker}" if ticker else "",
            "category": prophet_cat,
            "event_type": kalshi_cat,
            "price_yes": price_yes,
            "price_no": price_no,
            "volume_usd": round(volume, 2),
            "liquidity_usd": round(liquidity, 2),
            "expected_resolution_time": expected_resolution.isoformat() if expected_resolution else None,
            "resolution_criteria": (resolution_criteria or "")[:500],
            "status": status,
            "raw_market_data": raw_market_data,
            "raw_yes_bid": _raw_cents(raw.get("yes_bid_dollars", raw.get("yes_bid"))),
            "raw_yes_ask": _raw_cents(raw.get("yes_ask_dollars", raw.get("yes_ask"))),
            "raw_last_price": _raw_cents(raw.get("last_price_dollars", raw.get("last_price"))),
            "price_source": price_source,
            "tags": [],
        }

    # ------------------------------------------------------------------
    # Series discovery (for Track C weekly/short-frequency markets)
    # ------------------------------------------------------------------

    def list_series(self, frequency: str = None, category: str = None,
                    limit: int = 200, cursor: str = None) -> list[dict]:
        """
        List Kalshi series — the correct entry point for weekly/hourly/daily markets.

        Args:
            frequency: 'weekly', 'daily', 'hourly', or None for all
            category: filter by Kalshi category name
            limit: max series per page
        """
        params = {"limit": str(limit)}
        if cursor:
            params["cursor"] = cursor

        resp = _api("/series", params)
        if "error" in resp:
            print(f"Kalshi series error: {resp['error']}")
            return []

        series = resp.get("series", [])
        if not isinstance(series, list):
            return []

        results = []
        for s in series:
            freq = (s.get("frequency", "") or "").lower()
            kalshi_cat = (s.get("category", "") or "").lower()
            title = s.get("title", "")

            if not title:
                continue
            if frequency and freq != frequency.lower():
                continue
            if category and kalshi_cat != category.lower():
                continue

            prophet_cat = _map_category(kalshi_cat) or "unknown"
            results.append({
                "series_ticker": s.get("ticker", ""),
                "title": title,
                "category": kalshi_cat,
                "prophet_category": prophet_cat,
                "frequency": freq,
                "is_narrative": _is_narrative(title),
            })

        return results

    def get_markets_for_series(self, series_ticker: str,
                               status: str = "open", limit: int = 20) -> list[dict]:
        """Get normalized markets for a specific Kalshi series."""
        params = {"series_ticker": series_ticker, "limit": str(limit)}
        if status:
            params["status"] = status

        resp = _api("/markets", params)
        if "error" in resp:
            return []

        markets = resp.get("markets", [])
        normalized = []
        if isinstance(markets, list):
            for m in markets:
                nm = self.normalize_market(m, "kalshi")
                if nm is not None:
                    normalized.append(nm)
        return normalized

    def get_weekly_candidates(self, limit: int = 50) -> list[dict]:
        """
        Return weekly Kalshi markets visible under the frontend Weekly filter.

        Uses series-first discovery: list weekly-frequency series, then
        get their open markets.
        """
        weekly_series = self.list_series(frequency="weekly")
        if not weekly_series:
            print("No weekly series found")
            return []

        print(f"Found {len(weekly_series)} weekly series")

        candidates = []
        for s in weekly_series:
            if len(candidates) >= limit:
                break
            markets = self.get_markets_for_series(s["series_ticker"])
            for m in markets:
                if len(candidates) >= limit:
                    break
                candidates.append(m)

        return candidates

        return candidates

    # Backward-compat aliases
    def get_short_deadline_candidates(self, days_min=1, days_max=6):
        return self.get_track_c_candidates(days_min=days_min, days_max=days_max)

    def list_events(self, status="open", limit=100, cursor=None):
        """Backward-compat: event discovery using Kalshi events endpoint."""
        params = {"limit": str(limit), "status": status}
        if cursor:
            params["cursor"] = cursor
        resp = _api("/events", params)
        if "error" in resp:
            return []
        events = resp.get("events", [])
        if not isinstance(events, list):
            return []
        results = []
        for e in events:
            et = e.get("event_ticker", "")
            title = e.get("title", "")
            if not title or not et:
                continue
            if _is_blocked(title):
                continue
            results.append({
                "event_ticker": et,
                "title": title,
                "subtitle": e.get("sub_title", ""),
                "category": (e.get("category", "") or "").strip().lower(),
                "prophet_category": _map_category(e.get("category", "")) or "unknown",
                "is_narrative": _is_narrative(title, e.get("sub_title", "")),
            })
        return results

    def get_markets_for_event(self, event_ticker, limit=10):
        """Backward-compat: get markets for a Kalshi event."""
        params = {"event_ticker": event_ticker, "limit": str(limit)}
        resp = _api("/markets", params)
        if "error" in resp:
            return []
        markets = resp.get("markets", [])
        normalized = []
        if isinstance(markets, list):
            for m in markets:
                nm = self.normalize_market(m, "kalshi")
                if nm is not None:
                    normalized.append(nm)
        return normalized

    # ------------------------------------------------------------------
    # Market discovery (raw markets endpoint — used for broad scans)
    # ------------------------------------------------------------------

    def list_markets(self, status: str = "open", limit: int = 100,
                     cursor: str = None, max_close_ts = None,
                     min_close_ts = None, event_ticker: str = None) -> list[dict]:
        """
        Return normalized Kalshi markets (raw markets endpoint).

        Args:
            status: 'open', 'closed', 'settled', or None for all
            limit: max markets per page
            cursor: pagination cursor
            max_close_ts: max close time (ISO string or Unix ms)
            min_close_ts: min close time (ISO string or Unix ms)
            event_ticker: filter to a specific event
        """
        params = {"limit": str(limit)}
        if status:
            params["status"] = status
        if cursor:
            params["cursor"] = cursor
        if max_close_ts is not None:
            params["max_close_ts"] = str(max_close_ts)
        if min_close_ts is not None:
            params["min_close_ts"] = str(min_close_ts)
        if event_ticker:
            params["event_ticker"] = event_ticker

        resp = _api("/markets", params)
        if "error" in resp:
            print(f"Kalshi API error: {resp['error']}")
            return []

        markets = resp.get("markets", [])
        normalized = []
        if isinstance(markets, list):
            for m in markets:
                nm = self.normalize_market(m, "kalshi")
                if nm is not None:
                    normalized.append(nm)
        elif isinstance(markets, dict):
            for m in markets.values():
                nm = self.normalize_market(m, "kalshi")
                if nm is not None:
                    normalized.append(nm)
        return normalized

    def get_market_by_id(self, ticker: str) -> Optional[dict]:
        """Return one normalized Kalshi market by ticker."""
        resp = _api(f"/markets/{ticker}")
        if "error" in resp:
            print(f"Kalshi get_market_by_id error: {resp['error']}")
            return None

        market = resp.get("market", resp)
        if not market or not market.get("ticker"):
            return None

        return self.normalize_market(market, "kalshi")

    # ------------------------------------------------------------------
    # Track C — Short-deadline candidates
    # ------------------------------------------------------------------

    def get_track_c_candidates(self, days_min: int = 1,
                               days_max: int = 6) -> list[dict]:
        """
        Return short-deadline Track C stress-test candidates.

        Uses series-first discovery: finds weekly/daily/hourly series,
        fetches their markets, and filters by close_time.

        Track C allows: politics, culture, entertainment, crypto,
        commodities, economics, financials, tech, companies.
        Avoids sports if better candidates exist.
        """
        now = datetime.now(timezone.utc)
        min_dt = now + timedelta(days=days_min)
        max_dt = now + timedelta(days=days_max)

        # Track C accepted categories (wider net)
        track_c_cats = {
            "politics", "entertainment", "crypto", "economics",
            "commodities", "financials", "science and technology",
            "companies", "world", "social", "elections",
        }

        candidates = []

        # Strategy 1: Weekly series → markets (primary path)
        for freq in ("weekly",):
            series_list = self.list_series(frequency=freq, limit=300)
            for s in series_list:
                if len(candidates) >= 30:
                    break
                cat = s.get("category", "").lower()
                if cat not in track_c_cats and cat != "":
                    continue

                markets = self.get_markets_for_series(s["series_ticker"], limit=10)
                for m in markets:
                    if len(candidates) >= 30:
                        break

                    # Client-side close_time filter
                    res_time = m.get("expected_resolution_time")
                    if res_time:
                        try:
                            res_dt = datetime.fromisoformat(res_time)
                            if res_dt < min_dt or res_dt > max_dt:
                                continue
                        except (ValueError, TypeError):
                            pass

                    if m["price_source"] == "unknown":
                        continue
                    if _is_blocked(m["market_title"]):
                        continue
                    candidates.append(m)

        # Sort by resolution proximity
        candidates.sort(key=lambda m: m.get("expected_resolution_time") or "9999")
        return candidates

    # ------------------------------------------------------------------
    # Track B — Retrospective candidates
    # ------------------------------------------------------------------

    def get_retrospective_candidates(self,
                                     lookback_days: int = 180) -> list[dict]:
        """
        Return resolved/settled Kalshi markets for Track B retro calibration.

        Filters for narrative-friendly content. Uses settled-status events
        then fetches their markets.
        """
        candidates = []
        # Fetch settled events + open events (settled events may be rare)
        for status in ("settled", "open"):
            events = self.list_events(status=status, limit=50)
            for event in events:
                if len(candidates) >= 50:
                    break
                event_ticker = event.get("event_ticker", "")
                if not event_ticker:
                    continue

                markets = self.get_markets_for_event(event_ticker, limit=5)
                for m in markets:
                    if m.get("status") == "settled":
                        if _is_blocked(m["market_title"]):
                            continue
                        if m["price_source"] == "unknown":
                            continue
                        candidates.append(m)
            if len(candidates) >= 50:
                break

        # Sort into tiers
        tier1 = []  # strong narrative, good category
        tier2 = []  # weak narrative or borderline category
        tier3 = []  # usable for pipeline testing only

        for m in candidates:
            is_narr = _is_narrative(m["market_title"],
                                    m.get("raw_market_data", {}).get("subtitle", ""))
            good_cat = m["category"] not in ("unknown",)

            if is_narr and good_cat:
                tier1.append(m)
            elif is_narr or good_cat:
                tier2.append(m)
            else:
                tier3.append(m)

        # Return tier1 first, then tier2, up to 50
        return (tier1 + tier2 + tier3)[:50]

    # ------------------------------------------------------------------
    # Market history (price time series)
    # ------------------------------------------------------------------

    def get_market_history(self, ticker: str,
                           start_ts: int = None,
                           end_ts: int = None) -> list[dict]:
        """
        Return historical prices for a Kalshi market if available.

        Kalshi provides candlestick-style history via the /markets/{ticker}/history
        endpoint. Returns list of {timestamp, price} dicts.
        """
        params = {}
        if start_ts is not None:
            params["start_ts"] = str(start_ts)
        if end_ts is not None:
            params["end_ts"] = str(end_ts)

        resp = _api(f"/markets/{ticker}/history", params if params else None)
        if "error" in resp:
            print(f"Kalshi history error for {ticker}: {resp['error']}")
            return []

        # Kalshi returns history with candlestick fields
        history = resp.get("history", resp.get("candlesticks", []))
        if not history:
            return []

        points = []
        for h in history:
            try:
                ts = h.get("ts", h.get("timestamp"))
                if ts is None:
                    continue
                close = h.get("close", h.get("last_price"))
                open_p = h.get("open")
                if close is None and open_p is not None:
                    close = open_p
                if close is None:
                    continue
                price = float(close)
                # Convert cents to dollars if needed
                if price > 1.0:
                    price = price / 100.0

                dt = _parse_kalshi_time(ts)
                points.append({
                    "timestamp": dt.isoformat() if dt else None,
                    "timestamp_ms": ts,
                    "price": round(price, 4),
                })
            except (ValueError, TypeError, KeyError):
                continue

        return sorted(points, key=lambda p: p.get("timestamp_ms", 0))

    # ------------------------------------------------------------------
    # Resolution status
    # ------------------------------------------------------------------

    def get_resolution_status(self, ticker: str) -> dict:
        """
        Return market status and outcome if resolved.

        Returns:
          {"resolved": True/False, "actual_outcome": True/False/None,
           "resolution_time": "...", "resolution_source": "kalshi",
           "resolution_notes": "..."}
        """
        market = self.get_market_by_id(ticker)
        if not market:
            return {"resolved": False, "actual_outcome": None, "resolution_source": "kalshi_v2", "resolution_notes": "Market not found"}

        status = market.get("status", "unknown")
        raw = market.get("raw_market_data", {})

        # Check if settled
        if status in ("settled", "closed"):
            result = raw.get("result", "")
            actual_outcome = None
            if result and result.lower() in ("yes", "true"):
                actual_outcome = True
            elif result and result.lower() in ("no", "false"):
                actual_outcome = False

            return {
                "resolved": actual_outcome is not None,
                "actual_outcome": actual_outcome,
                "resolution_time": (market.get("expected_resolution_time")
                                    or datetime.now(timezone.utc).isoformat()),
                "resolution_source": "kalshi_v2",
                "resolution_notes": f"Kalshi status={status}, result={result}",
            }

        # If open/active, check if past close_time
        close_time = market.get("expected_resolution_time")
        if close_time:
            try:
                close_dt = datetime.fromisoformat(close_time)
                if close_dt < datetime.now(timezone.utc):
                    return {
                        "resolved": False,
                        "actual_outcome": None,
                        "resolution_time": close_time,
                        "resolution_source": "kalshi_v2",
                        "resolution_notes": "Past close_time but market still shows as open",
                    }
            except (ValueError, TypeError):
                pass

        return {
            "resolved": False,
            "actual_outcome": None,
            "resolution_source": "kalshi_v2",
            "resolution_notes": "Market still active/open",
        }

    # ------------------------------------------------------------------
    # Bulk utility: get event detail
    # ------------------------------------------------------------------

    def get_event_by_ticker(self, event_ticker: str) -> Optional[dict]:
        """Fetch Kalshi event-level detail (contains resolution info)."""
        resp = _api(f"/events/{event_ticker}")
        if "error" in resp:
            return None
        return resp.get("event", resp)


# --- Module-level convenience ---

_DEFAULT_SCANNER = None


def _scanner() -> KalshiScanner:
    global _DEFAULT_SCANNER
    if _DEFAULT_SCANNER is None:
        _DEFAULT_SCANNER = KalshiScanner()
    return _DEFAULT_SCANNER


def scan_kalshi_markets(status: str = "open", limit: int = 100) -> list[dict]:
    """Quick module-level access."""
    return _scanner().list_markets(status=status, limit=limit)


# --- Smoke test ---

if __name__ == "__main__":
    import sys

    s = KalshiScanner()

    print("=" * 60)
    print("Kalshi Scanner Smoke Test")
    print("=" * 60)

    # Test 1: List events (narrative discovery via events endpoint)
    print("\n[1/5] Listing events (narrative discovery, limit=50)...")
    events = s.list_events(status="open", limit=50)
    print(f"  Got {len(events)} events")
    for e in events[:5]:
        print(f"  [{e['category']}] {e['title'][:70]} | narrative={e['is_narrative']}")
    if events:
        print("  ✅ list_events OK")
    else:
        print("  ❌ No events")

    # Test 2: Get markets for first event with data
    print("\n[2/5] Get markets for events...")
    found_market = None
    if events:
        for e in events:
            markets = s.get_markets_for_event(e["event_ticker"])
            if markets:
                m = markets[0]
                print(f"  Event: [{e['category']}] {e['title'][:60]}")
                print(f"  Market: {m['market_title'][:60]}")
                print(f"  price_yes={m['price_yes']}, vol=${m['volume_usd']:.0f}, source={m['price_source']}")
                found_market = m
                break
    if found_market:
        print("  ✅ get_markets_for_event OK")
    else:
        print("  ⚠️  No markets with data found")

    # Test 3: Price normalization (always passes — logic test)
    print("\n[3/5] Price normalization...")
    norm = s.normalize_price({"yes_bid_dollars": 0.42, "yes_ask_dollars": 0.44})
    print(f"  dollars midpoint: {norm[0]} (expected ~0.43) price_source={norm[2]}")
    norm2 = s.normalize_price({"yes_bid_dollars": 0.08, "yes_ask_dollars": 0.10})
    print(f"  low-prob midpoint: {norm2[0]} (expected ~0.09) price_source={norm2[2]}")
    norm3 = s.normalize_price({"last_price_dollars": 0.37})
    print(f"  last_price only: {norm3[0]} (expected ~0.37) price_source={norm3[2]}")
    norm4 = s.normalize_price({})
    print(f"  empty data: price_source={norm4[2]} (expected 'unknown')")

    # Test 4: Short-deadline discovery
    print("\n[4/5] Short-deadline candidates (1-6 days)...")
    short = s.get_short_deadline_candidates(days_min=1, days_max=6)
    print(f"  Got {len(short)} candidates")
    for m in short[:3]:
        print(f"  {m['external_market_id'][:30]}: resolves {m.get('expected_resolution_time')} | {m['market_title'][:50]}")
    if short:
        print("  ✅ short-deadline filter OK")
    else:
        print("  ⚠️  No short-deadline candidates — narrow 1-6d window on narrative events")

    # Test 5: Resolution status
    print("\n[5/5] Resolution status...")
    if found_market:
        ticker = found_market["external_market_id"]
        res = s.get_resolution_status(ticker)
        print(f"  {ticker}: resolved={res['resolved']}, outcome={res.get('actual_outcome')}")
        print(f"  source={res['resolution_source']}")
    else:
        print("  ⚠️  Skipped — no market available")

    print("\n" + "=" * 60)
    print("Kalshi Scanner smoke test complete")
    print("=" * 60)
