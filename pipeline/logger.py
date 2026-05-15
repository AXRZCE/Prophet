"""
logger.py — Prophet Postgres persistence layer (stdlib-only).

All Phase 1 pipeline components write through this module.
Uses docker exec + psql to avoid external Python dependencies.

Schema: prophet.* (8 tables, migrated)
Author: ClawBot + Akshar
Date: May 12, 2026
Version: v0.1
"""

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List


# --- Database connection via Docker ---

POSTGRES_CONTAINER = os.environ.get("PROPHET_DB_CONTAINER", "clawbot_postgres")
POSTGRES_USER = os.environ.get("PROPHET_DB_USER", "clawbot")
POSTGRES_DB = os.environ.get("PROPHET_DB_NAME", "clawbot")

_PSQL_BASE = ["docker", "exec", "-i", POSTGRES_CONTAINER, "psql", "-U", POSTGRES_USER, "-d", POSTGRES_DB]


def _psql(sql: str) -> str:
    """Run SQL and return stdout."""
    r = subprocess.run(
        _PSQL_BASE + ["-t", "-A", "-c", sql],
        capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0:
        raise RuntimeError(f"psql error: {r.stderr.strip()}")
    return r.stdout.strip()


def _psql_exec(sql: str) -> None:
    """Run SQL without capturing output (INSERT/UPDATE)."""
    subprocess.run(
        _PSQL_BASE + ["-c", sql],
        capture_output=True, text=True, timeout=30, check=True,
    )


def _psql_query(sql: str) -> List[Dict[str, Any]]:
    """Run a query and return rows as dicts."""
    r = subprocess.run(
        _PSQL_BASE + ["-t", "-A", "-F", "\t"],
        input=sql, capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0:
        raise RuntimeError(f"psql error: {r.stderr.strip()}")
    lines = [line for line in r.stdout.strip().split("\n") if line and line != ""]
    if not lines:
        return []
    # Get column headers separately
    col_r = subprocess.run(
        _PSQL_BASE + ["-t", "-A", "-F", "\t"],
        input=sql.split(";")[0] + " LIMIT 0;",
        capture_output=True, text=True, timeout=30,
    )
    return lines


def _psql_val(sql: str) -> Optional[str]:
    """Execute INSERT ... RETURNING id and return the UUID.
    Raises RuntimeError on psql failure (no more silent None).
    Returns None only if UUID parsing fails despite successful INSERT."""
    r = subprocess.run(
        _PSQL_BASE + ["-t", "-A", "-c", sql],
        capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0:
        # No more silent swallowing — this is a hard DB failure
        raise RuntimeError(f"psql INSERT failed (exit {r.returncode}): {r.stderr.strip()[:500]}")
    # psql -t -A output: UUID on one line, "INSERT 0 1" on next.
    # For ON CONFLICT DO UPDATE, we get "UPDATE 1" instead.
    for line in r.stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        # Skip psql notification lines
        if line.startswith("INSERT") or line.startswith("UPDATE") or line.startswith("DELETE"):
            continue
        # This should be the UUID
        if len(line) > 20:
            return line
    # INSERT succeeded but RETURNING parsing failed — log and return None
    print(f"[_psql_val] WARNING: UUID parse failed after successful INSERT. Output: {r.stdout.strip()[:200]}", flush=True)
    return None


def _escape_sql(val: str) -> str:
    """Escape a string for SQL literal. Handles single quotes and backslashes."""
    return val.replace("\\", "\\\\").replace("'", "''")


# --- Public API ---

def create_event(
    polymarket_event_id: str,
    market_title: str,
    category: str,
    resolution_criteria: str = "",
    resolution_deadline: Optional[datetime] = None,
    market_url: str = "",
    platform: str = "polymarket",
    event_track: str = "",
    hypothesis_validity: str = "",
    selection_reason: str = "",
    manual_selection: bool = False,
    source_cutoff_time: Optional[datetime] = None,
    historical_snapshot_time: Optional[datetime] = None,
) -> str:
    """Create a new event row. Returns event UUID."""
    deadline_val = f"'{resolution_deadline.isoformat()}'" if resolution_deadline else "NULL"
    cutoff_val = f"'{source_cutoff_time.isoformat()}'" if source_cutoff_time else "NULL"
    hist_snap_val = f"'{historical_snapshot_time.isoformat()}'" if historical_snapshot_time else "NULL"
    title = _escape_sql(market_title)
    criteria = _escape_sql(resolution_criteria)
    url = _escape_sql(market_url)
    reason = _escape_sql(selection_reason)
    manual_val = str(manual_selection).lower()

    sql = f"""INSERT INTO prophet.events (polymarket_event_id, market_title, market_url, category, resolution_criteria, resolution_deadline, status, platform, event_track, hypothesis_validity, selection_reason, manual_selection, source_cutoff_time, historical_snapshot_time)
VALUES ('{polymarket_event_id}', '{title}', '{url}', '{category}', '{criteria}', {deadline_val}, 'open', '{platform}', '{event_track}', '{hypothesis_validity}', '{reason}', {manual_val}, {cutoff_val}, {hist_snap_val})
ON CONFLICT (polymarket_event_id) DO UPDATE SET market_title = EXCLUDED.market_title
RETURNING id;"""
    return _psql_val(sql)


def create_market_snapshot(
    event_id: str,
    price_yes: float,
    price_no: float = None,
    volume_usd: float = None,
    liquidity_usd: float = None,
    snapshot_at: Optional[datetime] = None,
    source: str = "polymarket_gamma",
    raw_market_data: Optional[Dict[str, Any]] = None,
    raw_yes_bid: Optional[float] = None,
    raw_yes_ask: Optional[float] = None,
    raw_last_price: Optional[float] = None,
    normalized_price_yes: Optional[float] = None,
    price_source: str = "",
) -> str:
    """Capture price/volume at simulation trigger time."""
    if price_no is None:
        price_no = round(1.0 - price_yes, 4)
    if snapshot_at is None:
        snapshot_at = datetime.now(timezone.utc)
    vol = str(volume_usd) if volume_usd is not None else "NULL"
    liq = str(liquidity_usd) if liquidity_usd is not None else "NULL"
    r_bid = str(raw_yes_bid) if raw_yes_bid is not None else "NULL"
    r_ask = str(raw_yes_ask) if raw_yes_ask is not None else "NULL"
    r_last = str(raw_last_price) if raw_last_price is not None else "NULL"
    n_price = str(normalized_price_yes) if normalized_price_yes is not None else str(price_yes) if price_yes is not None else "NULL"
    raw_json = json.dumps(raw_market_data or {}).replace("'", "''") if raw_market_data else "NULL"
    p_source = _escape_sql(price_source)

    sql = f"""INSERT INTO prophet.market_snapshots (event_id, price_yes, price_no, volume_usd, liquidity_usd, snapshot_at, source, raw_market_data, raw_yes_bid, raw_yes_ask, raw_last_price, normalized_price_yes)
VALUES ('{event_id}', {price_yes}, {price_no}, {vol}, {liq}, '{snapshot_at.isoformat()}', '{source}', {raw_json}::jsonb, {r_bid}, {r_ask}, {r_last}, {n_price})
RETURNING id;"""
    return _psql_val(sql)


def create_seed(
    event_id: str,
    seed_doc_text: str,
    source_urls: List[str] = None,
    source_time_window: str = "",
    seed_builder_version: str = "v0.1",
    seed_quality: str = "medium",
    manual_edits: bool = False,
) -> str:
    """Store seed document with full provenance."""
    seed_doc_hash = hashlib.sha256(seed_doc_text.encode()).hexdigest()[:16]
    source_count = len(source_urls) if source_urls else 0
    text = _escape_sql(seed_doc_text)
    urls_json = json.dumps(source_urls or []).replace("'", "''")

    sql = f"""INSERT INTO prophet.seeds (event_id, seed_doc_text, seed_doc_hash, source_urls, source_count, source_time_window, seed_builder_version, seed_quality, manual_edits)
VALUES ('{event_id}', '{text}', '{seed_doc_hash}', '{urls_json}'::jsonb, {source_count}, '{source_time_window}', '{seed_builder_version}', '{seed_quality}', {str(manual_edits).lower()})
RETURNING id;"""
    return _psql_val(sql)


def create_simulation_run(
    event_id: str,
    seed_id: str,
    market_snapshot_id: str,
    mirofish_project_id: str = "",
    mirofish_simulation_id: str = "",
    mirofish_report_id: str = "",
    raw_report: str = "",
    structured_forecast: Optional[Dict[str, Any]] = None,
    forecast_probability_yes: Optional[float] = None,
    forecast_confidence: Optional[float] = None,
    forecast_direction: str = None,
    probability_source: str = "llm_extractor",
    parse_success: bool = False,
    parse_error: str = "",
    market_price_used_as_forecast: bool = False,
    run_status: str = "completed",
    prompt_template_version: str = "",
    agent_persona_version: str = "",
    report_parser_version: str = "",
    model_name_agents: str = "deepseek-chat",
    model_name_report: str = "deepseek-chat",
    temperature_agents: float = None,
    agent_count: int = None,
    round_count: int = None,
    simulation_duration_sec: int = None,
    api_cost_estimate: float = None,
) -> Optional[str]:
    """Insert one simulation run with parsed forecast."""
    forecast_json = _escape_sql(json.dumps(structured_forecast or {}))
    report = _escape_sql(raw_report or "")
    raw_size = len(raw_report or "")
    err = _escape_sql(parse_error or "")
    f_dir = _escape_sql(forecast_direction or "")
    f_temp = str(temperature_agents) if temperature_agents is not None else "NULL"
    f_agents = str(agent_count) if agent_count is not None else "NULL"
    f_rounds = str(round_count) if round_count is not None else "NULL"
    f_dur = str(simulation_duration_sec) if simulation_duration_sec is not None else "NULL"
    f_cost = str(api_cost_estimate) if api_cost_estimate is not None else "NULL"
    f_prob = str(forecast_probability_yes) if forecast_probability_yes is not None else "NULL"
    f_conf = str(forecast_confidence) if forecast_confidence is not None else "NULL"

    sql = f"""INSERT INTO prophet.simulation_runs (
    event_id, seed_id, market_snapshot_id,
    mirofish_project_id, mirofish_simulation_id, mirofish_report_id,
    prompt_template_version, agent_persona_version, report_parser_version,
    model_name_agents, model_name_report, temperature_agents, agent_count, round_count,
    raw_report, raw_report_size_chars,
    structured_forecast,
    forecast_probability_yes, forecast_confidence, forecast_direction,
    probability_source, parse_success, parse_error,
    market_price_used_as_forecast,
    simulation_duration_sec, api_cost_estimate, run_status
) VALUES (
    '{event_id}', '{seed_id}', '{market_snapshot_id}',
    '{mirofish_project_id}', '{mirofish_simulation_id}', '{mirofish_report_id}',
    '{prompt_template_version}', '{agent_persona_version}', '{report_parser_version}',
    '{model_name_agents}', '{model_name_report}', {f_temp}, {f_agents}, {f_rounds},
    '{report}', {raw_size},
    '{forecast_json}'::jsonb,
    {f_prob}, {f_conf}, '{f_dir}',
    '{probability_source}', {str(parse_success).lower()}, '{err}',
    {str(market_price_used_as_forecast).lower()},
    {f_dur}, {f_cost}, '{run_status}'
) RETURNING id;"""
    return _psql_val(sql)


def create_stability_diagnostic(
    simulation_run_id: str,
    prob_iqr: float = None,
    rerun_variance: float = None,
    convergence_round: int = None,
    cross_model_delta: float = None,
    hedging_flag: bool = False,
    fast_convergence_flag: bool = False,
    high_variance_flag: bool = False,
    model_sensitivity_flag: bool = False,
    overall_stability: str = None,
) -> str:
    """Store stability metrics for a simulation run."""
    p_iqr = str(prob_iqr) if prob_iqr is not None else "NULL"
    p_var = str(rerun_variance) if rerun_variance is not None else "NULL"
    p_conv = str(convergence_round) if convergence_round is not None else "NULL"
    p_delta = str(cross_model_delta) if cross_model_delta is not None else "NULL"
    stab = f"'{overall_stability}'" if overall_stability else "NULL"

    sql = f"""INSERT INTO prophet.stability_diagnostics (
    simulation_run_id, prob_iqr, rerun_variance, convergence_round,
    cross_model_delta, hedging_flag, fast_convergence_flag,
    high_variance_flag, model_sensitivity_flag, overall_stability
) VALUES (
    '{simulation_run_id}', {p_iqr}, {p_var}, {p_conv},
    {p_delta}, {str(hedging_flag).lower()}, {str(fast_convergence_flag).lower()},
    {str(high_variance_flag).lower()}, {str(model_sensitivity_flag).lower()}, {stab}
) RETURNING id;"""
    return _psql_val(sql)


def create_resolution(
    event_id: str,
    actual_outcome: bool,
    resolution_time: Optional[datetime] = None,
    resolution_source: str = "",
    disputed: bool = False,
    resolution_notes: str = "",
) -> str:
    """Store resolved ground truth. actual_outcome: True=YES, False=NO."""
    if resolution_time is None:
        resolution_time = datetime.now(timezone.utc)
    src = _escape_sql(resolution_source)
    notes = _escape_sql(resolution_notes)

    sql = f"""INSERT INTO prophet.resolutions (event_id, actual_outcome, resolution_time, resolution_source, disputed, resolution_notes)
VALUES ('{event_id}', {str(actual_outcome).lower()}, '{resolution_time.isoformat()}', '{src}', {str(disputed).lower()}, '{notes}')
RETURNING id;"""
    return _psql_val(sql)


def create_calibration_result(
    simulation_run_id: str,
    event_id: str,
    category: str = "",
    market_brier_score: float = None,
    simulation_brier_score: float = None,
    simulation_better_than_market: bool = None,
    market_was_correct: bool = None,
    simulation_was_correct: bool = None,
    delta_direction_correct: bool = None,
    days_to_resolution: int = None,
) -> str:
    """Store Brier scores after resolution. Only for parse_success=true runs."""
    m_brier = str(market_brier_score) if market_brier_score is not None else "NULL"
    s_brier = str(simulation_brier_score) if simulation_brier_score is not None else "NULL"
    sim_better = str(simulation_better_than_market).lower() if simulation_better_than_market is not None else "NULL"
    m_correct = str(market_was_correct).lower() if market_was_correct is not None else "NULL"
    s_correct = str(simulation_was_correct).lower() if simulation_was_correct is not None else "NULL"
    d_correct = str(delta_direction_correct).lower() if delta_direction_correct is not None else "NULL"
    days = str(days_to_resolution) if days_to_resolution is not None else "NULL"
    cat = _escape_sql(category)

    sql = f"""INSERT INTO prophet.calibration_results (
    simulation_run_id, event_id, category,
    market_brier_score, sim_brier_score,
    sim_better_than_market, market_was_correct, sim_was_correct,
    delta_direction_correct, days_to_resolution
) VALUES (
    '{simulation_run_id}', '{event_id}', '{cat}',
    {m_brier}, {s_brier},
    {sim_better}, {m_correct}, {s_correct},
    {d_correct}, {days}
) RETURNING id;"""
    return _psql_val(sql)


# --- Failure logging ---

def log_failed_run(event_id: str, error: str, context: Dict[str, Any] = None) -> Optional[str]:
    """Log a simulation that failed to execute (not a parse failure)."""
    return create_simulation_run(
        event_id=event_id,
        seed_id=event_id,  # placeholder
        market_snapshot_id=event_id,  # placeholder
        raw_report=json.dumps(context or {}),
        structured_forecast={"error": error},
        parse_success=False,
        parse_error=error,
        run_status="failed",
    )


def log_failed_parse(simulation_run_id: str, raw_report: str, error: str) -> None:
    """Mark an existing simulation run as parse_failed."""
    err = _escape_sql(error)
    err_json = _escape_sql(json.dumps(error))
    sql = f"""UPDATE prophet.simulation_runs
SET parse_success = false,
    parse_error = '{err}',
    structured_forecast = jsonb_set(COALESCE(structured_forecast, '{{}}'::jsonb), '{{error}}', '{err_json}'::jsonb)
WHERE id = '{simulation_run_id}';"""
    _psql_exec(sql)


# --- Query utilities (return dicts via text parsing) ---

def get_unresolved_events() -> List[str]:
    """Return list of event IDs that have no resolution yet."""
    sql = """SELECT e.id FROM prophet.events e
LEFT JOIN prophet.resolutions r ON e.id = r.event_id
WHERE r.id IS NULL AND e.status = 'open';"""
    return [v for v in _psql(sql).split("\n") if v.strip()]


def get_parser_success_rate() -> Dict[str, Any]:
    """Count parser success/failure across all completed runs."""
    sql = """SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE parse_success = true) as success,
    COUNT(*) FILTER (WHERE parse_success = false) as failed
FROM prophet.simulation_runs
WHERE run_status = 'completed';"""
    parts = _psql(sql).split("|")
    if len(parts) >= 3:
        total = int(parts[0].strip()) if parts[0].strip() else 0
        success = int(parts[1].strip()) if parts[1].strip() else 0
        failed = int(parts[2].strip()) if parts[2].strip() else 0
        return {
            "total_runs": total,
            "successful_parses": success,
            "failed_parses": failed,
            "success_rate_pct": round(100.0 * success / total, 1) if total > 0 else 0,
        }
    return {"total_runs": 0, "successful_parses": 0, "failed_parses": 0, "success_rate_pct": 0}


# --- Disk persistence (anti-loss for container restarts) ---

from pathlib import Path as _Path

_REPORT_DIR = _Path(__file__).resolve().parent.parent / "reports" / "phase1"
_REPORT_DIR.mkdir(parents=True, exist_ok=True)


def save_sim_artifact(sim_id: str, payload: dict, kind: str = "result"):
    """Save simulation artifact to disk as JSON."""
    path = _REPORT_DIR / f"{sim_id}_{kind}.json"
    path.write_text(json.dumps(payload, indent=2, default=str))
    return str(path)


def save_sim_markdown(sim_id: str, text: str, kind: str = "report"):
    """Save simulation report markdown to disk."""
    path = _REPORT_DIR / f"{sim_id}_{kind}.md"
    path.write_text(text)
    return str(path)
