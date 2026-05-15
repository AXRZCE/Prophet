#!/usr/bin/env python3
"""
recover_from_disk.py — Recover simulation artifacts from disk after MiroFish crashes.

Scans prophet/reports/phase1/ for .md and .json files, checks if a corresponding
simulation_run exists in the DB, and backfills if missing.

Usage:
  PYTHONPATH=/home/akshar/clawbot-v2 python3 -m prophet.pipeline.recover_from_disk
  PYTHONPATH=/home/akshar/clawbot-v2 python3 -m prophet.pipeline.recover_from_disk --dry-run
"""

import json
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from prophet.pipeline.logger import (
    _psql, _psql_val, _escape_sql,
    create_simulation_run, save_sim_artifact,
)


REPORT_DIR = Path(__file__).resolve().parent.parent / "reports" / "phase1"


def find_artifacts():
    """Find all report/parsed/seed files on disk."""
    artifacts = {}
    for path in sorted(REPORT_DIR.glob("*")):
        if path.suffix not in (".md", ".json"):
            continue
        stem = path.stem  # e.g., "202f643e_report" → event_id = "202f643e"
        # Extract event ID (first UUID segment before underscore)
        parts = stem.split("_")
        if len(parts) >= 2:
            event_id = parts[0] if len(parts[0]) > 30 else stem.split("_")[0]
            if event_id not in artifacts:
                artifacts[event_id] = {}
            kind = "_".join(parts[1:]) if len(parts) > 1 else "artifact"
            artifacts[event_id][kind] = str(path)
    return artifacts


def artifact_in_db(event_id: str) -> bool:
    """Check if this event already has a completed simulation_run."""
    try:
        count = _psql(f"SELECT COUNT(*) FROM prophet.simulation_runs WHERE event_id = '{event_id}' AND run_status = 'completed';")
        return int(count.strip()) > 0 if count.strip() else False
    except Exception:
        return False


def recover_report(event_id: str, report_path: str, dry_run: bool = False):
    """Attempt to re-parse and backfill a report from disk."""
    report_text = Path(report_path).read_text()
    if not report_text.strip():
        return {"status": "skipped", "reason": "empty report"}

    print(f"  Report: {len(report_text)} chars from {report_path}")

    if dry_run:
        return {"status": "dry_run", "would_recover": True}

    # Try to parse the forecast from the report
    try:
        from prophet.pipeline.probability_parser import parse_forecast, PARSER_VERSION

        # Get event info
        event_info = _psql(f"SELECT market_title FROM prophet.events WHERE id = '{event_id}';")
        title = event_info.split("|")[0].strip() if event_info and "|" in event_info else "Unknown"

        parsed = parse_forecast(
            raw_report=report_text,
            market_question=title,
            resolution_criteria="",
            market_price_at_sim=0.5,
        )

        if not parsed.get("parse_success"):
            return {"status": "failed", "reason": f"parse failed: {parsed.get('error')}"}

        # Get or create snapshot/seed placeholders
        snap_id = _psql(f"SELECT id FROM prophet.market_snapshots WHERE event_id = '{event_id}' ORDER BY snapshot_at DESC LIMIT 1;")
        if not snap_id:
            snap_id = event_id  # placeholder

        seed_id = _psql(f"SELECT id FROM prophet.seeds WHERE event_id = '{event_id}' ORDER BY created_at DESC LIMIT 1;")
        if not seed_id:
            seed_id = event_id  # placeholder

        sim_id = create_simulation_run(
            event_id=event_id,
            seed_id=seed_id.strip() if seed_id else event_id,
            market_snapshot_id=snap_id.strip() if snap_id else event_id,
            raw_report=report_text,
            structured_forecast=parsed,
            forecast_probability_yes=parsed.get("forecast_probability_yes"),
            forecast_confidence=parsed.get("forecast_confidence"),
            forecast_direction=parsed.get("forecast_direction"),
            probability_source=parsed.get("probability_source", "recovery"),
            parse_success=True,
            parse_error=parsed.get("error", ""),
            report_parser_version=PARSER_VERSION,
            prompt_template_version="recovery",
        )

        return {"status": "recovered", "sim_id": sim_id}

    except Exception as e:
        return {"status": "failed", "reason": str(e)[:200]}


def main():
    dry_run = "--dry-run" in sys.argv

    print("=" * 60)
    print("Prophet Recovery — Disk → DB Backfill")
    print("=" * 60)
    print(f"Scanning: {REPORT_DIR}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()

    artifacts = find_artifacts()
    print(f"Found {len(artifacts)} event(s) with disk artifacts\n")

    recovered = 0
    skipped = 0
    failed = 0

    for event_id, kinds in sorted(artifacts.items()):
        if artifact_in_db(event_id):
            print(f"[SKIP] {event_id[:16]}... — already in DB")
            skipped += 1
            continue

        report_path = kinds.get("report") or kinds.get("artifact")
        if not report_path:
            print(f"[SKIP] {event_id[:16]}... — no report file found")
            skipped += 1
            continue

        print(f"[RECOVER] {event_id[:16]}...")
        result = recover_report(event_id, report_path, dry_run)

        if result["status"] == "recovered":
            print(f"  ✅ Recovered: {result.get('sim_id')}")
            recovered += 1
        elif result["status"] == "dry_run":
            print(f"  📋 Would recover (dry run)")
        else:
            print(f"  ❌ Failed: {result.get('reason')}")
            failed += 1

    print()
    print(f"Results: {recovered} recovered, {skipped} skipped, {failed} failed")
    print("=" * 60)


if __name__ == "__main__":
    main()
