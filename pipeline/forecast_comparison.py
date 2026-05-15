"""
forecast_comparison.py — Compute Brier scores and calibration metrics.

Compares simulation forecasts against actual outcomes. Generates
calibration_results rows in Postgres.

Formula:
  Brier score = (probability - outcome)^2
  where outcome = 1 for YES, 0 for NO

Hard rule: Only compute calibration for parse_success=true runs.
Failed parses are excluded from scoring but tracked separately.

Author: ClawBot + Akshar
Date: May 12, 2026
Version: v0.1
"""

import sys
import os
from typing import Dict, List, Optional

from prophet.pipeline.logger import create_calibration_result, _psql_val


def compute_brier(probability: float, actual_outcome: bool) -> float:
    """Brier score = (prob - outcome)^2 where outcome is 1.0 for YES, 0.0 for NO."""
    outcome = 1.0 if actual_outcome else 0.0
    return (probability - outcome) ** 2


def was_correct(probability: float, actual_outcome: bool, threshold: float = 0.5) -> bool:
    """Directional accuracy: did probability > 0.5 match the outcome?"""
    predicted_yes = probability > threshold
    return predicted_yes == actual_outcome


def compute_calibration_for_event(event_id: str) -> List[Dict]:
    """
    Compute calibration results for all completed simulation runs tied to an event.

    Fetches resolution from prophet.resolutions and computes Brier scores
    for every simulation_run where parse_success=true.

    Returns list of calibration_result dicts with IDs.
    """
    results = []

    # Get resolution
    from prophet.pipeline.logger import _psql
    resolution = _psql(f"""
        SELECT actual_outcome, EXTRACT(EPOCH FROM (resolution_time - (
            SELECT MIN(created_at) FROM prophet.simulation_runs WHERE event_id = '{event_id}'
        ))) / 86400 as days
        FROM prophet.resolutions WHERE event_id = '{event_id}' LIMIT 1;
    """)

    if not resolution:
        return results

    # Parse resolution output (tab-separated)
    parts = resolution.split("|")
    if len(parts) < 1:
        return results
    actual_outcome = parts[0].strip().lower() in ("true", "t", "1", "yes")
    days_to_resolution = int(float(parts[1])) if len(parts) > 1 and parts[1].strip() else None

    # Get all completed simulation runs for this event (parse_success=true only)
    runs_raw = _psql(f"""
        SELECT
            sr.id as sim_id,
            sr.forecast_probability_yes,
            sr.run_status,
            sr.parse_success,
            e.category,
            ms.price_yes as market_price
        FROM prophet.simulation_runs sr
        JOIN prophet.events e ON sr.event_id = e.id
        JOIN prophet.market_snapshots ms ON sr.market_snapshot_id = ms.id
        WHERE sr.event_id = '{event_id}'
        AND sr.run_status = 'completed'
        AND sr.parse_success = true
        ORDER BY sr.created_at;
    """)

    if not runs_raw:
        return results

    for line in runs_raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        cols = line.split("|")
        if len(cols) < 6:
            continue

        sim_id = cols[0].strip()
        try:
            forecast = float(cols[1].strip())
        except (ValueError, IndexError):
            continue
        category = cols[3].strip() if len(cols) > 3 else ""
        try:
            market_price = float(cols[5].strip()) if len(cols) > 5 else 0.5
        except (ValueError, IndexError):
            market_price = 0.5

        # Compute scores
        sim_brier = compute_brier(forecast, actual_outcome)
        market_brier = compute_brier(market_price, actual_outcome)
        sim_better = sim_brier < market_brier
        market_correct = was_correct(market_price, actual_outcome)
        sim_correct = was_correct(forecast, actual_outcome)
        # Delta direction: did simulation point in the right direction vs market?
        delta_correct = (forecast > market_price) == actual_outcome

        # Write calibration result
        cal_id = create_calibration_result(
            simulation_run_id=sim_id,
            event_id=event_id,
            category=category,
            market_brier_score=round(market_brier, 6),
            simulation_brier_score=round(sim_brier, 6),
            simulation_better_than_market=sim_better,
            market_was_correct=market_correct,
            simulation_was_correct=sim_correct,
            delta_direction_correct=delta_correct,
            days_to_resolution=days_to_resolution,
        )

        results.append({
            "simulation_run_id": sim_id,
            "sim_brier": round(sim_brier, 6),
            "market_brier": round(market_brier, 6),
            "sim_better": sim_better,
            "sim_correct": sim_correct,
            "calibration_id": cal_id,
        })

    return results


def get_aggregate_brier_by_category() -> Dict[str, Dict]:
    """Aggregate Brier scores across all resolved events, grouped by category."""
    sql = """
        SELECT
            e.category,
            COUNT(*) as events,
            ROUND(AVG(cr.market_brier_score)::numeric, 6) as avg_market_brier,
            ROUND(AVG(cr.sim_brier_score)::numeric, 6) as avg_sim_brier,
            COUNT(*) FILTER (WHERE cr.sim_better_than_market = true) as sim_better_count,
            COUNT(*) FILTER (WHERE cr.market_was_correct = true) as market_correct,
            COUNT(*) FILTER (WHERE cr.sim_was_correct = true) as sim_correct
        FROM prophet.calibration_results cr
        JOIN prophet.events e ON cr.event_id = e.id
        GROUP BY e.category
        ORDER BY events DESC;
    """
    from prophet.pipeline.logger import _psql
    raw = _psql(sql)

    results = {}
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split("|")
        if len(parts) < 7:
            continue
        category = parts[0].strip()
        try:
            results[category] = {
                "events": int(parts[1].strip()),
                "avg_market_brier": float(parts[2].strip()),
                "avg_sim_brier": float(parts[3].strip()),
                "sim_better_count": int(parts[4].strip()),
                "market_correct": int(parts[5].strip()),
                "sim_correct": int(parts[6].strip()),
            }
        except (ValueError, IndexError):
            continue
    return results
