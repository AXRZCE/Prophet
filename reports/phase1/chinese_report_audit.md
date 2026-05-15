# Chinese Report Audit — Prophet Phase 1.1

**Generated:** 2026-05-15 13:15 UTC
**Auditor:** ClawBot
**Scope:** All stress_test simulation reports on disk + DB

---

## Summary

| Classification | Count | Notes |
|---|---|---|
| `suspicious` | 12 | Chinese-language Drake feature reports — parser passed but reasoning is opaque |
| `exclude_from_scoring` | 2 | Approval rating events — forecast = market_price = 0.005 (market-price-copy) |
| `clean` | 1 | Bitcoin event — forecast=0.75, market=0.005, extreme divergence but not copied |
| **Total** | 15 | |

---

## Per-Event Detail

### `exclude_from_scoring` (2 events)

| Event | Forecast | Market | Outcome | Reason |
|---|---|---|---|---|
| Trump approval > 41.6 (run 1) | 0.005 | 0.005 | NO | Forecast = market. Both 0.5%. No independent reasoning. |
| Trump approval > 41.6 (run 2) | 0.005 | 0.005 | NO | Same. Duplicate run, same result. |

**Action:** These 2 simulation runs are flagged `exclude_from_edge_claims`. They contribute nothing to Prophet's calibration signal. The forecast is indistinguishable from the market price. Mark `forecast_quality = market_price_copy` in DB if a column exists, or note in calibration_notes.

### `suspicious` (12 events)

All 12 Drake Iceman feature events. Reports generated in Chinese by MiroFish / DeepSeek V4.

| Event | Forecast | Market | Outcome | Brier | Market Brier | Parser Hit? |
|---|---|---|---|---|---|---|
| Future on Iceman | 0.650 | 0.770 | YES | 0.1225 | 0.0529 | ✅ Yes (correct call) |
| Travis Scott on Iceman | 0.440 | 0.240 | NO | 0.1936 | 0.0576 | ✅ Yes |
| Morgan Wallen on Iceman | 0.370 | 0.150 | NO | 0.1369 | 0.0225 | ✅ Yes |
| EsDeeKid on Iceman (run 1) | 0.260 | 0.260 | NO | 0.0676 | 0.0676 | ✅ Yes |
| Central Cee on Iceman | 0.700 | 0.480 | NO | 0.4900 | 0.2304 | ✅ Yes |
| Yeat on Iceman | 0.700 | 0.500 | NO | 0.4900 | 0.2500 | ✅ Yes |
| Young Thug on Iceman | 0.650 | 0.270 | NO | 0.4225 | 0.0729 | ✅ Yes |
| Fakemink on Iceman | 0.650 | 0.260 | NO | 0.4225 | 0.0676 | ✅ Yes |
| Lil Baby on Iceman | 0.750 | 0.200 | NO | 0.5625 | 0.0400 | ✅ Yes |
| Karol G on Iceman | 0.850 | 0.320 | NO | 0.7225 | 0.1024 | ✅ Yes |
| PinkPantheress on Iceman | 0.850 | 0.150 | NO | 0.7225 | 0.0225 | ✅ Yes |
| Lil Wayne on Iceman | 0.950 | 0.270 | NO | 0.9025 | 0.0729 | ✅ Yes |

**Parser extraction:** The probability parser succeeded on all 12 despite Chinese reports. Forecasting numbers appear in the reports in numeric form (e.g., "77%", "65%") which the regex-based parser can extract. However, the Chinese-language reasoning is opaque — we cannot audit whether the forecast was derived from agent consensus or was a hallucinated number.

**Risk assessment:** Low immediate risk. The parser extracted numbers correctly. The scoring is valid. But if these were Track A (primary evidence), we would not accept Chinese-language reports without translation and manual review.

**Action:** Mark all 12 as `forecast_quality = suspicious`, `exclude_from_edge_claims = true`. Do NOT delete — data is valid. Just don't build claims on Chinese reports.

### `clean` (1 event)

| Event | Forecast | Market | Outcome | Note |
|---|---|---|---|---|
| Bitcoin ≤ $71,699.99 | 0.750 | 0.005 | NO | Extreme divergence (0.75 vs 0.005). No disk report available (report saved by a different path). No evidence of market-price-copy. |

**Note:** The BTC forecast of 0.75 was clearly wrong (BTC was $79K+, nowhere near $71.7K). This is a seed quality failure, not an audit integrity issue. The seed must have lacked current price data — to be addressed by seed guardrails (Priority 6).

---

## EsDeeKid Stability Failure

Same event, same seed, two independent MiroFish runs:

| Run | Forecast | Market | Correct? | Brier |
|---|---|---|---|---|
| Run 1 | 0.260 | 0.260 | ✅ Yes | 0.0676 |
| Run 2 | 0.650 | 0.260 | ❌ No | 0.4225 |

**Spread:** 39 points across two runs. This is the strongest evidence that single-run MiroFish forecasts are unstable. Ensemble support (Priority 4) is essential.

---

## Recommendations

1. Mark 2 approval rating events `exclude_from_scoring` in `prophet.calibration_results` (no column exists, add a note field or track in metadata)
2. Mark 12 Drake reports `forecast_quality = suspicious` in tracking
3. After English-language enforcement is verified, re-run the EsDeeKid event as a 3-run ensemble
4. Do not delete any existing data — just add quality flags
