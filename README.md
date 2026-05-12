# Prophet — Project Blueprint v1.4

**Status:** Gate G0 Passed — Phase 1 Ready
**Version:** 1.4
**Last Updated:** 2026-05-12
**Repos:** `AXRZCE/Prophet` (main), `AXRZCE/clawbot-v2` (master)

---

## The Core Idea

Prediction markets aggregate dispersed beliefs into prices (Hayek's insight, financialized). MiroFish simulates how beliefs form, spread, and polarize through social dynamics. Neither system alone closes the loop.

**The gap no one has filled:** A closed-loop system where simulated narrative dynamics → inform trading decisions → outcomes calibrate future simulations.

This is not about speed (HFT). It is about depth — modeling second and third-order narrative effects before the market prices them in.

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
│  │   OASIS)     │   │   + Kalshi   │   │ sim vs real  │  │
│  │              │   │     APIs)    │   │  price delta │  │
│  └──────────────┘   └──────────────┘   └──────┬───────┘  │
│                                                 │         │
│                        ┌────────────────────────┘         │
│                        ▼                                  │
│  ┌──────────────┐   ┌──────────────┐                      │
│  │  EXECUTION   │   │   LEARNING   │                      │
│  │   ENGINE     │──▶│     LOOP     │                      │
│  │  (Phase 3+)  │   │              │                      │
│  │              │   │ sim vs actual│                      │
│  │  position    │   │  resolution  │                      │
│  │  sizing +    │   │  → calibrate │                      │
│  │  trade exec  │   └──────────────┘                      │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Gate G0 Result

Gate G0 passed after three successful MiroFish simulations, a working probability parser, a migrated Prophet Postgres schema, and one end-to-end parsed database write.

The core integration risk is cleared. Phase 1 may begin.

### Gate G0 Final Checklist

| Requirement | Status |
|---|---|
| MiroFish deploys on existing infra | ✅ Passed |
| Full seed→graph→simulation→report pipeline | ✅ Passed |
| Programmatic API workflow verified | ✅ Passed |
| Async polling documented | ✅ Passed |
| Direct DeepSeek API works | ✅ Passed |
| Zep graph generation | ✅ Passed |
| 3 test simulations (different categories) | ✅ Passed |
| Resource profile measured | ✅ Passed |
| ReportAgent output format known | ✅ Passed |
| Structured probability native output | ❌ Not native — parser required |
| Probability parser (`probability_parser.py`) | ✅ Built, 5/5 tests pass |
| Anti-market-price-copy logic | ✅ 5-heuristic validator |
| Prophet Postgres schema (8 tables) | ✅ Migrated |
| One end-to-end parsed DB write | ✅ Confirmed |
| **Gate G0** | ✅ **Full Pass** |

---

## Phase 0 Infrastructure Results

### What Was Confirmed

Three end-to-end simulations completed successfully across all required event categories:

| # | Event | Category | Agents | Rounds | Report Size |
|---|---|---|---|---|---|
| 1 | Ethereum Pectra Upgrade | crypto_protocol | 13 | 5 | 51KB |
| 2 | XRP Spot ETF Approval | crypto_regulatory | ~15 | 5 | 30KB |
| 3 | Anthropic $50B ARR | company_product | ~15 | 5 | 51KB |

### Phase 0 Resource Profile

| Metric | Value |
|---|---:|
| Docker image size | ~14GB |
| Container RAM idle | ~400MB |
| Container RAM during simulation | ~1.5GB |
| Full system free RAM after deployment | ~2.0GB of 7.8GB |
| Test simulation size | 13 agents, 5 rounds |
| Full pipeline runtime | ~10 minutes |
| Estimated API cost per simulation | ~$2.50 |

The existing ClawBot droplet is sufficient for Phase 1. Do not upgrade infrastructure.

### What Changed From Blueprint Assumptions

