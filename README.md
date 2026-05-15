# Prophet — Project Blueprint v1.6

**Status:** Phase 1.1 — Hardening + Observation
**Events:** 26 logged, 21 resolved, 14 scored
**Version:** 1.6
**Last Updated:** 2026-05-15
**Repos:** `AXRZCE/Prophet` (code only — clawbot-v2 MUST NOT contain Prophet code)

---

## The Core Idea

Prediction markets aggregate dispersed beliefs into prices (Hayek's insight, financialized). MiroFish simulates how beliefs form, spread, and polarize through social dynamics. Neither system alone closes the loop.

**The gap no one has filled:** A closed-loop system where simulated narrative dynamics → inform trading decisions → outcomes calibrate future simulations.

This is not about speed (HFT). It is about depth — modeling second and third-order narrative effects before the market prices them in.

---

## Current Status (Phase 1.1)

Phase 1 data collection is complete. Track C calibration is scored and the market beat simulation on every scored event. This was expected because Track C events are short-deadline stress tests with strong public data and high market efficiency.

Track C validates the pipeline, not the core Prophet hypothesis.

Track A remains the primary experiment. Track A calibration begins when live narrative events resolve.

### Key Phase 1 Finding

Prophet successfully measured the model and found that MiroFish narrative simulation was badly miscalibrated on short-deadline stress-test events. The market was substantially better calibrated. This is not a project failure — it is the purpose of the calibration lab.

### Track Summary

| Track | Platform | Events | Sims | Resolved | Scored | Sim Brier | Market Brier |
|---|---:|---:|---:|---:|---:|---:|
| Track A - Narrative | polymarket | 14 | 10 | 0 | 0 | — | — |
| Track B - Retrospective | kalshi | 5 | 0 | 5 | 0 | — | — |
| Track C - Stress Test | kalshi | 18 | 16 | 15 | 14 | 0.3900 | 0.0704 |

Simulations beat market: 0/16. Phase 2 locked until Track A proves edge.

---

## Why This Works: The Theoretical Backing

| System | What It Does | What It Doesn't Do |
|---|---|---|
| **Prediction Markets** | Aggregates dispersed beliefs into prices | Doesn't explain WHY; fails on low-liquidity events; biases from retail gamblers |
| **MiroFish / OASIS** | Simulates how beliefs form, spread, polarize through social dynamics | No financial calibration; agents have no skin in the game; no ground truth feedback loop |
| **AI Agents** | Autonomous perceive → reason → act loops at scale | No built-in narrative model; no belief formation simulation; just execution |

**Prophet fills the top-left quadrant:**

```
                    │ Has Narrative Model │ No Narrative Model
────────────────────┼───────────────────────┼──────────────────────
Connected to        │                       │
Real Markets        │     ★ PROPHET ★       │   Trading Bots
                    │     (this project)    │   DeFAI Agents
────────────────────┼───────────────────────┼──────────────────────
NOT Connected to    │                       │
Real Markets        │   MiroFish / OASIS    │   Academic ABM
                    │                       │   Statistical Models
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                       PROPHET SYSTEM                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────┐  │
│  │  NARRATIVE   │   │ MARKET LENS  │   │ DIVERGENCE  │  │
│  │   ENGINE     │──▶│              │──▶│ CALCULATOR  │  │
│  │ (MiroFish/   │   │ (Polymarket  │   │              │  │
│  │   OASIS)     │   │  Gamma API)  │   │ sim vs real  │  │
│  │              │   │              │   │  price delta │  │
│  └──────────────┘   └──────────────┘   └──────┬───────┘  │
│                                                 │         │
│                        ┌────────────────────────┘         │
│                        ▼                                  │
│  ┌──────────────┐   ┌──────────────┐                      │
│  │ CALIBRATION  │   │   LEARNING   │                      │
│  │   REPORT     │◀──│     LOOP     │                      │
│  │  (Phase 1    │   │              │                      │
│  │ deliverable) │   │ sim vs actual│                      │
│  │              │   │  resolution  │                      │
│  └──────────────┘   │ → Brier score│                      │
│                     └──────────────┘                      │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Execution engine — Phase 3+ only. Not built.         │ │
│  └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Gate History

| Gate | Requirement | Status |
|---|---|---|
| **G0** | MiroFish integration + parser + DB write | ✅ Full Pass |
| **G1** | Phase 1 pipeline build (8 modules) | ✅ Full Pass |
| **G1.5** | Smoke test — one live end-to-end run | ✅ Passed |
| **G2a** | 10 events logged, 7/10 parsed, events resolved, sim Brier better | ✅ 26/10 logged, 26/26 parsed, 21 resolved, Track C scored (0/16 sim wins — expected for stress tests) |

---

## Gate G0 Summary

Three successful MiroFish simulations (crypto protocol, crypto regulatory, company product), working probability parser, 8-table Postgres schema, and one end-to-end parsed DB write. Full details in Phase 0 section.

**Gate G0: ✅ Full Pass**

---

## Phase 0 — Infrastructure Results

### Resource Profile

| Metric | Value |
|---|---:|
| Docker image size | ~14GB |
| Container RAM idle | ~400MB |
| Container RAM during simulation | ~1.5GB |
| System free RAM after deployment | ~3.0GB of 7.8GB |
| Test simulation size | 13 agents, 5 rounds |
| Full pipeline runtime | ~10 minutes |
| Estimated API cost per simulation | ~$2.50 |

The existing ClawBot droplet is sufficient for Phase 1. Do not upgrade infrastructure.

### Phase 0 Test Simulations

| # | Event | Category | Agents | Rounds | Report Size |
|---|---|---|---|---|---|
| 1 | Ethereum Pectra Upgrade | crypto_protocol | 13 | 5 | 51KB |
| 2 | XRP Spot ETF Approval | crypto_regulatory | ~15 | 5 | 30KB |
| 3 | Anthropic $50B ARR | company_product | ~15 | 5 | 51KB |

### Blueprint vs Reality

| Blueprint Assumption | Phase 0 Finding |
|---|---|
| MiroFish uses FastAPI with `/docs` | MiroFish uses Flask — no auto-generated docs |
| `/openapi.json` available | API routes reverse-engineered from `backend/app/api/` |
| LiteLLM proxy required | Direct DeepSeek API works; LiteLLM not needed |
| ReportAgent may output JSON | ReportAgent outputs narrative markdown only — 3/3 confirmed |
| `host.docker.internal` for networking | Doesn't work on Linux — direct cloud API endpoints used |
| RAM would be tight | 2.0GB free even with MiroFish running |

---

## Phase 1 Smoke Test — Results

### First Live Run (2026-05-12)

```
Event: "U.S. enacts AI safety bill before 2027?"
Category: ai_narrative
Market price (YES): 0.28
Simulation forecast: 0.425
Delta: +0.145 (simulation more bullish than market)
Parse success: true
Confidence: 0.60
Anti-confusion: PASS (market 0.28 ≠ forecast 0.425)
Cost: ~$2.50
Latency: ~15 min end-to-end
```

### 7 Bugs Found and Fixed During Smoke Test

| # | Bug | Root Cause | Fix |
|---|---|---|---|
| 1 | `seed_hash` KeyError | Seed builder returns `seed_doc_hash`, code referenced `seed_hash` | Renamed key reference |
| 2 | `SEED` NameError | Global `SEED` variable referenced but doesn't exist | Changed to `seed["seed_builder_version"]` |
| 3 | Graph build HTTP 404 | `_poll_task` POSTed instead of GET to `f"/api/graph/task/{task_id}"` | Rewrote `_poll_task(method, path, data)` |
| 4 | Simulation never "completes" | Detection checked non-existent `reddit_completed`/`twitter_completed` fields | Added `status` field check: `s in ("completed", "stopped", "failed")` |
| 5 | `urllib` scoping error | `import urllib.request` inside `if files:` block shadowed module-level import | Removed local import |
| 6 | `platform` column doesn't exist | `create_event` INSERT referenced column never in schema | Removed `platform` from SQL and function signature |
| 7 | `_psql_val` returned None silently | psql exit code 1 on SQL error wasn't surfaced | Added `len(line) > 20` filter; root fix was removing `platform` |

All 7 were one-line fixes. The pipeline survived contact with reality.

### Smoke Test Verdict

The failures were real integration bugs, not architecture failures. Every fix was contained and local. The pipeline is now operational.

**Smoke test: ✅ Passed**

### Current Pipeline Dashboard

```
Prophet Phase 1 — Live Status (as of 2026-05-12)
═══════════════════════════════════════════════════
Events with completed simulations: 2
Simulation runs completed: 2
Successful parses: 2 (100%)
Failed parses: 0
Resolved events: 0
Calibration scores: 0 (awaiting resolution)
Gate G2a progress: 2/10
```

### DB State Note

`prophet.events` contains 6 rows but only 2 have completed simulation runs. The extra rows are likely from failed attempts or discovery inserts during debugging. Before scaling to 10 events, Gate G2a counts only events with at least one `completed` `simulation_run` — not raw event row count.

---

## MiroFish Integration Contract

MiroFish backend is Flask, not FastAPI. No `/docs` or OpenAPI schema. API routes were reverse-engineered from `backend/app/api/`.

### Real API Workflow

```
POST /api/graph/ontology/generate → project_id, ontology
POST /api/graph/build             → task_id → poll GET → graph_id
POST /api/simulation/create       → simulation_id
POST /api/simulation/prepare      → task_id → poll POST → ready
POST /api/simulation/start        → runs simulation
POST /api/report/generate         → task_id → poll POST → report_id
GET  /api/report/<report_id>      → markdown_content
```

**Polling note:** Graph build uses GET for status. Report status uses POST. Simulation prepare uses POST. `_poll_task(method, path, data)` must pass method explicitly.

**Completion detection:** MiroFish simulation status stays at `running`/`not_started` even after logs confirm completion. Check `status` field for `"completed"`, `"stopped"`, or `"failed"` — not platform-specific sub-fields.

### LLM Configuration

```
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL_NAME=deepseek-chat
```

Direct DeepSeek API, no LiteLLM. Do not reintroduce LiteLLM without a real reason.

---

## Probability Parser

### Core Design Lesson

> The parser's hardest job is not extracting a probability. It is deciding when the report is too ambiguous to trust.
>
> A failed parse is valid data. A confidently wrong parse contaminates the calibration study.

### Parser Strategy (Priority Order)

| Priority | Method | Status |
|---|---|---|
| 1 | Modify ReportAgent prompt to force final JSON block | Deferred — do not change MiroFish during Phase 1 |
| 2 | LLM extractor (second DeepSeek call) | ✅ Active — ~$0.05–0.10/sim |
| 3 | Regex extraction | Testing/verification only — never production |
| 4 | Manual extraction | **Forbidden** |

### Output Schema

**Success:**
```json
{
  "forecast_probability_yes": 0.425,
  "forecast_confidence": 0.60,
  "forecast_direction": "YES",
  "probability_source": "llm_extractor",
  "market_price_detected": 0.28,
  "market_price_used_as_forecast": false,
  "extracted_probability_ranges": ["40-45%"],
  "dominant_narrative": "one sentence",
  "contrarian_narrative": "one sentence",
  "final_reasoning": "one sentence",
  "parse_success": true,
  "parser_version": "v0.1"
}
```

**Failure:**
```json
{
  "forecast_probability_yes": null,
  "forecast_confidence": null,
  "forecast_direction": null,
  "probability_source": "llm_extractor",
  "market_price_detected": null,
  "market_price_used_as_forecast": false,
  "extracted_probability_ranges": [],
  "dominant_narrative": null,
  "contrarian_narrative": null,
  "final_reasoning": null,
  "parse_success": false,
  "error": "No clear simulation forecast found in report",
  "parser_version": "v0.1"
}
```

### Anti-Confusion Check — 4 Signals

Instead of a simple numeric comparison, the validator uses 4 signals:

1. **Numeric proximity** — is the forecast within 3% of market price?
2. **Agent estimate keywords** — does reasoning mention "weighted", "consensus", "agent", "converged"?
3. **Range count** — did the LLM extract multiple agent ranges (genuine synthesis) or just one?
4. **Market copy keywords** — does reasoning say "therefore this", "extracting this value", "market price is"?

Decision matrix:
- Market copy keywords without agent keywords → **FAIL** (copied)
- Agent keywords + multiple ranges → **PASS** (coincidence)
- Neither clearly → **PASS but note** (ambiguous)

The Pectra case (forecast=0.72, market=0.72) correctly passed because agent keywords and multiple ranges were present. XRP correctly flagged ambiguous.

### Parser Safety Rules

1. Market price references must not be treated as simulation forecasts.
2. Market prices are masked or separately tracked before extraction.
3. Parser output must include `market_price_used_as_forecast`.
4. Ambiguous reports must return `parse_success=false`.
5. Manual probability correction is forbidden.
6. Parser version must be stored for every run.
7. `parse_success=false` runs are excluded from Brier scoring, included in parser reliability metrics.
8. Never invent precision — if report says 60–65%, output midpoint 0.625 and record original range.

### Parser Test Suite (5/5 passing)

| # | Test | Expected | Status |
|---|---|---|---|
| 1 | Pectra report (agent-derived 0.72) | parse_success=true, forecast≠market_price | ✅ |
| 2 | XRP ETF report (structurally ambiguous) | parse_success=false | ✅ |
| 3 | Anthropic ARR report | parse_success=true, forecast=0.05 | ✅ |
| 4 | Anti-confusion: LLM returns exact market price | parse_success=false, market_price_used_as_forecast=true | ✅ |
| 5 | Garbage input | parse_success=false | ✅ |

---

## Prophet Postgres Schema

8 tables in `prophet.*` schema. Migrated and operational.

| Table | Purpose |
|---|---|
| `events` | One row per tracked market |
| `market_snapshots` | Price/volume at simulation trigger time |
| `seeds` | Source material used for each simulation |
| `simulation_runs` | One row per simulation execution + parsed forecast |
| `stability_diagnostics` | Per-run variance and convergence flags |
| `resolutions` | Ground truth outcomes after market resolution |
| `calibration_results` | Brier scores computed post-resolution |
| `parser_audit` | Full parser input/output log for debugging |

### Key Schema Rules

- `market_price_used_as_forecast` stored in `simulation_runs` — always populated
- `parser_version` stored in `simulation_runs` — every run, no exceptions
- `parse_success=false` runs kept in DB; excluded from Brier scoring; included in parser reliability metrics
- `structured_forecast` stored as JSONB in `simulation_runs`
- `raw_report` stored as TEXT in `simulation_runs`
- Market snapshot captured at simulation trigger time, not discovery time

---

## Phase 1 Pipeline — All 8 Modules

| # | Module | Lines | Status |
|---|---|---|---|
| 1A | `logger.py` | 380 | ✅ Operational |
| 1B | `mirofish_runner.py` | 250 | ✅ Operational |
| 1C | `market_scanner.py` | 200 | ✅ Operational (403 fixed) |
| 1D | `seed_builder.py` | 230 | ✅ Operational |
| 1E | `run_calibration.py` | 260 | ✅ Operational |
| 1F | `resolution_monitor.py` | 120 | ⬜ Built, cron not yet set up |
| 1G | `forecast_comparison.py` | 160 | ✅ Built, awaiting resolved events |
| 1H | `calibration_report.py` | 190 | ✅ Generates cleanly |

**Total:** ~1,990 lines, stdlib-only, no pip dependencies.

### Architecture Decisions

| Decision | Rationale |
|---|---|
| Stdlib-only (`subprocess` + `psql -c`) | No pip on host; works better than psycopg2 for this deployment |
| `market_scanner.py` discovers, `logger.py` snapshots at trigger time | Scanner finds candidates; trigger-time snapshot prevents stale price data |
| `mirofish_runner.py` does NOT parse probabilities | Runner returns raw reports only; parser called separately by orchestrator |
| Calibration only for `parse_success=true` runs | Prevents bad data from contaminating calibration |
| MiroFish ReportAgent prompt unchanged | Changing it changes the experiment; defer until after 10–20 events |

### Market Data Fallback Rule

If automated Polymarket discovery fails due to API access restrictions, Prophet may proceed with manual event selection as long as:

1. The market URL/ID is stored.
2. The market snapshot is captured at simulation trigger time.
3. The event selection source is marked `manual`.
4. No trading credentials are used.

---

## Phase 1 — Operating Rules

### Event Count Progression

Do not jump directly to 10. Use staged progression:

```
2 events → 3 events → 5 events → 10 events
    ↑          ↑
 one clean    review: parser rate,
 no-code-     runtime, seed quality,
 change run   category mix, DB hygiene
 first
```

**Current:** 2 events. Next target: one clean run with zero code changes.

### Allowed Event Categories

| Category | Allowed |
|---|---|
| `crypto_protocol` | ✅ |
| `crypto_regulatory` | ✅ |
| `company_product` | ✅ |
| `ai_narrative` | ✅ |
| Sports | ❌ |
| Pure macro | ❌ |
| Elections | ❌ |
| Celebrity/culture | ❌ |
| Low-liquidity meme | ❌ |

### Frozen Simulation Config (first 10 events)

```
model: deepseek-chat
agents: 13–15
rounds: 5
parser_version: v0.1
seed_builder_version: v0.1
```

Do not tune configuration mid-study. Config changes require a new version tag and a new experiment batch.

### Market Filters (Polymarket)

- Binary YES/NO only
- Volume > $50K
- Probability between 15% and 85%
- 7–60 days to expected resolution
- Prefer crypto/regulatory/company narrative events

### Event Status Lifecycle

Use consistent statuses across all events:

```
discovered → seeded → simulation_completed → parse_success / parse_failed
→ pending_resolution → resolved → scored / abandoned
```

### Gate G2a Counting Rule

Gate G2a counts only events with at least one `simulation_run` in `run_status = 'completed'`. Raw `prophet.events` row count is not the G2a metric.

Calibration report should display:

```
events_discovered
events_with_snapshots
events_with_seeds
events_with_completed_simulations ← this is the G2a count
events_scored
```

---

## Gate G2a — Phase 1 Exit Criteria

| Requirement | Status |
|---|---|
| 10 events with completed simulations | ⏳ 2/10 |
| 7/10 parse successfully | ⏳ 2/2 so far |
| No systematic market-price-copy failure | ✅ Clean so far |
| Resolution monitor cron active | ⬜ Not set up |
| At least some events resolved | ⬜ 0 resolved |
| Sim Brier directionally better than market Brier | ⬜ No data |
| No major stability flags | ⬜ Pending diagnostics |

**G2a overall: 2/10 events. Not started on scoring.**

Perfection is not required. Clean data is required.

---

## Immediate Next Steps

### Step 1 — Set Up Resolution Monitor Cron (do this first)

Before adding any more events, the resolution monitor must be running. Once you have 10 events, missing a resolution damages the calibration loop.

```bash
# Add to crontab
0 9 * * * cd /home/akshar/clawbot-v2/prophet && python3 pipeline/resolution_monitor.py >> logs/resolution_monitor.log 2>&1
```

Manual commands for testing:
```bash
python3 pipeline/resolution_monitor.py --dry-run
python3 pipeline/resolution_monitor.py --once
```

Expected behavior:
- Find all events with `run_status = pending_resolution`
- Check Polymarket Gamma for resolution
- If unresolved: no-op
- If resolved: write `resolutions` row + compute `calibration_results`

### Step 2 — One Clean Run With Zero Code Changes

Run one more event end-to-end. Verify no code changes are needed. This is the proof that the 7-bug fixes stuck.

```bash
python3 pipeline/run_calibration.py --event-id <new_event_id>
```

If it completes cleanly (even with `parse_success=false`), the pipeline is stable.

### Step 3 — Scale to 5 Events

After the clean run, add events to reach 5 total. At 5 events, pause and review:

- Parser success rate so far
- Average simulation runtime
- Seed quality distribution
- DB row cleanliness
- Any failure logs

### Step 4 — Scale to 10 Events

Only after the 5-event review is clean. Gate G2a formally starts at 10.

### Step 5 — Generate Calibration Report at 10 Events

```bash
python3 pipeline/calibration_report.py
```

Review for G2a checklist. If no events have resolved yet, use Phase 1.5 replay on historical Polymarket markets with known outcomes.

---

## What Is Not Being Built (Phase 1 Hard Boundary)

| Component | Phase |
|---|---|
| Trading execution engine | Phase 3+ |
| Wallet integration | Phase 3+ |
| Order placement code | Phase 3+ |
| Kalshi integration | Phase 2+ |
| Position sizing logic | Phase 3+ |
| Dashboard / UI | Phase 2+ |
| Paper trading simulation | Phase 2 |

Phase 1 is a research instrument. The only deliverable is a calibration report.

---

## Risk Register

| ID | Risk | Likelihood | Impact | Mitigation | Fallback |
|---|---|---|---|---|---|
| R01 | MiroFish API breaks on update | Low | High | Pin Docker image version | Re-run Phase 0 tests on new image |
| R02 | DeepSeek API cost exceeds budget | Low | Medium | ~$2.50/sim; 10 events = ~$25 total | Switch to cheaper model for agents |
| R03 | Droplet RAM insufficient at scale | Low | Medium | 2.0GB free confirmed | Upgrade droplet only if needed |
| R04 | Polymarket API changes | Medium | Medium | Use Gamma API; monitor changelog | Fall back to manual event selection |
| R05 | Parser fails on new report formats | Medium | High | Version all parser runs | Flag as `parse_success=false`; improve prompt |
| R06 | Events don't resolve during Phase 1 | Medium | Medium | Select 7–60 day events | Extend timeline; use Phase 1.5 replay |
| R07 | Simulation results are too noisy | Medium | Medium | Freeze config; track stability diagnostics | Rerun; analyze variance |
| R08 | Zep free tier rate limits | Low | Low | Usage within limits | Upgrade Zep tier |
| R09 | CFTC/regulatory risk | Low | High | Phase 1 is research only; no trading | Keep execution out until legal review |
| R10 | MiroFish agents homogenize | Low | Medium | OASIS convergence prevention built in | Monitor convergence_round |
| R11 | Seed quality too low | Medium | Medium | Require minimum 3 sources | Reject low-quality seeds; improve builder |
| R12 | Parser contamination from market price references | Medium | Very High | Mask market price; 5-heuristic validator; reject ambiguous | Exclude failed parses from calibration |
| R13 | Ambiguous reports reduce sample size | Medium | Medium | Track parser success rate; 7/10 threshold | Improve seed format after Phase 1 |
| R14 | Polymarket API blocked from cloud IP | High | High | Browser-like headers; manual event IDs; local scanner bridge | Manual event selection for all Phase 1 |
| R15 | DB row count drifts from G2a event count | Medium | Medium | Count only completed simulation runs; track lifecycle states | Clean test rows; mark abandoned |
| R16 | Events resolve before resolution monitor active | Medium | High | Set up cron before scaling past 2 events | Backfill manually from Polymarket data |

---

## Directory Structure

```
prophet/
├── phase0/
│   ├── reports/
│   │   ├── sim01_pectra.md
│   │   ├── sim02_xrp_etf.md
│   │   └── sim03_anthropic_arr.md
│   └── metadata/
│       ├── sim01_pectra.json
│       ├── sim02_xrp_etf.json
│       └── sim03_anthropic_arr.json
├── pipeline/
│   ├── logger.py                 ← ✅ 380 lines, live
│   ├── mirofish_runner.py        ← ✅ 250 lines, live
│   ├── market_scanner.py         ← ✅ 200 lines, 403 fixed
│   ├── seed_builder.py           ← ✅ 230 lines, live
│   ├── probability_parser.py     ← ✅ 5/5 tests pass
│   ├── run_calibration.py        ← ✅ 260 lines, smoke tested
│   ├── resolution_monitor.py     ← ✅ built, cron pending
│   ├── forecast_comparison.py    ← ✅ Brier math verified
│   └── calibration_report.py     ← ✅ generates cleanly
├── schema/
│   └── schema.sql                ← ✅ 8 tables, migrated
├── tests/
│   └── test_probability_parser.py ← ✅ 5/5 passing
├── logs/
│   └── resolution_monitor.log
└── reports/
    └── phase_1_calibration_report.md
```

---

## Version History

| Version | Date | Changes |
|---|---|---|
| v1.0 | — | Initial blueprint |
| v1.1 | — | MiroFish research added |
| v1.2 | 2026-05-11 | Phase 0 conditional pass; Flask correction; LiteLLM removal; resource profile |
| v1.3 | 2026-05-12 | Phase 0 full pass; parser built; schema migrated; DB write confirmed |
| v1.4 | 2026-05-12 | Gate G0 full pass; Phase 1 build order and all 8 module specs |
| v1.5 | 2026-05-12 | Phase 1 pipeline operational; smoke test passed; 7 bugs fixed; G2a at 2/10; R14–R16 added; event lifecycle states; fallback rules |
