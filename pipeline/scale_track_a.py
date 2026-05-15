#!/usr/bin/env python3
"""Track A — Run 3 live narrative events with track metadata."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prophet.pipeline.market_scanner import scan_markets
from prophet.pipeline.run_calibration import run_one_event
from prophet.pipeline.logger import create_event, create_market_snapshot, create_seed, create_simulation_run
from prophet.pipeline.probability_parser import parse_forecast, PARSER_VERSION
from prophet.pipeline.seed_builder import build_seed_from_search
from prophet.pipeline.mirofish_runner import run_simulation
from datetime import datetime, timezone

candidates = scan_markets(limit=10)
print(f"Scanner: {len(candidates)} candidates")

# Filter to Track A candidates
track_a = [c for c in candidates if c['category'] in ('ai_narrative', 'crypto_regulatory', 'company_product', 'crypto_protocol')]
if not track_a:
    print("No Track A candidates from scanner")
    sys.exit(1)

# Pick up to 3 new events
events_to_run = track_a[:3] if len(track_a) >= 3 else track_a

for i, event in enumerate(events_to_run):
    selection_reason = f"Track A — live narrative event #{i+1}. Category: {event['category']}. Scanner-discovered from Polymarket."
    
    print(f"\n{'='*60}")
    print(f"Track A Event {i+1}/{len(events_to_run)}: [{event['category']}] {event['market_title'][:80]}")
    print(f"Price={event['price_yes']}, Vol=${event['volume_usd']:,.0f}, Track=live_narrative")
    print(f"{'='*60}")
    
    # Run with track metadata
    market_id = event['external_market_id']
    snapshot_time = datetime.now(timezone.utc)
    
    # Event
    eid = create_event(
        polymarket_event_id=f"track-a-{i+1}-{market_id[:20]}",
        market_title=event['market_title'],
        category=event['category'],
        resolution_criteria=event.get('resolution_criteria', ''),
        event_track='live_narrative',
        hypothesis_validity='true',
        selection_reason=selection_reason,
        manual_selection=False,
    )
    if not eid:
        print(f"  ❌ create_event failed")
        continue
    print(f"  [1/6] Event: {eid}")
    
    # Snapshot
    sid = create_market_snapshot(eid, event['price_yes'], volume_usd=event['volume_usd'])
    print(f"  [2/6] Snapshot: {sid}")
    
    # Seed
    seed = build_seed_from_search(
        event['market_title'], event.get('resolution_criteria', ''),
        event['price_yes'], volume_usd=event['volume_usd']
    )
    seed_id = create_seed(eid, seed['seed_doc_text'], seed['source_urls'],
                          seed_builder_version=seed['seed_builder_version'],
                          seed_quality=seed['seed_quality'])
    print(f"  [3/6] Seed: {seed_id} | quality={seed['seed_quality']}, sources={seed['source_count']}")
    
    # MiroFish
    req = f"Simulate how stakeholders discuss: {event['market_title']}. Model narrative dynamics."
    print(f"  [4/6] MiroFish: launching (3 rounds, ~5 min)...")
    sim = run_simulation(seed['seed_doc_text'], req, f"Prophet Track A: {event['market_title'][:50]}", max_rounds=3)
    
    if sim['status'] != 'completed':
        print(f"  ❌ Simulation failed: {sim.get('error')}")
        continue
    
    print(f"  [5/6] Report: {len(sim['raw_report_markdown'])} chars")
    
    # Parse
    parsed = parse_forecast(sim['raw_report_markdown'], event['market_title'],
                           event.get('resolution_criteria', ''), event['price_yes'])
    
    # Write
    run_id = create_simulation_run(
        event_id=eid, seed_id=seed_id, market_snapshot_id=sid,
        mirofish_project_id=sim.get('project_id',''), mirofish_simulation_id=sim.get('simulation_id',''),
        mirofish_report_id=sim.get('report_id',''), raw_report=sim['raw_report_markdown'],
        structured_forecast=parsed,
        forecast_probability_yes=parsed.get('forecast_probability_yes'),
        forecast_confidence=parsed.get('forecast_confidence'),
        forecast_direction=parsed.get('forecast_direction'),
        parse_success=parsed['parse_success'],
        report_parser_version=PARSER_VERSION,
        agent_count=sim['agent_count'], round_count=sim['round_count'],
        simulation_duration_sec=sim['duration_sec'], api_cost_estimate=2.50,
    )
    
    print(f"  [6/6] DB: {run_id} | parse={parsed['parse_success']} forecast={parsed.get('forecast_probability_yes')}")
    print(f"  ✅ COMPLETE")

print(f"\n{'='*60}")
print(f"Track A scaling complete")
