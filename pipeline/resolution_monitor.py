"""
resolution_monitor.py — Daily job to check unresolved Prophet events.

Supports both Polymarket and Kalshi platforms. Dispatches to correct
resolution checker based on event.platform field.

When an event resolves:
  - Writes resolution row to prophet.resolutions
  - Triggers forecast_comparison for all simulation_runs tied to the event

Designed to run as a daily cron job. Reads from Postgres.

Usage:
  python resolution_monitor.py           # Check all unresolved events
  python resolution_monitor.py --dry-run # Show what would be checked

Author: ClawBot + Akshar
Date: May 12, 2026
Version: v0.2 — Multi-platform support (Kalshi + Polymarket)
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from prophet.pipeline.logger import create_resolution, get_unresolved_events, _psql
from prophet.pipeline.forecast_comparison import compute_calibration_for_event
from prophet.pipeline.kalshi_scanner import KalshiScanner


POLYMARKET_GAMMA = os.environ.get("POLYMARKET_GAMMA_URL", "https://gamma-api.polymarket.com")


def check_polymarket_resolution(polymarket_event_id: str) -> Optional[Dict]:
    """Check Polymarket Gamma API for event resolution."""
    url = f"{POLYMARKET_GAMMA}/events/{polymarket_event_id}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

    event = data if isinstance(data, dict) else {}
    resolved = event.get("resolved", False)
    if not resolved:
        return None

    markets = event.get("markets", [])
    if not markets:
        return None

    m = markets[0]
    outcomes = m.get("outcomes", [])
    for outcome in outcomes:
        if outcome.get("isResolved") or m.get("resolved"):
            outcome_val = outcome.get("outcome", outcome.get("label", ""))
            actual_outcome = outcome_val.upper() == "YES"
            return {
                "resolved": True,
                "actual_outcome": actual_outcome,
                "resolution_source": "polymarket_gamma",
                "resolution_time": datetime.now(timezone.utc),
            }

    return None


def check_kalshi_resolution(ticker: str) -> Optional[Dict]:
    """Check Kalshi API for market resolution status."""
    scanner = KalshiScanner()
    return scanner.get_resolution_status(ticker)


def check_resolution(platform: str, external_id: str) -> Optional[Dict]:
    """
    Platform-aware resolution check dispatcher.

    Returns None if unresolved, or resolution dict with:
      resolved, actual_outcome, resolution_source, resolution_time
    """
    if platform == "polymarket":
        return check_polymarket_resolution(external_id)
    elif platform == "kalshi":
        return check_kalshi_resolution(external_id)
    else:
        raise ValueError(f"Unsupported platform: {platform}")


def scan_and_resolve(dry_run: bool = False) -> List[Dict]:
    """
    Check all unresolved Prophet events using platform-aware dispatch.
    Resolve any that have finished and trigger calibration.
    """
    unresolved_ids = get_unresolved_events()
    if not unresolved_ids:
        print("No unresolved events found.")
        return []

    results = []
    for event_id in unresolved_ids:
        # Get external ID and platform from events table
        row = _psql(f"""
            SELECT polymarket_event_id, COALESCE(platform, 'polymarket') as platform
            FROM prophet.events WHERE id = '{event_id}';
        """)
        if not row:
            continue

        parts = row.strip().split("|")
        external_id = parts[0].strip() if len(parts) > 0 else None
        platform = parts[1].strip() if len(parts) > 1 else "polymarket"

        if not external_id:
            continue

        print(f"Checking: {event_id} (platform={platform}, external_id={external_id[:40]}...)")

        try:
            status = check_resolution(platform, external_id)
        except ValueError as e:
            print(f"  ❌ {e}")
            continue

        if status and status.get("resolved"):
            outcome_str = 'YES' if status.get('actual_outcome') else 'NO'
            print(f"  ✅ RESOLVED: outcome={outcome_str} (source={status.get('resolution_source')})")

            if not dry_run:
                # Write resolution
                res_id = create_resolution(
                    event_id=event_id,
                    actual_outcome=status["actual_outcome"],
                    resolution_source=status.get("resolution_source", platform),
                    resolution_time=status.get("resolution_time"),
                    resolution_notes=status.get("resolution_notes", ""),
                )
                print(f"  Resolution saved: {res_id}")

                # Trigger calibration
                cal_results = compute_calibration_for_event(event_id)
                print(f"  Calibration: {len(cal_results)} simulation(s) scored")

            results.append({
                "event_id": event_id,
                "outcome": status["actual_outcome"],
                "platform": platform,
                "status": "resolved",
            })
        else:
            print(f"  Still pending")

    return results


def main():
    parser = argparse.ArgumentParser(description="Prophet Resolution Monitor")
    parser.add_argument("--dry-run", action="store_true", help="Check without writing")
    args = parser.parse_args()

    results = scan_and_resolve(dry_run=args.dry_run)

    print(f"\n{'=' * 50}")
    print(f"Total checked: {len(get_unresolved_events())}")
    print(f"Newly resolved: {len(results)}")
    for r in results:
        print(f"  {r['event_id'][:20]}... → {'YES' if r['outcome'] else 'NO'}")


if __name__ == "__main__":
    main()
