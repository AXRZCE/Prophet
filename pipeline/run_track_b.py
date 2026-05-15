#!/usr/bin/env python3
"""
run_track_b.py — Prophet Track B retrospective event setup.

Creates retro events from settled Kalshi weekly markets with known outcomes.
Writes events + resolutions to Postgres. Seeds/sims are run separately
with anti-leakage time-filtered SearXNG queries.

Author: ClawBot + Akshar
Date: May 13, 2026
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime, timezone
from prophet.pipeline.kalshi_scanner import KalshiScanner
from prophet.pipeline.logger import create_event, create_market_snapshot, create_resolution, _psql_exec, _psql_val


def main():
    scanner = KalshiScanner()
    print("=" * 60)
    print("Prophet Track B — Retrospective Event Setup")
    print("=" * 60)

    # Settled weekly series with known outcomes
    targets = [
        ("KXAPRPOTUS-26MAY08-41.6", "Will the President's approval rating be above 41.6?", 
         "politics", 0.005, 6408, False, "2026-05-08T15:00:00+00:00", "partial",
         "Retrospective Kalshi weekly politics market. Resolved May 8."),
        ("KXAPRPOTUS-26MAY08-41.5", "Will the President's approval rating be between 41.4 and 41.6?",
         "politics", 0.005, 6673, False, "2026-05-08T15:00:00+00:00", "partial",
         "Retrospective Kalshi weekly politics market. Resolved May 8."),
        ("KXSURVIVORELIMINATION-26MAY07-TIF", "Will Tiffany Nicole Ervin be eliminated from Survivor S50 E11?",
         "entertainment", 0.06, 31958, False, "2026-05-07T02:55:03+00:00", "partial",
         "Retrospective Kalshi weekly entertainment market. Resolved May 7."),
        ("KXSURVIVORELIMINATION-26MAY07-RIZ", "Will Rizo Velovic be eliminated from Survivor S50 E11?",
         "entertainment", 0.01, 21898, False, "2026-05-07T02:54:51+00:00", "partial",
         "Retrospective Kalshi weekly entertainment market. Resolved May 7."),
        ("KXETH-26MAY13-8PM-T1540", "Ethereum price at May 13, 2026 at 8pm EDT above $1540?",
         "crypto", 0.01, 50, False, "2026-05-14T00:00:00+00:00", "false",
         "Retrospective crypto price market. Pipeline validation only. Resolved May 13."),
    ]

    created = 0
    for ticker, title, cat, price, vol, outcome, res_time_str, validity, reason in targets:
        # Check if already exists
        existing = _psql_val(f"SELECT id FROM prophet.events WHERE polymarket_event_id = '{ticker}';")
        if existing:
            print(f"  SKIP: {title[:60]} (already exists: {existing[:20]}...)")
            continue

        res_dt = datetime.fromisoformat(res_time_str)
        source_cutoff = res_dt  # Anti-leakage: sources must be from before resolution
        
        event_id = create_event(
            polymarket_event_id=ticker,
            market_title=title,
            category=cat,
            resolution_criteria=f"Kalshi settled: {title}",
            market_url=f"https://kalshi.com/markets/{ticker}",
            platform="kalshi",
            event_track="retrospective",
            hypothesis_validity=validity,
            selection_reason=reason,
            manual_selection=True,
            source_cutoff_time=source_cutoff,
            historical_snapshot_time=res_dt,
        )
        
        if not event_id:
            print(f"  FAIL: {title[:60]}")
            continue

        # Write resolution
        res_id = create_resolution(
            event_id=event_id,
            actual_outcome=outcome,
            resolution_time=res_dt,
            resolution_source="kalshi_v2_settled",
            resolution_notes=f"Retrospective: market settled with result={'YES' if outcome else 'NO'}",
        )
        
        print(f"  ✅ [{validity}] {title[:60]}")
        print(f"     event={event_id[:20]}... resolution={res_id[:20]}... outcome={'YES' if outcome else 'NO'}")
        created += 1

    print(f"\nTrack B events created: {created}")
    if created >= 5:
        print("✅ Track B has 5+ retrospective events")
    else:
        print(f"⚠️  Only {created}/5 — need more settled markets")


if __name__ == "__main__":
    main()
