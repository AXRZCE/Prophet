# PHASE_0_SPEC.md — Prophet Phase 0: Pre-Build Lock Results

**Date:** May 12, 2026  
**Result:** ✅ CONDITIONAL PASS — integration verified, 3/3 tests complete, parser required  
**Test simulations:** 3 complete (Pectra, XRP ETF, Anthropic ARR)

---

## Phase 0 Questions — Answered

| # | Question | Answer | Confidence |
|---|---|---|---|
| 1 | Can MiroFish run on existing ClawBot infra? | ✅ Docker, 1.5GB RAM peak | High |
| 2 | Does MiroFish expose a usable backend API? | ✅ Flask REST on port 5001 | High |
| 3 | Can a seed document be submitted programmatically? | ✅ Yes via file upload + ontology generate | High |
| 4 | Can ReportAgent return structured probability? | ❌ All 3 tests: narrative-only. Parser required. | High |
| 5 | Can results be stored cleanly? | ✅ 3 reports saved, all 29-51KB markdown | High |

---

## Test Results Summary

| # | Test | Category | Agents | Rounds | Report Size | Structured JSON? | Status |
|---|---|---|---|---|---|---|---|
| 1 | Pectra Upgrade | Crypto/Protocol | 13 | 5 | 51KB | ❌ | ✅ |
| 2 | XRP ETF | Crypto/Regulatory | ~15 | 5 | 30KB | ❌ | ✅ |
| 3 | Anthropic ARR | Company/Product | ~15 | 5 | 51KB | ❌ | ✅ |

**Consistent finding across all 3:** ReportAgent produces narrative markdown with:
- Embedded market price references (e.g., "YES price 0.72")
- Agent-sourced probability ranges (e.g., "75-80%", "60-65%")
- Qualitative directional signals
- Raw LLM tool call artifacts at report boundaries

**No native JSON probability block in any report.**

---

## Architecture Discovery

### MiroFish is Flask, not FastAPI (Blueprint Correction)

| Assumed (Blueprint v1.2) | Actual (Phase 0) |
|---|---|
| FastAPI on port 5001 | Flask on port 5001 |
| `/docs` Swagger UI available | No auto-generated docs |
| OpenAPI schema | Must reverse-engineer from source |
| `uvicorn` server | Flask dev server |

### Full API Workflow (Verified x3)

```
POST /api/graph/ontology/generate   → project_id, ontology
POST /api/graph/build               → task_id → [poll] → graph_id
POST /api/simulation/create         → simulation_id
POST /api/simulation/prepare        → task_id → [poll] → ready
POST /api/simulation/start          → [runs agent interactions]
POST /api/report/generate           → task_id → [poll] → report_id
GET  /api/report/<report_id>        → markdown_content
```

### LLM Configuration

Direct DeepSeek API works. LiteLLM proxy NOT running (OpenClaw embedded, not standalone).

```bash
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL_NAME=deepseek-chat
```

### Resource Profile

| Metric | Value |
|---|---|
| MiroFish Docker image | ~14GB (disk) |
| Container RAM idle | ~400MB |
| Container RAM during simulation | ~1.5GB |
| System RAM with MiroFish | 2.0GB free (of 7.8GB) |
| Per-simulation API cost | ~$2.50 |
| Pipeline runtime | ~10 minutes |

Current droplet is sufficient for Phase 1.

---

## ReportAgent Output Format (Critical Finding)

**Format:** Narrative markdown  
**Probability extraction:** Not native — requires parser  
**Parser priority chain (per blueprint):**

1. Modify ReportAgent prompt to force final JSON block (preferred)
2. LLM extractor via second-stage DeepSeek call (primary fallback)
3. Regex extraction (test only)
4. Manual extraction (FORBIDDEN)

---

## Phase 0 Pass/Fail Checklist

- [x] 3 manual simulations complete (Pectra, XRP ETF, Anthropic ARR)
- [x] MiroFish integration method documented (Flask API contract)
- [x] Seed submission method known (file upload → ontology)
- [x] ReportAgent output format known (narrative markdown)
- [x] Probability extraction strategy confirmed (LLM extractor)
- [x] 3 reports saved (29-51KB each)
- [x] RAM usage profiled (~1.5GB peak)
- [x] API cost estimated (~$2.50/sim)
- [ ] Prophet Postgres write tested (pending: parser + schema)
- [ ] Parser built and tested against all 3 reports

---

## Next Steps (Gate G0 Completion)

1. Build `probability_parser.py` — test on all 3 reports
2. Create Prophet Postgres schema
3. Write one parsed test result into Postgres
4. Mark Gate G0 fully passed
5. Begin Phase 1: Calibration Study