| Blueprint Assumption | Phase 0 Finding |
|---|---|
| MiroFish uses FastAPI with `/docs` | MiroFish uses Flask — no auto-generated docs |
| `/openapi.json` available for client generation | API routes reverse-engineered from `backend/app/api/` |
| LiteLLM proxy required on port 4000 | LiteLLM is embedded in OpenClaw; direct DeepSeek works |
| ReportAgent may output structured JSON | ReportAgent outputs narrative markdown only — 3/3 confirmed |
| `host.docker.internal` for Docker networking | Doesn't work on Linux — direct cloud API endpoints used |
| RAM would be tight | 2.0GB free even with MiroFish running |

---

## MiroFish Integration Contract

MiroFish backend is Flask, not FastAPI. There is no `/docs` or OpenAPI schema. API routes were reverse-engineered from `backend/app/api/`.

### Real API Workflow

```
POST /api/graph/ontology/generate → project_id, ontology
POST /api/graph/build             → task_id → poll → graph_id
POST /api/simulation/create       → simulation_id
POST /api/simulation/prepare      → task_id → poll → ready
POST /api/simulation/start        → runs simulation
POST /api/report/generate         → task_id → poll → report_id
GET  /api/report/<report_id>      → markdown_content
```

### LLM Configuration

Phase 0 and Phase 1 use direct DeepSeek API through OpenAI-compatible SDK format.

```
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL_NAME=deepseek-chat
```

LiteLLM proxy is not required for Phase 1. Direct DeepSeek reduces RAM and infrastructure complexity. LiteLLM may be reintroduced later only if model routing becomes necessary. Do not add it back without a real reason.

---

## Probability Parser

### Design Lesson

> The parser's hardest job is not extracting a probability. It is deciding when the report is too ambiguous to trust.
>
> A failed parse is valid data. A confidently wrong parse contaminates the calibration study.

### ReportAgent Output

ReportAgent does not natively produce structured JSON probability output. It produces narrative markdown reports with embedded probability ranges and qualitative signals.

Therefore, Prophet Phase 1 requires `probability_parser.py`.

### Parser Strategy (Priority Order)

| Priority | Method | When |
|---|---|---|
| 1 | Modify ReportAgent prompt to force final JSON block | Test first — if consistent, use as primary |
| 2 | LLM extractor (second DeepSeek call) | Primary fallback; ~$0.05–0.10/sim |
| 3 | Regex extraction | Testing/verification only — never production |
| 4 | Manual extraction | **Forbidden** |

**Current implementation:** LLM extractor (Priority 2). Priority 1 testing deferred until after 10 Phase 1 events. Do not modify MiroFish ReportAgent prompt during Phase 1 — changing it changes the experiment.

### Parser Output Schema

**Success:**
```json
{
  "forecast_probability_yes": 0.67,
  "forecast_confidence": 0.54,
  "forecast_direction": "YES",
  "probability_source": "llm_extractor",
  "market_price_detected": 0.72,
  "market_price_used_as_forecast": false,
  "extracted_probability_ranges": ["60-65%", "75-80%"],
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

### Anti-Confusion Check Design

Instead of a simple numeric comparison, the validator uses 4 signals:

1. **Numeric proximity** — is the forecast within 3% of market price?
2. **Agent estimate keywords** — does reasoning mention "weighted", "consensus", "agent", "converged"?
3. **Range count** — did the LLM extract multiple agent ranges (genuine synthesis) or just one?
4. **Market copy keywords** — does reasoning say "therefore this", "extracting this value", "market price is"?

Decision matrix:
- Market copy keywords without agent keywords → **FAIL** (copied)
- Agent keywords + multiple ranges → **PASS** (coincidence)
- Neither clearly → **PASS but note** (ambiguous)

### Parser Safety Rules

1. Market price references must not be treated as simulation forecasts.
2. Market prices are masked or separately tracked before extraction.
3. Parser output must include `market_price_used_as_forecast`.
4. Ambiguous reports must return `parse_success=false`.
5. Manual probability correction is forbidden.
6. Parser version must be stored for every run.
7. If report contains `parse_success=false`, exclude from calibration scoring — count as parser failure metric.
8. Never invent precision. If report says 60–65%, output midpoint 0.625 and record original range.

### Parser Learning Curve (Phase 0 History)

```
Attempt 1: Basic prompt → LLM returned 0.72 and 0.35 (market prices) for Pectra/XRP
Attempt 2: Hardened prompt with visual separators → same result
Attempt 3: Added pre-processing (market price masking) → same result
Root cause: Reports were saved as full API JSON, not pure markdown. LLM was parsing JSON wrapper.
Attempt 4: Stripped JSON wrapper → Pectra passes (agent-derived 0.72 = coincidence, not copy)
            XRP still fails (LLM reasoning: "提取该值" = copy detected)
