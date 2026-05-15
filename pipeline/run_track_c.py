#!/usr/bin/env python3
"""
run_track_c.py — Prophet Track C runner using Kalshi weekly markets.

Discovers short-deadline Kalshi candidates, labels them as Track C
stress tests, and runs the full calibration pipeline.

Usage:
  python run_track_c.py --limit 5
  python run_track_c.py --limit 5 --max-rounds 3  # faster

Author: ClawBot + Akshar
Date: May 13, 2026
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import argparse
import json
from datetime import datetime, timezone

from prophet.pipeline.logger import (
    create_event,
    create_market_snapshot,
    create_seed,
    create_simulation_run,
    log_failed_run,
    get_parser_success_rate,
)
from prophet.pipeline.kalshi_scanner import KalshiScanner
from prophet.pipeline.seed_builder import build_seed_from_search
from prophet.pipeline.mirofish_runner import run_simulation
from prophet.pipeline.probability_parser import parse_forecast, PARSER_VERSION


def pick_track_c_candidates(limit: int = 5) -> list:
    """Select Track C candidates with category variety."""
    scanner = KalshiScanner()
    picks = []
    
    # Priority targets by category (verified weekly series tickers)
    target_series = {
        "politics": ["KXAPRPOTUS", "KXEOWEEK", "KXTRUMPFAV", "KXVOTEHUBTRUMPUPDOWN"],
        "entertainment": ["KXSURVIVORELIMINATION", "KXTOPMOVIENFLX", "KXTOPSHOWPAR", "KXTOPMOVIEDIS"],
        "crypto": ["KXBTC", "KXETH", "KXDOGEMAXW"],
        "commodity": ["OILW", "KXCOPPERW"],
        "financial": ["KXINXI", "KXGBPUSD"],
    }
    
    # Try to get 1 from each category, then fill from top volume
    for cat, tickers in target_series.items():
        if len(picks) >= limit:
            break
        for ticker in tickers:
            try:
                mkts = scanner.get_markets_for_series(ticker, status="open", limit=3)
                if mkts:
                    m = mkts[0]  # Take highest-volume market from this series
                    picks.append(m)
                    break
            except Exception:
                continue
    
    # If still need more, grab from all weekly candidates sorted by volume
    if len(picks) < limit:
        existing_tickers = {p["external_market_id"] for p in picks}
        all_c = scanner.get_track_c_candidates(days_min=1, days_max=14)
        all_c.sort(key=lambda c: c.get("volume_usd", 0), reverse=True)
        for c in all_c:
            if len(picks) >= limit:
                break
            if c["external_market_id"] not in existing_tickers:
                picks.append(c)
    
    # Assign hypothesis validity based on event_ticker prefix
    for p in picks:
        ticker = (p.get("external_market_id", "") or "").lower()
        event_ticker = (p.get("raw_market_data", {}).get("event_ticker", "") or "").lower()
        title_lower = p["market_title"].lower()
        
        # Check both the market ticker and event_ticker for category matching
        identifiers = ticker + " " + event_ticker
        
        # Politics/approval = partial
        if any(kw in identifiers for kw in ["approve", "trumpfav", "eoweek", "votehub", "approval"]):
            p["_hypothesis"] = "partial"
            p["_reason"] = "Short-deadline Kalshi weekly politics/polling market. Partially narrative."
        # Entertainment/culture = partial
        elif any(kw in identifiers for kw in ["survivor", "netflix", "topmovie", "topshow", "spotify"]):
            p["_hypothesis"] = "partial"
            p["_reason"] = "Short-deadline Kalshi weekly entertainment/culture market. Partially narrative."
        # Crypto/commodity price = false
        elif any(kw in identifiers for kw in ["btc", "eth", "doge", "oil", "copper", "gbp", "inxi"]):
            p["_hypothesis"] = "false"
            p["_reason"] = "Short-deadline price/commodity market. Used to validate resolution/scoring pipeline only. Not core narrative evidence."
        elif any(kw in title_lower for kw in ["trump", "approval", "executive order", "netflix"]):
            p["_hypothesis"] = "partial"
            p["_reason"] = "Short-deadline Kalshi weekly market. Partially narrative."
        else:
            p["_hypothesis"] = "false"
            p["_reason"] = "Short-deadline Kalshi weekly market. Used for pipeline scoring validation."
    
    return picks[:limit]


def run_one_track_c(market: dict, max_rounds: int = 3) -> dict:
    """Run full Prophet pipeline for one Track C Kalshi event."""
    market_title = market["market_title"]
    market_ticker = market["external_market_id"]
    category = market.get("category", "unknown")
    price_yes = market["price_yes"]
    price_no = market["price_no"]
    volume = market.get("volume_usd", 0)
    liquidity = market.get("liquidity_usd", 0)
    resolution_criteria = market.get("resolution_criteria", "")
    platform = "kalshi"
    event_track = "stress_test"
    hypothesis_validity = market.get("_hypothesis", "false")
    selection_reason = market.get("_reason", "Track C stress test")
    price_source = market.get("price_source", "midpoint")
    
    result = {
        "market_title": market_title,
        "ticker": market_ticker,
        "status": "failed",
        "error": None,
    }

    try:
        snapshot_time = datetime.now(timezone.utc)
        
        # Step 1: Event
        print(f"[1/6] Event: {market_title[:80]}")
        event_id = create_event(
            polymarket_event_id=market_ticker,
            market_title=market_title,
            category=category,
            resolution_criteria=resolution_criteria,
            market_url=market.get("market_url", ""),
            platform=platform,
            event_track=event_track,
            hypothesis_validity=hypothesis_validity,
            selection_reason=selection_reason,
            manual_selection=True,
        )
        result["event_id"] = event_id
        print(f"  ID={event_id} | track={event_track} | validity={hypothesis_validity}")
        
        # Step 2: Snapshot
        print(f"[2/6] Snapshot: price={price_yes}, vol=${volume:,.0f}")
        snap_id = create_market_snapshot(
            event_id=event_id,
            price_yes=price_yes,
            price_no=price_no,
            volume_usd=volume,
            liquidity_usd=liquidity,
            snapshot_at=snapshot_time,
            source="kalshi_v2",
            raw_yes_bid=market.get("raw_yes_bid"),
            raw_yes_ask=market.get("raw_yes_ask"),
            raw_last_price=market.get("raw_last_price"),
            normalized_price_yes=price_yes,
            price_source=price_source,
        )
        if not snap_id:
            result["error"] = "Market snapshot creation returned None (likely DB failure)"
            print(f"  ❌ {result['error']}")
            log_failed_run(event_id, result["error"], {})
            return result
        
        # Step 3: Seed
        print(f"[3/6] Seed: searching...")
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
        print(f"  quality={seed['seed_quality']}, sources={seed['source_count']}")
        
        # Step 4: MiroFish
        requirement = f"Simulate how stakeholders and analysts discuss: {market_title}. Model the narrative and information dynamics. IMPORTANT: All output must be in English."
        print(f"[4/6] Simulation ({max_rounds} rounds)...")
        sim_result = run_simulation(
            seed_doc=seed["seed_doc_text"],
            simulation_requirement=requirement,
            project_name=f"Prophet Track C: {market_title[:50]}",
            max_rounds=max_rounds,
        )
        
        if sim_result["status"] != "completed":
            result["error"] = f"Sim failed: {sim_result.get('error')}"
            log_failed_run(event_id, result["error"], sim_result)
            print(f"  ❌ {result['error']}")
            return result
        
        raw_report = sim_result["raw_report_markdown"]
        print(f"  Report: {len(raw_report)} chars")
        
        # Step 5: Parse
        print(f"[5/6] Parse...")
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
        
        if parse_ok:
            print(f"  ✅ forecast={forecast:.4f}, conf={confidence:.2f}, dir={direction}")
        else:
            print(f"  ⚠️  {parsed.get('error', 'no clear forecast')}")
        
        # Step 6: DB write
        print(f"[6/6] DB write...")
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
        result["forecast"] = forecast
        result["parse_success"] = parse_ok
        result["status"] = "completed"
        print(f"  ✅ {sim_id}")
        
    except Exception as e:
        result["error"] = str(e)
        print(f"  ❌ Error: {e}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Prophet Track C — Kalshi Stress Tests")
    parser.add_argument("--limit", type=int, default=5, help="Number of Track C events")
    parser.add_argument("--max-rounds", type=int, default=3, help="MiroFish simulation rounds")
    parser.add_argument("--dry-run", action="store_true", help="Show candidates without running")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Prophet Track C — Kalshi Weekly Stress Tests")
    print("=" * 60)
    
    # Pick candidates
    candidates = pick_track_c_candidates(limit=args.limit)
    print(f"\nSelected {len(candidates)} Track C candidates:\n")
    for i, c in enumerate(candidates):
        print(f"  [{i+1}] [{c.get('category','?')}] {c['market_title'][:70]}")
        print(f"      ticker={c['external_market_id'][:40]} price={c['price_yes']} vol=${c['volume_usd']:,.0f}")
        print(f"      validity={c['_hypothesis']} resolves={c.get('expected_resolution_time')}")
    
    if args.dry_run:
        print("\n[Dry run — no simulations executed]")
        return
    
    print(f"\n{'=' * 60}")
    print(f"Running {len(candidates)} Track C events\n")
    
    results = []
    for i, c in enumerate(candidates):
        print(f"--- Track C Event {i+1}/{len(candidates)} ---")
        result = run_one_track_c(c, max_rounds=args.max_rounds)
        results.append(result)
        print()
    
    # Summary
    print("=" * 60)
    completed = [r for r in results if r["status"] == "completed"]
    failed = [r for r in results if r["status"] == "failed"]
    parsed = [r for r in completed if r.get("parse_success")]
    
    print(f"Track C Complete: {len(completed)}/{len(results)}")
    print(f"Parsed successfully: {len(parsed)}/{len(completed or [1])}")
    print(f"Failed: {len(failed)}")
    
    for r in completed:
        icon = "✅" if r.get("parse_success") else "⚠️"
        print(f"  {icon} {r['market_title'][:70]}... — forecast={r.get('forecast')}")
    
    print(f"\nTrack C events now in prophet.events (event_track=stress_test)")


if __name__ == "__main__":
    main()
