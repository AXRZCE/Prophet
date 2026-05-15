"""
mirofish_runner.py — MiroFish API adapter for Prophet.

Wraps the reverse-engineered Flask workflow. Submits seed documents, runs
simulations, and returns raw ReportAgent markdown. Does NOT parse probabilities
(that's probability_parser.py's job).

API endpoints (Flask, not FastAPI — no /docs):
  POST /api/graph/ontology/generate  → project_id, ontology
  POST /api/graph/build              → task_id → poll → graph_id
  POST /api/simulation/create        → simulation_id
  POST /api/simulation/prepare       → task_id → poll → ready
  POST /api/simulation/start         → runs agents
  POST /api/report/generate          → task_id → poll → report_id
  GET  /api/report/<report_id>       → markdown_content
  POST /api/simulation/stop          → kill processes, free RAM

Author: ClawBot + Akshar
Date: May 12, 2026
Version: v0.3 — Concurrent sim limiter + auto-cleanup
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


MIROFISH_BASE_URL = os.environ.get("MIROFISH_URL", "http://localhost:5001")
MAX_CONCURRENT_SIMS = 2

# Timeouts
POLL_INTERVAL_SEC = 8
ONTOLOGY_TIMEOUT_SEC = 60
BUILD_TIMEOUT_SEC = 180
PREPARE_TIMEOUT_SEC = 180
SIM_START_TIMEOUT_SEC = 30
SIM_RUN_TIMEOUT_SEC = 600  # wait for agents to finish
REPORT_TIMEOUT_SEC = 300

# Step timing log (module-level for diagnostics)
_step_timings = []


def _log_step(step: str, status: str, duration_sec: float = 0, **meta):
    """Log step timing for diagnostics."""
    entry = {"step": step, "status": status, "duration_sec": round(duration_sec, 1), **meta}
    _step_timings.append(entry)
    print(f"  [{step}] {status} ({round(duration_sec, 1)}s){' — ' + str(meta.get('error','')) if status == 'failed' else ''}")


def get_step_timings():
    return list(_step_timings)


def _log_failed_to_db(event_id: str, step: str, error: str):
    """Log a failed simulation attempt to prophet.simulation_runs."""
    try:
        from prophet.pipeline.logger import log_failed_run
        log_failed_run(event_id or "unknown", f"[{step}] {error}", {"step": step, "error": error})
    except Exception:
        pass  # best-effort


def _api(method: str, path: str, data: dict = None, files: dict = None) -> dict:
    """Call MiroFish API and return JSON response."""
    url = f"{MIROFISH_BASE_URL}{path}"

    if files:
        # Multipart upload
        boundary = "----FormBoundary7MA4YWxkTrZu0gW"
        body = b""
        for key, val in data.items():
            body += f"--{boundary}\r\n".encode()
            body += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
            body += f"{val}\r\n".encode()
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="files"; filename="seed.md"\r\n'.encode()
        body += b"Content-Type: application/octet-stream\r\n\r\n"
        body += files["files"][1]  # (filename, content_bytes)
        body += f"\r\n--{boundary}--\r\n".encode()

        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        })
    elif data:
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json"
        })
    else:
        req = urllib.request.Request(url)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else str(e)
        return {"success": False, "error": f"HTTP {e.code}: {error_body[:500]}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _poll_task(method: str, path: str, data: dict = None, timeout_sec: int = 300, label: str = "task") -> dict:
    """Poll an async task until completion or timeout."""
    elapsed = 0
    while elapsed < timeout_sec:
        result = _api(method, path, data)
        if not result.get("success"):
            return result
        status = result.get("data", {}).get("status", "")
        if status in ("completed", "ready"):
            return result
        if status == "failed":
            return result
        time.sleep(POLL_INTERVAL_SEC)
        elapsed += POLL_INTERVAL_SEC
    return {"success": False, "error": f"{label} timed out after {timeout_sec}s"}


def run_simulation(
    seed_doc: str,
    simulation_requirement: str,
    project_name: str = "Prophet Test",
    enable_twitter: bool = True,
    enable_reddit: bool = True,
    max_rounds: int = 5,
    event_id: str = None,
) -> dict:
    """
    Run a complete MiroFish simulation from seed to report.

    Each step is timed and logged. Failed steps are written to DB.

    Returns dict with project_id, graph_id, simulation_id, report_id,
    raw_report_markdown, step_timings, status, error.
    """
    global _step_timings
    _step_timings = []

    # Gate: limit concurrent MiroFish sims to prevent OOM
    if not _wait_for_sim_slot():
        result = {
            "project_id": None, "graph_id": None, "simulation_id": None,
            "report_id": None, "raw_report_markdown": None,
            "agent_count": 0, "round_count": max_rounds, "duration_sec": 0,
            "step_timings": [], "status": "failed",
            "error": "Too many concurrent MiroFish simulations",
        }
        return result

    start_time = time.time()
    result = {
        "project_id": None,
        "graph_id": None,
        "simulation_id": None,
        "report_id": None,
        "raw_report_markdown": None,
        "agent_count": 0,
        "round_count": max_rounds,
        "duration_sec": 0,
        "step_timings": [],
        "status": "failed",
        "error": None,
    }

    def _fail(step_name, msg):
        result["error"] = f"[{step_name}] {msg}"
        _log_failed_to_db(event_id, step_name, msg)
        return result

    # Duplicate prevention: skip if this event already has a completed sim
    if event_id and has_completed_sim(event_id):
        result["status"] = "skipped"
        result["error"] = "Duplicate prevention — event already simulated"
        print(f"  [skip] Event already has completed sim, skipping", flush=True)
        return result

    try:
        # ── Step 1: Upload seed + generate ontology ──
        t0 = time.time()
        _log_step("ontology", "started")
        seed_bytes = seed_doc.encode("utf-8")
        resp = _api("POST", "/api/graph/ontology/generate",
                     data={
                         "simulation_requirement": simulation_requirement,
                         "project_name": project_name,
                     },
                     files={"files": ("seed.md", seed_bytes)})
        _log_step("ontology", "completed" if resp.get("success") else "failed",
                  time.time() - t0, error=resp.get("error", ""))

        if not resp.get("success"):
            return _fail("ontology", resp.get("error", "unknown"))

        project_id = resp["data"]["project_id"]
        result["project_id"] = project_id

        # ── Step 2: Build knowledge graph ──
        t0 = time.time()
        _log_step("graph_build", "started", project_id=project_id)
        resp = _api("POST", "/api/graph/build", {"project_id": project_id})
        if not resp.get("success"):
            return _fail("graph_build", resp.get("error", "unknown"))

        task_id = resp["data"]["task_id"]
        task_result = _poll_task("GET", f"/api/graph/task/{task_id}", None,
                                 BUILD_TIMEOUT_SEC, "graph build")
        if task_result.get("data", {}).get("status") != "completed":
            return _fail("graph_build", task_result.get("error", "timeout"))

        proj_resp = _api("GET", f"/api/graph/project/{project_id}")
        graph_id = proj_resp.get("data", {}).get("graph_id")
        if not graph_id:
            return _fail("graph_build", "no graph_id in project after build")
        result["graph_id"] = graph_id
        _log_step("graph_build", "completed", time.time() - t0, graph_id=graph_id)

        # ── Step 3: Create simulation ──
        t0 = time.time()
        _log_step("sim_create", "started")
        resp = _api("POST", "/api/simulation/create", {
            "project_id": project_id,
            "enable_twitter": enable_twitter,
            "enable_reddit": enable_reddit,
        })
        if not resp.get("success"):
            return _fail("sim_create", resp.get("error", "unknown"))

        simulation_id = resp["data"]["simulation_id"]
        result["simulation_id"] = simulation_id
        result["agent_count"] = resp["data"].get("entities_count", 0)
        _log_step("sim_create", "completed", time.time() - t0, simulation_id=simulation_id)

        # ── Step 4: Prepare simulation ──
        t0 = time.time()
        _log_step("sim_prepare", "started")
        resp = _api("POST", "/api/simulation/prepare", {"simulation_id": simulation_id})
        if not resp.get("success"):
            return _fail("sim_prepare", resp.get("error", "unknown"))

        # Poll prepare status
        task_id = resp["data"].get("task_id", "")
        elapsed = 0
        while elapsed < PREPARE_TIMEOUT_SEC:
            state_resp = _api("GET", f"/api/simulation/{simulation_id}")
            cfg_ready = state_resp.get("data", {}).get("config_generated", False)
            if cfg_ready:
                break
            time.sleep(POLL_INTERVAL_SEC)
            elapsed += POLL_INTERVAL_SEC

        if elapsed >= PREPARE_TIMEOUT_SEC:
            return _fail("sim_prepare", f"timeout after {PREPARE_TIMEOUT_SEC}s")

        profiles = state_resp.get("data", {}).get("profiles_count", 0)
        entities = state_resp.get("data", {}).get("entities_count", 0)
        result["agent_count"] = profiles or entities or result["agent_count"]
        _log_step("sim_prepare", "completed", time.time() - t0, agents=result["agent_count"])

        # ── Step 5: Start simulation ──
        t0 = time.time()
        _log_step("sim_start", "started", rounds=max_rounds)
        resp = _api("POST", "/api/simulation/start", {
            "simulation_id": simulation_id,
            "max_rounds": max_rounds,
        })
        if not resp.get("success"):
            return _fail("sim_start", resp.get("error", "unknown"))
        _log_step("sim_start", "running", time.time() - t0)

        # ── Step 5b: Wait for agents to complete ──
        t0 = time.time()
        _log_step("sim_run", "waiting", rounds=max_rounds)
        expected_wait = max_rounds * 90 + 30  # per round + overhead
        wait_time = min(expected_wait, SIM_RUN_TIMEOUT_SEC)

        # Poll for completion
        elapsed = 0
        while elapsed < wait_time:
            time.sleep(POLL_INTERVAL_SEC)
            elapsed += POLL_INTERVAL_SEC
            # Check run status
            try:
                status_resp = _api("GET", f"/api/simulation/{simulation_id}/run-status")
                run_status = status_resp.get("data", {}).get("status", "")
                if run_status in ("completed", "finished"):
                    break
            except Exception:
                pass

        _log_step("sim_run", "completed", elapsed,
                  rounds=max_rounds, agents=result["agent_count"])

        # ── Step 6: Generate report + poll for completion ──
        t0 = time.time()
        _log_step("report", "started")

        # Trigger async generation
        _api("POST", "/api/report/generate", {"simulation_id": simulation_id})

        # Poll GET /api/report/check/{simulation_id} until completed
        report_id = None
        elapsed = 0
        while elapsed < REPORT_TIMEOUT_SEC:
            time.sleep(5)
            elapsed += 5
            try:
                check = _api("GET", f"/api/report/check/{simulation_id}")
                if check.get("data", {}).get("has_report"):
                    rstat = check["data"].get("report_status", "")
                    if rstat == "completed":
                        report_id = check["data"]["report_id"]
                        break
            except Exception:
                pass

        if not report_id:
            return _fail("report", f"no completed report after {REPORT_TIMEOUT_SEC}s")
        result["report_id"] = report_id
        _log_step("report", "completed", time.time() - t0, report_id=report_id)

        # ── Step 7: Fetch report markdown (retry until content available) ──
        t0 = time.time()
        _log_step("fetch", "started")
        markdown = ""
        for attempt in range(12):
            time.sleep(3)
            resp = _api("GET", f"/api/report/{report_id}")
            markdown = resp.get("data", {}).get("markdown_content", "")
            if markdown:
                break

        if not markdown:
            return _fail("fetch", "markdown_content empty after retries")

        result["raw_report_markdown"] = markdown
        result["status"] = "completed"
        _log_step("fetch", "completed", time.time() - t0, chars=len(markdown))

    except Exception as e:
        result["error"] = f"Unexpected: {str(e)}"

    finally:
        result["duration_sec"] = int(time.time() - start_time)
        result["step_timings"] = get_step_timings()

        # Cleanup: stop the MiroFish simulation process to free RAM
        if result.get("simulation_id"):
            try:
                _stop_simulation(result["simulation_id"])
            except Exception:
                pass  # best-effort cleanup

    return result


def count_running_mirofish_sims() -> int:
    """Count run_parallel_simulation.py processes inside the MiroFish container."""
    try:
        r = subprocess.run(
            ["docker", "exec", "mirofish", "sh", "-c",
             "ps aux | grep run_parallel_simulation | grep -v grep | wc -l"],
            capture_output=True, text=True, timeout=10,
        )
        return int(r.stdout.strip() or 0)
    except Exception:
        return 0  # assume safe


def has_completed_sim(event_id: str) -> bool:
    """Check if an event already has a completed simulation run in the DB.
    Prevents duplicate runs from batch scripts that get killed and re-launched."""
    try:
        from prophet.pipeline.logger import _psql
        count = _psql(f"SELECT COUNT(*) FROM prophet.simulation_runs WHERE event_id = '{event_id}' AND run_status = 'completed';")
        return int(count.strip()) > 0 if count and count.strip() else False
    except Exception:
        return False  # assume no existing sim on error


def _wait_for_sim_slot(max_wait_sec: int = 600) -> bool:
    """Block until fewer than MAX_CONCURRENT_SIMS are running. Returns True if slot available."""
    deadline = time.time() + max_wait_sec
    while time.time() < deadline:
        running = count_running_mirofish_sims()
        if running < MAX_CONCURRENT_SIMS:
            return True
        print(f"  [gate] {running}/{MAX_CONCURRENT_SIMS} sims running, waiting for slot...", flush=True)
        time.sleep(15)
    print(f"  [gate] Timed out waiting for sim slot after {max_wait_sec}s", flush=True)
    return False


def _stop_simulation(simulation_id: str) -> None:
    """Kill a MiroFish simulation to free memory (run_parallel_simulation.py process)."""
    try:
        _api("POST", "/api/simulation/stop", {"simulation_id": simulation_id})
    except Exception:
        pass  # best-effort, process may already be dead