Attempt 5: Built context-aware validator → Pectra passes, XRP correctly flagged ambiguous
Final: 5/5 tests green ✅
```

---

## Prophet Postgres Schema

8 tables in `prophet.*` schema.

### Table Overview

| Table | Purpose |
|---|---|
| `events` | One row per tracked market |
| `market_snapshots` | Price/volume at simulation trigger time |
| `seeds` | Source material used for each simulation |
| `simulation_runs` | One row per simulation execution + parsed forecast |
| `stability_diagnostics` | Per-run variance and convergence flags |
| `resolutions` | Ground truth outcomes after market resolution |
| `calibration_results` | Brier scores computed post-resolution |
| `paper_trades` | Phase 2-only — schema exists but not used in Phase 1 |

### Key Schema Rules

- `market_price_used_as_forecast` stored in `simulation_runs` — always populated
- `parser_version` stored in `simulation_runs` — every run, no exceptions
- `parse_success=false` runs are kept in DB, excluded from Brier scoring, included in parser reliability metrics
- `structured_forecast` stored as JSONB in `simulation_runs`
- `raw_report` stored as TEXT in `simulation_runs`
- Market snapshot captured at simulation trigger time, not discovery time

---

## Phase 1 — The Calibration Lab

### Objective

Prove that MiroFish narrative simulation forecasts are better calibrated than market prices on narrative-heavy binary events. This is purely a research/measurement phase. No trading.

### Phase 1 Operating Rules

**Event count:** Start with 10 live events. Do not expand to 20 until the first 10 produce clean data.

**Allowed event categories:**
- `crypto_protocol`
- `crypto_regulatory`
- `company_product`
- `ai_narrative`

**Blocked categories (Phase 1):**
- Sports
- Pure macro
- Elections
- Celebrity/culture markets
- Low-liquidity meme markets

**Simulation config (frozen for first 10 events):**
```
model: deepseek-chat
agents: 13–15
rounds: 5
parser_version: v0.1
seed_builder_version: v0.1
```

Do not tune configuration mid-study. If config changes, version it and treat as a new experiment batch.

**Market filters (Polymarket):**
- Binary YES/NO only
- Volume > $50K
- Probability between 15% and 85%
- 7–60 days to expected resolution
- Prefer crypto/regulatory/company narrative events

---

## Phase 1 Build Order

Build in this exact sequence. Each component depends on the one before it.

### Phase 1A — `logger.py`

Build first. Every downstream component logs through this.

**Required methods:**
```python
create_event(...)
create_market_snapshot(...)
create_seed(...)
create_simulation_run(...)
create_stability_diagnostic(...)
create_resolution(...)
create_calibration_result(...)
log_failed_run(event_id, error, context)
log_failed_parse(simulation_run_id, raw_report, error)
```

**Rule:** No pipeline step produces important data that is not written to Postgres. A failed parse is not an error to hide — it is a real result and must be logged.

### Phase 1B — `mirofish_runner.py`

Wraps the reverse-engineered Flask workflow. Does not parse probabilities — that is the parser's job.

**Required output:**
```json
{
  "project_id": "...",
  "graph_id": "...",
  "simulation_id": "...",
  "report_id": "...",
  "raw_report_markdown": "...",
  "agent_count": 15,
  "round_count": 5,
  "duration_sec": 600,
  "status": "completed"
}
```

**Hard rule:** `mirofish_runner.py` does not parse probabilities. It runs simulations and returns raw reports. Parser remains separate.

### Phase 1C — `market_scanner.py`

**Required output per event:**
```json
{
  "external_market_id": "...",
  "market_title": "...",
  "market_url": "...",
  "category": "crypto_regulatory",
  "price_yes": 0.42,
  "price_no": 0.58,
  "volume_usd": 123456.78,
  "liquidity_usd": 23456.78,
  "expected_resolution_time": "...",
  "resolution_criteria": "..."
}
```

**Hard rule:** Capture market snapshot at simulation trigger time, not discovery time.

### Phase 1D — `seed_builder.py`

**Required output fields:**
- `seed_doc_text`
- `seed_doc_hash`
- `source_urls`
- `source_count`
- `source_time_window`
- `seed_quality` — `high` / `medium` / `low` / `manual`
- `manual_edits` (boolean)
- `seed_builder_version`

**Seed quality labels:**
- `high` — 5+ relevant sources, clear resolution rules
- `medium` — 3–4 sources, mostly clear context
- `low` — fewer than 3 sources or unclear narratives
- `manual` — human-edited seed

**Hard rule:** Manual seed edits are allowed but must be flagged as `manual_edits=true`. Do not present manual input as automated data.

### Phase 1E — `run_calibration.py`

Main orchestrator. Output should be boring and clear.

**Flow:**
```
select event
capture market snapshot
build seed
run MiroFish (mirofish_runner.py)
parse probability (probability_parser.py)
write simulation_run (logger.py)
mark parse success/failure
```

**CLI:**
```bash
python run_calibration.py --event-id <id>
python run_calibration.py --limit 3
python run_calibration.py --dry-run
```

**Console output format:**
```
[1/6] Event selected: "Will XRP ETF be approved by June 30?"
[2/6] Market snapshot saved: price_yes=0.42, volume=$123K
[3/6] Seed saved: quality=high, sources=7
[4/6] Simulation started: project_id=..., ETA ~10 min
[5/6] Report received: 51KB, report_id=...
[6/6] Parser: SUCCESS — forecast_yes=0.58, confidence=0.71
[✓] Simulation run saved: run_id=...
```

### Phase 1F — `resolution_monitor.py`

Daily scheduled job.

**Flow:**
```
find unresolved events
check Polymarket resolution status
if resolved:
  write resolution row
  compute calibration_result for all simulation_runs tied to event
