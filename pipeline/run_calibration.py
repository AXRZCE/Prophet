#!/usr/bin/env python3
"""
run_calibration.py — Prophet Phase 1 main orchestrator.

Runs the full calibration pipeline: select event → snapshot → seed →
MiroFish simulation → parse probability → write to Postgres.

Usage:
  python run_calibration.py --event-id <polymarket_id>
  python run_calibration.py --limit 3
  python run_calibration.py --dry-run
  python run_calibration.py --event-id <id> --max-rounds 3 --twitter-only

Environment:
  PROPHET_DB_PASSWORD  Postgres password for clawbot user
  MIROFISH_URL         MiroFish base URL (default: http://localhost:5001)

Author: ClawBot + Akshar
Date: May 12, 2026
Version: v0.1
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone

from prophet.pipeline.logger import (
    create_event,
    create_market_snapshot,
    create_seed,
    create_simulation_run,
    log_failed_run,
    get_parser_success_rate,
)
from prophet.pipeline.market_scanner import scan_markets, get_market_by_id
from prophet.pipeline.seed_builder import build_seed_from_search
from prophet.pipeline.mirofish_runner import run_simulation
from prophet.pipeline.probability_parser import parse_forecast, PARSER_VERSION


def run_one_event(event: dict, max_rounds: int = 5, dry_run: bool = False) -> dict:
    """
    Run the complete calibration pipeline for one event.

    Returns a dict with results including simulation_run_id or error.
    """
    market_title = event["market_title"]
    market_id = event["external_market_id"]
    category = event["category"]
    price_yes = event["price_yes"]
    price_no = event["price_no"]
    volume = event["volume_usd"]
    liquidity = event["liquidity_usd"]
    resolution_criteria = event.get("resolution_criteria", "")

    result = {
        "event_id": None,
        "simulation_run_id": None,
        "market_title": market_title,
        "category": category,
        "price_yes": price_yes,
        "forecast_yes": None,
        "parse_success": False,
        "status": "failed",
        "error": None,
    }

    try:
        # --- Step 1: Store event in Postgres ---
        print(f"[1/6] Event: \"{market_title[:80]}\"")
        if dry_run:
            print("  [DRY RUN] Would create event row")
            return {**result, "status": "dry_run"}

        snapshot_time = datetime.now(timezone.utc)

        event_id = create_event(
            polymarket_event_id=market_id,
            market_title=market_title,
            category=category,
            resolution_criteria=resolution_criteria,
            market_url=event.get("market_url", ""),
        )
        result["event_id"] = event_id

        # --- Step 2: Capture market snapshot ---
        print(f"[2/6] Market snapshot: price_yes={price_yes}, volume=${volume:,.0f}")
        snap_id = create_market_snapshot(
            event_id=event_id,
            price_yes=price_yes,
            price_no=price_no,
            volume_usd=volume,
            liquidity_usd=liquidity,
            snapshot_at=snapshot_time,
        )

        # --- Step 3: Build seed document ---
        print(f"[3/6] Seed: searching SearXNG for context...")
        seed = build_seed_from_search(
            market_question=market_title,
            resolution_criteria=resolution_criteria,
            price_yes=price_yes,
            price_no=price_no,
            volume_usd=volume,
            liquidity_usd=liquidity,
        )
        seed_id = create_seed(
            event_id=event_id,
            seed_doc_text=seed["seed_doc_text"],
            source_urls=seed["source_urls"],
            seed_builder_version=seed["seed_builder_version"],
            seed_quality=seed["seed_quality"],
            manual_edits=seed["manual_edits"],
        )
        print(f"  Seed quality: {seed['seed_quality']}, sources: {seed['source_count']}, hash: {seed['seed_doc_hash']}")

        # --- Step 4: Run MiroFish simulation ---
        requirement = f"Simulate how different stakeholders discuss and form opinions about: {market_title}. Model the narrative dynamics between supporters and skeptics."
        print(f"[4/6] Simulation: launching MiroFish ({max_rounds} rounds, ETA ~10 min)...")
        sim_result = run_simulation(
            seed_doc=seed["seed_doc_text"],
            simulation_requirement=requirement,
            project_name=f"Prophet: {market_title[:50]}",
            max_rounds=max_rounds,
        )

        if sim_result["status"] != "completed":
            result["error"] = f"Simulation failed: {sim_result.get('error')}"
            log_failed_run(event_id, result["error"], sim_result)
            print(f"  ❌ Simulation failed: {sim_result.get('error')}")
            return result

        raw_report = sim_result["raw_report_markdown"]
        print(f"  Report received: {len(raw_report)} chars, report_id={sim_result['report_id']}")

        # --- Step 5: Parse probability ---
        print(f"[5/6] Parser: extracting forecast...")
        parsed = parse_forecast(
            raw_report=raw_report,
            market_question=market_title,
            resolution_criteria=resolution_criteria,
            market_price_at_sim=price_yes,
        )

        parse_ok = parsed["parse_success"]
        forecast = parsed.get("forecast_probability_yes")
        confidence = parsed.get("forecast_confidence")
        direction = parsed.get("forecast_direction")
        result["forecast_yes"] = forecast
        result["parse_success"] = parse_ok

        if parse_ok:
            print(f"  ✅ PARSED: forecast={forecast:.4f}, confidence={confidence:.2f}, direction={direction}")
        else:
            print(f"  ⚠️ AMBIGUOUS: {parsed.get('error', 'no clear forecast')}")

        # --- Step 6: Write simulation run to Postgres ---
        print(f"[6/6] DB write: saving simulation run...")
        sim_id = create_simulation_run(
            event_id=event_id,
            seed_id=seed_id,
            market_snapshot_id=snap_id,
            mirofish_project_id=sim_result["project_id"],
            mirofish_simulation_id=sim_result["simulation_id"],
            mirofish_report_id=sim_result["report_id"],
            raw_report=raw_report,
            structured_forecast=parsed,
            forecast_probability_yes=forecast,
            forecast_confidence=confidence,
            forecast_direction=direction,
            probability_source=parsed.get("probability_source", "llm_extractor"),
            parse_success=parse_ok,
            parse_error=parsed.get("error", ""),
            market_price_used_as_forecast=parsed.get("market_price_used_as_forecast", False),
            report_parser_version=PARSER_VERSION,
            prompt_template_version=seed["seed_builder_version"],
            agent_persona_version="pectra-v1",
            model_name_agents="deepseek-chat",
            model_name_report="deepseek-chat",
            agent_count=sim_result["agent_count"],
            round_count=sim_result["round_count"],
            simulation_duration_sec=sim_result["duration_sec"],
            api_cost_estimate=2.50,
        )

        result["simulation_run_id"] = sim_id
        result["status"] = "completed"

        print(f"  ✅ Simulation run saved: {sim_id}")
        print()

    except Exception as e:
        result["error"] = str(e)
        if result["event_id"]:
            log_failed_run(result["event_id"], str(e), result)
        print(f"  ❌ Error: {e}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Prophet Phase 1 — Calibration Pipeline")
    parser.add_argument("--event-id", help="Polymarket event ID to process")
    parser.add_argument("--limit", type=int, default=1, help="Max number of events to scan and process")
    parser.add_argument("--max-rounds", type=int, default=5, help="MiroFish simulation rounds")
    parser.add_argument("--twitter-only", action="store_true", help="Twitter simulation only (faster)")
    parser.add_argument("--dry-run", action="store_true", help="Validate without running simulations")
    parser.add_argument("--stats", action="store_true", help="Show parser success rate and exit")
    args = parser.parse_args()

    # Stats mode
    if args.stats:
        rate = get_parser_success_rate()
        print(json.dumps(rate, indent=2))
        sys.exit(0)

    # Select events
    events = []
    if args.event_id:
        print(f"Fetching event: {args.event_id}")
        event = get_market_by_id(args.event_id)
        if event:
            events = [event]
        else:
            print(f"Event not found: {args.event_id}")
            sys.exit(1)
    else:
        print(f"Scanning Polymarket for up to {args.limit} candidates...")
        events = scan_markets(limit=args.limit * 3)
        if not events:
            print("No candidate events found. Try:")
            print("  - Check Polymarket API availability")
            print("  - Use --event-id to process a known event")
            sys.exit(1)
        events = events[:args.limit]

    print(f"Processing {len(events)} event(s)\n{'=' * 60}")

    results = []
    for i, event in enumerate(events):
        print(f"--- Event {i+1}/{len(events)} ---")
        result = run_one_event(event, max_rounds=args.max_rounds, dry_run=args.dry_run)
        results.append(result)

    # Summary
    print("=" * 60)
    completed = [r for r in results if r["status"] == "completed"]
    failed = [r for r in results if r["status"] == "failed"]
    parsed = [r for r in completed if r["parse_success"]]

    print(f"Completed: {len(completed)}/{len(results)}")
    print(f"Parsed successfully: {len(parsed)}/{len(completed or [1])}")
    print(f"Failed: {len(failed)}")

    for r in completed:
        icon = "✅" if r["parse_success"] else "⚠️"
        print(f"  {icon} {r['market_title'][:70]}... — forecast={r['forecast_yes']}")

    parser_rate = get_parser_success_rate()
    print(f"\nCumulative parser rate: {parser_rate['success_rate_pct']}%")


if __name__ == "__main__":
    main()
