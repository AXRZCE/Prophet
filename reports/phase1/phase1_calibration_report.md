# Prophet Phase 1 — Calibration Report

**Generated:** 2026-05-15 04:22 UTC

---

## Project Status

**Kalshi discovery solved — MiroFish execution stability fixed.**

| Aspect | Status |
|---|---|
| Kalshi scanner | ✅ Working — series-first weekly market discovery |
| Track A (Polymarket) | ✅ 13 events, 6 simulations — primary evidence |
| Track B (Kalshi retro) | ⚠️ 5 event/resolution shells inserted — 0 simulations (anti-leakage pending) |
| Track C (Kalshi stress) | ⚠️ 5 event shells inserted — 0 simulations (pipeline validation pending) |
| Resolution monitor | ✅ Multi-platform (Polymarket + Kalshi) |
| MiroFish execution | ✅ Fixed — step-level timing + correct report polling |

## Track Summary

| Track | Platform | Events | Completed Sims | Failed Sims | Resolved | Scored | Validity (T/P/F) |
|---|---:|---:|---:|---:|---:|---:|
| Track A — Live Narrative | polymarket | 14 | 10 | 0 | 0 | 0 | 14/0/0 |
| Track B — Retrospective | kalshi | 5 | 0 | 0 | 5 | 0 | 0/4/1 |
| Track C — Stress Test | kalshi | 18 | 16 | 0 | 15 | 16 | 0/13/5 |

## Track A — Live Narrative

*Primary long-term Prophet evidence. Polymarket live narrative events.*

| Metric | Value |
|---|---|
| Events | 14 |
| Platform | polymarket |
| Completed simulations | 10 |
| Failed simulations | 0 |
| Resolved | 0 |
| Scored (calibration) | 0 |
| Validity: true | 14 |
| Validity: partial | 0 |
| Validity: false | 0 |

**Status: Active.** 10 simulation(s) completed.


## Track B — Retrospective

*Historical sanity check. Settled Kalshi markets with known outcomes.*

| Metric | Value |
|---|---|
| Events | 5 |
| Platform | kalshi |
| Completed simulations | 0 |
| Failed simulations | 0 |
| Resolved | 5 |
| Scored (calibration) | 0 |
| Validity: true | 0 |
| Validity: partial | 4 |
| Validity: false | 1 |

**Status: Events inserted, simulations pending.** Track data shells exist but no simulation runs have completed. This track does not yet contribute calibration evidence.


## Track C — Stress Test

*Operational validation. Short-deadline Kalshi weekly markets for pipeline scoring.*

| Metric | Value |
|---|---|
| Events | 18 |
| Platform | kalshi |
| Completed simulations | 16 |
| Failed simulations | 0 |
| Resolved | 15 |
| Scored (calibration) | 16 |
| Validity: true | 0 |
| Validity: partial | 13 |
| Validity: false | 5 |

**Status: Active.** 16 simulation(s) completed.


## ⚠️ Important

**Track B and Track C currently have event shells but no simulation runs.**

- Track B has resolved event shells — outcomes known, anti-leakage seed generation pending.

- Track C has stress-test event shells — weekly Kalshi markets labeled for pipeline validation.

- **Do not claim Track B or Track C is complete until simulations exist.**


## Parser Health

| Track | Total | Success | Failed | Rate |
|---|---:|---:|---:|
| Track A — Live Narrative | 10 | 10 | 0 | 100.0% |
| Track C — Stress Test | 16 | 16 | 0 | 100.0% |

**Cumulative parser success rate: 100.0%** (26/26)

## Pending Resolutions

| Track | Event | Platform | Price | Hypothesis |
|---|---|---:|---:|
| Track A — Live Narrative | Will Apple announce a foldable iPhone in 2026? | polymarket | 0.2800 | true |
| Track A — Live Narrative | Will OpenAI announce earbuds or headphones in 2026 | polymarket | 0.3500 | true |
| Track A — Live Narrative | Will OpenAI announce earbuds or headphones in 2026 | polymarket | 0.5000 | true |
| Track A — Live Narrative | Will Loopscale launch a token by Dec 31 2026? | polymarket | 0.3700 | true |
| Track A — Live Narrative | Will Loopscale launch a token by Dec 31 2026? | polymarket | 0.3700 | true |
| Track A — Live Narrative | Will Loopscale launch a token by December 31, 2026 | polymarket | 0.5000 | true |
| Track A — Live Narrative | Will Loopscale launch a token by December 31, 2026 | polymarket | 0.3700 | true |
| Track A — Live Narrative | Will OpenAI's IPO closing market cap be above $800 | polymarket | 0.7200 | true |
| Track A — Live Narrative | SpaceX market cap $2.0-2.5T at IPO close? | polymarket | 0.2750 | true |
| Track A — Live Narrative | SpaceX market cap $2.0-2.5T at IPO? | polymarket | 0.2750 | true |
| Track A — Live Narrative | Will SpaceX's market cap be between $2.0T and $2.5 | polymarket | 0.2750 | true |
| Track A — Live Narrative | U.S. enacts AI safety bill before 2027? | polymarket | 0.2800 | true |
| Track A — Live Narrative | Debug test 2 | polymarket |  | true |
| Track A — Live Narrative | Debug test | polymarket |  | true |
| Track A — Live Narrative | Debug test | polymarket |  | true |

## Scoring Rules

**Blended Brier scores across tracks are disabled.** Each track tests a different hypothesis:

- Track A: Can MiroFish simulations beat prediction market prices on narrative events?

- Track B: Do historical replays validate the simulation methodology?

- Track C: Does the resolution/scoring pipeline function correctly?


Track C results are used for operational validation only. They test resolution monitoring, Brier scoring, and report generation. They are not primary evidence for Prophet's narrative forecasting edge unless `hypothesis_validity=true`.

## Gate G2a Assessment

- 10 events logged: ✅ (26/10)
- 7/10 parse successfully: ✅ (26/26)
- No systematic market-price-copy failure: ✅
- Events resolved: ✅ (20 resolved)
- Track separation active: ✅ (A/B/C reported separately)
- Multi-platform support: ✅ (Polymarket + Kalshi)
- Track B/C simulations: ⬜ (pending MiroFish execution)