```

**Rule:** Do not delete unresolved events. Keep them pending until explicit resolution confirmation.

### Phase 1G — `forecast_comparison.py`

Computes calibration scores after resolution.

**Metrics computed:**
```python
market_brier_score = (market_price_yes - actual_outcome) ** 2
simulation_brier_score = (forecast_probability_yes - actual_outcome) ** 2
simulation_better_than_market = simulation_brier_score < market_brier_score
market_was_correct = round(market_price_yes) == actual_outcome
simulation_was_correct = round(forecast_probability_yes) == actual_outcome
delta_direction_correct = True if sim and market agree, and outcome confirmed
```

Where `actual_outcome = 1` for YES, `0` for NO.

**Hard rule:** Only compute calibration scores if `parse_success=true`. Failed parses are excluded from forecast scoring but included in parser reliability metrics.

### Phase 1H — `calibration_report.py`

Generates the Phase 1 deliverable: `reports/phase_1_calibration_report.md`

**Required table:**

| Event | Category | Market Prob | Sim Prob | Actual | Market Brier | Sim Brier | Sim Better? | Parse Status | Stability Flags |
|---|---|---:|---:|---|---:|---:|---|---|---|

**Required summary metrics:**
- Total events tracked
- Resolved events
- Successful parses / Failed parses / Parser success rate
- Sim mean Brier score vs Market mean Brier score
- Sim better count vs Market better count
- Directional accuracy
- Ambiguous report count

---

## Gate G2a — Phase 1 Exit Criteria

Gate G2a passes only if:

1. 10 events are logged cleanly in Postgres
2. At least 7/10 parse successfully (`parse_success=true`)
3. No systematic market-price-copy failure detected
4. At least some events have resolved (or Phase 1.5 replay is used)
5. Simulation Brier is directionally better than market Brier on resolved/scored events
6. Stability diagnostics show no major red flags

Perfection is not required. Clean data is required.

---

## Risk Register

| ID | Risk | Likelihood | Impact | Mitigation | Fallback |
|---|---|---|---|---|---|
| R01 | MiroFish API breaks on update | Low | High | Pin Docker image version; version API contract | Re-run Phase 0 tests on new image |
| R02 | DeepSeek API cost exceeds budget | Low | Medium | ~$2.50/sim; 10 events = ~$25 total | Switch to cheaper model for agents; reserve Pro for ReportAgent only |
| R03 | Droplet RAM insufficient at scale | Low | Medium | 2.0GB free confirmed; do not increase agent count | Upgrade droplet only if needed |
| R04 | Polymarket API changes | Medium | Medium | Use Gamma API; monitor changelog | Fall back to manual market selection |
| R05 | Parser fails on new report formats | Medium | High | Version all parser runs; test new formats before use | Flag as `parse_success=false`; improve parser prompt |
| R06 | Events don't resolve during Phase 1 | Medium | Medium | Select 7–60 day events; use Phase 1.5 replay if needed | Extend timeline; don't force scoring |
| R07 | Simulation results are too noisy | Medium | Medium | Freeze config for first 10; track stability diagnostics | Re-run simulations; analyze variance |
| R08 | Zep free tier rate limits | Low | Low | Current usage well within limits | Upgrade Zep tier if needed |
| R09 | CFTC/regulatory risk on trading | Low | High | Phase 1 is research only; no trading | Keep execution layer out until legal review |
| R10 | MiroFish agents homogenize | Low | Medium | OASIS has built-in convergence prevention; diverse personas | Monitor convergence_round in diagnostics |
| R11 | Seed quality too low for coherent simulation | Medium | Medium | Require minimum 3 sources; flag `seed_quality=low` | Reject low-quality seeds; improve seed_builder |
| R12 | Parser contamination from market price references | Medium | Very High | Mask market price references; 5-heuristic anti-confusion check; reject ambiguous reports | Exclude failed parses from calibration; improve parser/versioning |
| R13 | Ambiguous narrative reports reduce usable sample size | Medium | Medium | Track parser success rate; require 7/10 minimum for Gate G2a | Improve ReportAgent prompt or seed format (after Phase 1) |

---

## What Is Not Being Built (Phase 1)

Do not build any of the following until Phase 2 is explicitly approved:

- Dashboard or UI
- Trading execution engine
- Wallet integration
- Order placement code
- Kalshi integration
- Position sizing logic
- Paper trading simulation

Phase 1 is a research instrument. The only output is a calibration report.

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
│   ├── logger.py
│   ├── mirofish_runner.py
│   ├── market_scanner.py
│   ├── seed_builder.py
│   ├── probability_parser.py    ← built, 5/5 tests pass
│   ├── run_calibration.py
│   ├── resolution_monitor.py
│   ├── forecast_comparison.py
│   └── calibration_report.py
├── sql/
│   └── schema.sql               ← migrated, 8 tables
├── tests/
│   └── test_probability_parser.py ← 5/5 passing
└── reports/
    └── phase_1_calibration_report.md
```

---

## Version History

| Version | Date | Changes |
|---|---|---|
| v1.0 | 2026-05-11 | Initial blueprint — complete research synthesis, architecture, roadmap |
| v1.1 | 2026-05-11 | Reframed as calibration lab; narrowed Phase 1 to single category; added stability diagnostics |
| v1.2 | 2026-05-11 | Phase 0 conditional pass; Flask correction; LiteLLM removal; resource profile; parser spec |
| v1.3 | 2026-05-12 | Phase 0 infrastructure verified; parser built and tested; schema migrated; Gate G0 conditional |
| v1.4 | 2026-05-12 | Gate G0 full pass; 5/5 parser tests green; DB write confirmed; Phase 1 approved; build order defined |
