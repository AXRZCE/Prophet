# Prophet — Blueprint

## A Simulation-Calibrated Prediction Market System

> **Phase 1 is not step one of building Prophet. Phase 1 is the experiment that determines whether Prophet should exist at all. This entire document may be worthless. The experiment exists to find out.**
> **Development must not begin until Phase 0 is complete.**
> Phase 0 verifies whether MiroFish can be controlled programmatically, whether ReportAgent can return structured probability output, and whether Prophet can run one complete seed-to-report workflow without manual intervention.

**Author:** ClawBot + Akshar
**Date:** May 12, 2026
**Status:** Pre-Development — Phase 0 Required
**Version:** 1.2
**Phase 0 Spec:** PHASE_0_SPEC.md — required before production development

---

## Table of Contents

1. [Core Assumption & Honest Framing](#core-assumption--honest-framing)
2. [Executive Summary](#executive-summary)
3. [The Three Domains](#the-three-domains)
4. [The Gap](#the-gap)
5. [Why No One Is Building This](#why-no-one-is-building-this)
6. [Prophet Architecture](#prophet-architecture)
7. [First Principles Design](#first-principles-design)
8. [Phase 0: Pre-Build Lock](#phase-0-pre-build-lock)
9. [Phase 1: Calibration Study](#phase-1-calibration-study)
10. [Phase 1.5: Retrospective Sanity Check](#phase-15-retrospective-sanity-check)
11. [Phase 2: Paper Trading](#phase-2-paper-trading)
12. [Phase 3: Live Trading](#phase-3-live-trading)
13. [Phase 4: Productization](#phase-4-productization)
14. [Technical Reference](#technical-reference)
15. [Risk Register](#risk-register)
16. [Appendix A: Research Sources](#appendix-a-research-sources)
17. [Appendix B: Future Modules](#appendix-b-future-modules)
18. [Document History](#document-history)

---

## Core Assumption & Honest Framing

Prophet rests on one hypothesis:

> *A swarm simulation that models how narratives form, spread, and converge through social dynamics can predict event outcomes more accurately than prediction market prices.*

**This hypothesis is unvalidated.** MiroFish has zero published accuracy benchmarks on resolved real-world prediction events. The academic swarm intelligence studies that suggest promise use **human swarms**, not LLM agent swarms. LLM agents have known pathologies: they're trained on the same data, they don't have real money at stake, their "beliefs" are next-token distributions not probability estimates, and they're susceptible to prompt-induced consensus. A swarm of 500 LLM agents may simply be 500 copies of the same training data bias.

**Prophet is not a product plan. It is a structured experiment — a calibration lab — to test whether this hypothesis holds.** The lab has no trading PnL target, no product roadmap, and no founder narrative. It has one job: compare market probability, simulation probability, and actual outcome, repeatedly, until the data says something clear.

Phase 1 costs ~$50 and 2-4 weeks. It answers a single falsifiable question: **"For a narrow category of narrative-rich events, does simulation Brier score beat market Brier score?"** — starting with 10 events in one category before expanding to 20, and only in one category (crypto/regulatory/company narrative events) rather than mixed domains.

| Outcome | What It Means | What We Do |
|---|---|---|
| Sim beats market clearly (10+ events) | Hypothesis has legs in this category | Expand to 20, then Phase 2 |
| Ambiguous (no clear signal) | Might be noise — check stability diagnostics (see § Simulation Stability Diagnostics) | Follow the framework |
| Market beats sim clearly | Hypothesis likely wrong for current config | Major iteration or abandon |

If Phase 1 fails, the document beyond the Phase 1 section is irrelevant. If Phase 1 succeeds, we have the most important thing: **data, not arguments.**

**False-confidence detection is not optional.** LLM agents may produce persuasive reports with weak accuracy, cluster near 50%, or converge too fast to informative disagreement. Phase 1 explicitly tracks these failure modes separately from the core hypothesis test (see § Simulation Stability Diagnostics). A simulation that "sounds right" but systematically misfires is worse than one that predicts poorly — it builds false confidence that degrades every downstream decision.

### Phase 1 Trading Lock

Phase 1 must not include:

- wallet private keys
- Polymarket trading API keys
- Kalshi trading API keys
- order placement code
- live execution paths
- automated buy/sell actions
- position sizing connected to real capital

Phase 1 is a calibration study only. The system may read market data, store prices, run simulations, and compute accuracy metrics. It must not trade.

Execution code is forbidden until Gate G2b is passed.

---

## Executive Summary

**Prophet** is a calibration laboratory that sits between three domains: **swarm intelligence simulation** (MiroFish/OASIS — thousands of AI agents modeling narrative formation), **prediction markets** (Polymarket/Kalshi — crowd beliefs aggregated into prices), and **actual resolved outcomes** (the ground truth). Its job is not to trade. Its job is to measure whether simulation-based forecasts are better calibrated than market prices for narrative-rich events.

The core bet: *A swarm simulation that models how narratives form, spread, and converge through social dynamics can predict event outcomes more accurately than prediction market prices — especially for narrative-rich, multi-stakeholder events where the crowd systematically underweights second-order effects.*

**Prophet is not a trading system. It is a calibration engine.** Trading is a downstream application — one that only becomes relevant if calibration survives Phase 1-3 with evidence. Decision intelligence for narrative-heavy events (product launches, policy shifts, protocol upgrades) is an equally viable end state and may arrive first.

If the calibration hypothesis holds, Prophet generates compounding alpha across prediction markets, forecasting dashboards, and scenario analysis tools. If false, the experiment generates a unique dataset (simulation vs market vs reality across many event types) that no one else has.

**No one is building this.** The skill stack (multi-agent simulation + prediction market mechanics + crypto infrastructure + production backend) doesn't exist in any single team, and the incentive structures of every relevant actor push away from this exact integration.

---

## The Three Domains

### Domain 1: Prediction Markets (2026 State of Play)

**Scale:** $20B+/month in global volume. Up from $73M (Polymarket, 2023). A legitimate financial primitive - the Federal Reserve cites Kalshi as a superior macro expectations benchmark.

**The Duopoly:**

| | Kalshi | Polymarket |
|---|---|---|
| **Market Share** | 52.6% (US) | 30-35% (global) |
| **Regulation** | CFTC-regulated DCM (fiat USD) | Crypto-native (USDC on Polygon) |
| **Access** | US-only | Global (geo-blocked in US) |
| **Fees** | 1-2% per contract | 0-1.5% (often fee-free) |
| **Markets** | Politics, Fed rates, sports (18 states), crypto | Politics, culture, crypto, macro, everything |
| **APIs** | REST + WebSocket + Python SDK | Gamma (discovery) + CLOB (trading) + Data (analytics) |
| **Backing** | Institutional | ICE invested $2B at $9B valuation |
| **Tech** | Standard CLOB | 45ms latency, 3,200 orders/sec, smart contract settlement |

**API Access (Polymarket):**

Polymarket's API landscape is mature and bot-friendly:

| API | Base URL | Use Case | Auth |
|---|---|---|---|
| Gamma API | `https://gamma-api.polymarket.com` | Markets, events, search, tags | None |
| Data API | `https://data-api.polymarket.com` | Positions, trades, OI, leaderboards | User address |
| CLOB API | `https://clob.polymarket.com` | Orderbook, trading, pricing | API keys |
| Bridge API | `https://bridge.polymarket.com` | Deposits/withdrawals | Yes |

**Rate Limits (generous for bots):**
- Authenticated: 20 req/sec per API key
- Public market data: 300-500 req/10s per endpoint
- Order placement: 50 req/sec burst, 5 req/sec sustained
- WebSocket: unlimited for live data
- Partner tier: highest limits, gasless trading

**Key Public Endpoints (No Auth Required):**
```
GET /markets?active=true&limit=50           # Discover active markets
GET /events?category=election               # Filter by category
GET /markets/{marketId}                     # Get tokenIDs for trading
GET /midpoints?token_id={tokenID}           # Current mid-market price
GET /prices-history?market={id}&interval=1d  # Historical prices
```

**Regulatory Landscape (2026):**

The CFTC has shifted from restrictive to permissive:
- **Feb 6, 2026:** Withdrew 2024 proposed rules that would have banned "gaming" contracts
- **Mar 11-12, 2026:** Opened ANPRM for public comment - signaling "responsible innovation"
- **Mar 31, 2026:** Enforcement priorities focused on insider trading, not market bans
- Chairman Selig frames it as innovation with safeguards under exclusive CFTC authority

This is the friendliest regulatory window prediction markets have ever had.

**Documented Market Weaknesses (What Prophet Exploits):**

| Weakness | Description | Exploitation Strategy |
|---|---|---|
| **Favorite-Longshot Bias** | Markets overprice unlikely outcomes (e.g., 10% when true probability is 3%) | Simulation can calibrate true probabilities for long-tail events |
| **Liquidity-Driven Distortion** | Large "whale" trades swing prices beyond informational value | Simulation provides independent probability that ignores whale noise |
| **Herd Behavior** | Information cascades where traders follow others rather than fundamentals | Agent swarm explicitly models herding dynamics as they form |
| **Poor Calibration on Niche Events** | Brier scores falter in low-volume/ambiguous markets | Simulation generates independent analysis where crowd is thin |
| **Narrative Blind Spots** | Markets price events but don't model second-order narrative effects | This is Prophet's core edge - modeling what the crowd hasn't processed yet |
| **Retail Dominance** | 90% of sports volume is retail gambling, embedding systematic biases | Simulation models institutional-quality analysis, not retail emotion |

---

### Domain 2: MiroFish - Swarm Intelligence Simulation

**What it is:** An open-source engine that spawns thousands of LLM-powered AI agents (up to 1 million) with unique personalities, memories, and behavioral logic. Agents interact in simulated Twitter and Reddit environments. Emergent social dynamics produce structured prediction reports.

**Backstory:** Built in approximately 10 days by a 20-year-old Chinese student. Received strategic support and incubation from Shanda Group. Open-sourced on GitHub (666ghj/MiroFish). Raised $4.1M in funding. Trending #1 on GitHub in March 2026.

**Core Workflow:**

```
Step 1: Ontology Generation
    Raw reports/notes/fiction → structured entities, motives, factual anchors

Step 2: Graph Construction
    Neo4j-powered knowledge graph exposing actors, tensions, memory structure

Step 3: Parallel Simulation
    Platform-native agents interact across Twitter + Reddit style channels
    Multiple rounds of posting, commenting, debating, reposting, following

Step 4: Report Generation
    ReportAgent condenses trajectory into readable prediction report
    Key turning points, risks, confidence signals, dominant narratives

Step 5: Deep Interaction
    Interrogate the simulated world through ReportAgent
    Interview individual agents about their beliefs and reasoning
```

**Technical Architecture:**

| Component | Technology | Role |
|---|---|---|
| **Simulation Engine** | CAMEL-AI OASIS | Multi-agent orchestration, up to 1M concurrent agents |
| **Agent Reasoning** | LLM (OpenAI-compatible API) | Each agent uses LLM for social decision-making |
| **Memory** | Zep Cloud + Neo4j | Long-term agent memory, relationship graphs |
| **Knowledge Graph** | GraphRAG | Seed document → entity extraction → relationship mapping |
| **Frontend** | React (port 3000) | Upload seeds, configure agents, launch sims, view reports |
| **Backend** | Python/FastAPI (port 5001) | Orchestration, LLM calls, simulation management |
| **Social Actions** | 23 action types | Post, comment, repost, follow, like, debate, search, trend, mute |

**Agent Capabilities:**
- 23 social actions: CREATE_POST, CREATE_COMMENT, LIKE_POST, DISLIKE_POST, REPOST, FOLLOW, MUTE, SEARCH_POSTS, SEARCH_USER, TREND, REFRESH, DO_NOTHING
- Stateful memory of interactions and preferences
- LLM-driven natural language reasoning (not rigid if-then rules)
- Unique personas generated from seed material via GraphRAG
- 24-hour activity schedules via Time Engine
- Event-driven environment to prevent conversational loops and state degradation

**Deployment Options:**

| Aspect | Cloud | Local/Docker |
|---|---|---|
| Scale | 1M+ agents | 50-500 agents (hardware-limited) |
| Cost | Per-call API pricing | Fixed infra cost |
| Memory | Zep Cloud | Neo4j (offline replacement) |
| LLM | Any OpenAI-compatible API | Any OpenAI-compatible API |
| Fidelity | High (parallel inference) | Lower (sequential/batched) |

**Relevant Use Cases (from MiroFish's built-in scenarios):**
- **Public Opinion Forecast:** How incidents/controversies evolve across platforms
- **Launch Stress Test:** How customers, competitors, commentators react to product launches
- **Policy Reaction:** How institutions and stakeholder groups interpret policy drafts
- **Finance Case:** How management, analysts, and retail narratives react to the same financial signal
- **Narrative Continuation:** How fictional worlds evolve after new events

**LLM Integration:** Supports any OpenAI SDK-format API. Defaults to Alibaba Qwen-Plus. Compatible with DeepSeek Flash/Pro via LiteLLM. This makes simulation costs manageable - Flash is approximately 12x cheaper than Pro.

---

### Domain 3: AI Agents & DeFAI (2026)

**The Agent Takeover of DeFi:**
- Single AI agent on Solana already manages more daily transaction volume than the bottom 20% of human retail traders combined
- AI agents projected to execute >80% of DeFi transactions by 2030
- >80% of DeFi TVL expected to be managed/optimized by agentic AI by decade's end
- "Agent-as-a-Service" models now charge based on data consumption (tokens) rather than hourly fees

**DeFAI Ecosystem:**
- Virtuals Protocol & Bittensor democratizing agent deployment
- Users can deploy financial bots in minutes
- Investors can buy "agent shares" - own pieces of AI revenue streams
- Specialist bots outpacing generalists in specific niches

**Agent Identity & Payments:**
- KYA (Know Your Agent) replacing KYC - cryptographic signatures establish trustworthy AI identities
- x402 standard enabling high-frequency microtransactions between agents
- Projected 30% of Base daily transactions and 5% of Solana non-vote transactions in 2026

**Emerging Risk - Algorithmic Resonance:**
- Most top-tier agents trained on identical datasets (Binance, Etherscan, Bloomberg)
- Feedback loops where thousands of agents execute simultaneous sell orders
- A new systemic risk category created by agent homogeneity

---

## The Gap

### The Categorical Void

There are four approaches to prediction in 2026. One quadrant is empty:

```
                    │  Has Narrative Model  │  No Narrative Model
────────────────────┼───────────────────────┼──────────────────────
Connected to        │                       │
Real Markets        │     ★ PROPHET ★       │   Trading Bots
                    │     (this project)    │   DeFAI Agents
────────────────────┼───────────────────────┼──────────────────────
NOT Connected to    │                       │
Real Markets        │   MiroFish / OASIS    │   Academic ABM
                    │                       │   Statistical Models
```

### What Each Approach Does - and Doesn't Do

**Approach 1: Pure Statistical Forecasting**
- FutureSearch, Good Judgment Project, Metaculus, Manifold
- `News → Statistical Model → Probability → Compare to market → Trade if edge > X%`
- **Does:** Takes inputs, runs math, outputs a number
- **Doesn't:** Model the *process* of belief formation. No simulation of how narratives spread through Twitter, how demographics react differently, how polarization changes probability distributions

**Approach 2: Academic Agent-Based Modeling**
- Simudyne Pulse, university research labs, 2026 Taylor & Francis paper on manipulation
- `Define agent rules → Run simulation → Observe emergent patterns → Publish paper`
- **Does:** Models market dynamics with heterogeneous agents to understand herding, manipulation, price discovery
- **Doesn't:** Connect to real markets, put real capital at risk, or generate actionable trading signals. Descriptive, not operational. Predefined rules, not LLM-driven reasoning. No feedback loop from real outcomes.

**Approach 3: Trading Bots**
- PolyStrat, BulkQuant, 3Commas, custom Polymarket scripts
- `Market Data → Signal Generation → Position Sizing → Trade Execution`
- **Does:** React to price movements, volume changes, order book imbalances. Process 100x more data than humans.
- **Doesn't:** Model narratives. No understanding of WHY prices move. Can't simulate counterfactuals. Purely reactive - responds to what IS, not what WILL BE.

**Approach 4: DeFAI / Autonomous Agents**
- Virtuals Protocol, Bittensor, ElizaOS, OpenClaw-based agents
- `Agent perceives environment → Reasons about state → Decides action → Executes on-chain`
- **Does:** Operate autonomously across DeFi protocols, manage positions, optimize yield
- **Doesn't:** Simulate social dynamics or narrative formation. Trained on on-chain data, price feeds, protocol states. Execution engines, not simulation engines. No world model.

**Prophet lives in the empty quadrant:**
- Has a narrative model (MiroFish/OASIS agent swarms)
- Connected to real markets (Polymarket/Kalshi APIs)
- Closed-loop learning (simulation vs reality feedback)
- Generates forward-looking forecasts from first-principles simulation, not reactive signal processing

### The Fundamental Insight

Prediction market prices encode *what the crowd believes will happen*. MiroFish simulations encode *how the crowd will form and evolve their beliefs*.

A price tells you "65% chance." A simulation tells you "the market says 65%, but our agents show that when the policy details leak Wednesday, retail will overreact, institutions will counter-trade Thursday, and consensus will converge to 82% by Friday."

The edge is understanding the *trajectory* of belief formation, not just the endpoint. This is what no existing approach does.

---

## Why No One Is Building This

### 1. The Skill Stack Doesn't Exist in One Person or Team

| Required Skill | Typical Background | Overlap |
|---|---|---|
| Multi-agent LLM simulation (OASIS, agent swarms) | AI research, PhD-level multi-agent systems | Rare |
| Prediction market mechanics (CLOB, binary options pricing) | Quant finance, derivatives trading | Rare |
| Crypto infrastructure (Polygon, smart contracts, USDC) | Web3/smart contract engineering | Moderate |
| Production backend (APIs, workers, databases) | Backend/systems engineering | Common |
| Narrative analysis / social dynamics modeling | Social science, political science | Uncommon |

Very few individuals have even 3 of these. Almost no teams have all 5. The communities barely overlap.

### 2. The Incentive Structures Push Away From Integration

**MiroFish / Shanda Group:** Their incentive is platform adoption - more users uploading docs, more simulations run. Building a proprietary trading system doesn't grow their user base. It would be a conflict (using their engine to extract value from markets, rather than selling the engine).

**CAMEL-AI / OASIS:** Academic consortium. Incentives: citations, papers, community contributions. A trading system is outside their scope and doesn't advance their research agenda. No academic reward for building a prediction market bot.

**Polymarket / Kalshi:** Their incentive is volume and liquidity. They want MORE traders, not smarter ones. A tool that helps specific traders systematically beat the market potentially triggers adverse selection - retail realizes they're the dumb money and leaves. Platforms have a structural incentive to keep the playing field level enough that retail participation doesn't collapse.

**Quant funds / professional traders:** If they build anything like this, they keep it proprietary. The few people capable of building this have the strongest incentive to hide it. The absence of public evidence isn't evidence of absence - it's evidence of secrecy.

**Open-source AI community:** Building this requires domain knowledge in binary options pricing, order book mechanics, USDC settlement, CFTC regulation, and event contract resolution - none of which are in the typical open-source AI dev's toolkit. And the payoff is niche alpha, not GitHub stars or academic citations or conference talks. Way more grinding for way less prestige.

**Retail / indie builders:** The people who DO build prediction market bots are crypto-native degens optimizing for speed and arbitrage. Their mental model is "read prices, find edge, trade." The conceptual leap to "simulate social dynamics, compare to prices, THEN trade" is a paradigm shift most traders never make. Conversely, the people who understand simulation (AI researchers) typically don't trade prediction markets at all.

### 3. The Time Horizon Mismatch

| What Needs to Happen | Time Required | Who Can't Afford This |
|---|---|---|
| Build simulation pipeline | 2-4 weeks | - (anyone can) |
| Run simulations on real events | Ongoing | - |
| **Wait for events to resolve** | **Days to months** | Startups (18-month VC cycles), academics (conference deadlines) |
| Compare simulation vs reality | Ongoing accumulation | Anyone needing a paper/demo/raise in <6 months |
| Tune parameters from calibration data | Months to years | Anyone optimizing for quarterly results |
| Compound the learning loop | Years | Almost everyone |

The payoff curve is back-loaded. Year 1: generating calibration data, eating losses. Year 2: system starts outperforming. Year 3-5: data moat is deep enough that new entrants can't replicate. This is a power-law compounding curve that looks flat for the first 12-18 months. No VC-funded startup can sell that to a board. No academic can publish that before tenure. No indie hacker can survive that long without revenue.

### 4. The "MiroFish is Brand New" Factor

MiroFish's GitHub was created in April 2026 - barely a month old. The community is still figuring out basic reliability, debating deployment tradeoffs, sharing prompt recipes. Financial use cases are experimental GitHub issues, not production systems. The window is open *right now*. In 6-12 months, someone will have productionized this - either a startup, a hedge fund, or a well-funded solo builder.

### 5. The Cold Start Bootstrap Problem

```
To know if simulations beat markets → you need calibration data
To get calibration data → you need to run simulations on real events
To run meaningful simulations → you need a tuned simulation pipeline
To tune the pipeline → you need calibration data
```

Someone must bootstrap this cold. That means running early simulations knowing they'll be inaccurate, eating API costs with no immediate return, recording everything systematically even when the signal looks noisy, and trusting the learning curve exists before you can see it. Most builders hit this loop, see early noise, conclude "it doesn't work," and leave. They never discover whether the noise was the bootstrapping phase or the steady state. The difference between "it doesn't work" and "it doesn't work YET" is months of systematic logging - and almost nobody bridges that gap.

### 6. The Gambling Stigma

Despite being cited by the Federal Reserve, regulated by the CFTC, backed by ICE at $9B, and doing $20B+/month in volume - prediction markets carry a gambling stigma. Serious AI/ML engineers associate them with crypto degens and political betting, not legitimate information aggregation. The people with the technical skills to build this are often the most reputation-conscious. This creates a talent vacuum at the exact intersection where the most interesting work is possible.

### Summary: The Structural Void

| Barrier | Who it Filters Out |
|---|---|
| Skill stack too broad | 99% of individual builders |
| Incentives push toward other things | Platforms, academics, quants, open-source devs |
| Time horizon too long (12-36 months) | VC startups, academic labs, indie hackers |
| Tool is brand new (<2 months old) | Hasn't had time for financial integrations |
| Cold start requires faith | Anyone optimizing for short-term signal |
| Gambling stigma | Reputation-conscious AI/ML engineers |

These barriers compound, not add. The set of people who can overcome ALL of them simultaneously is vanishingly small.

---

## Prophet Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          PROPHET SYSTEM                              │
│                                                                      │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐   │
│  │ NARRATIVE       │   │ MARKET LENS     │   │ FORECAST        │   │
│  │ ENGINE          │──▶│                 │──▶│ COMPARISON      │   │
│  │                 │   │                 │   │ ENGINE           │   │
│  │ MiroFish/OASIS  │   │ Polymarket APIs │   │ sim probability  │   │
│  │ agent swarm     │   │ + Kalshi APIs   │   │ vs              │   │
│  │ simulation      │   │                 │   │ market price    │   │
│  │                 │   │ market prices   │   │                 │   │
│  │ seed → report   │   │ order books     │   │ conviction      │   │
│  │ → probability   │   │ historical data │   │ score           │   │
│  └─────────────────┘   └─────────────────┘   └───────┬─────────┘   │
│                                                       │             │
│                       ┌───────────────────────────────┘             │
│                       ▼                                              │
│  ┌─────────────────┐   ┌─────────────────────────┐   ┌────────────┐ │
│  │ TRADING MODULE  │   │ RESOLUTION +            │   │ CALIBRATION│ │
│  │ [FUTURE - Ph 3] │──▶│ CALIBRATION ENGINE      │   │ DASHBOARD  │ │
│  │                 │   │                         │   │            │ │
│  │ (Not in Ph 1/2) │   │ sim vs actual resolution│   │ active sims│ │
│  │                 │   │                         │   │ calibration│ │
│  │                 │   │ Brier scores            │   │ metrics    │ │
│  │                 │   │ → calibrate everything  │   │ divergence │ │
│  └─────────────────┘   └─────────────────────────┘   └────────────┘ │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    DATA LAYER (Postgres + Redis + Qdrant)    │    │
│  │  events | snapshots | seeds | simulations | resolutions     │    │
│  │  diagnostics | calibration | [paper_trades - Phase 2+]      │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### Layer Activation by Phase

| Layer | Phase 0 | Phase 1 | Phase 1.5 | Phase 2 | Phase 3 |
|---|---:|---:|---:|---:|---:|
| Market Scanner | ❌ | ✅ | ✅ | ✅ | ✅ |
| Seed Builder | ⚠️ Manual test | ✅ | ✅ | ✅ | ✅ |
| Narrative Engine | ✅ Test only | ✅ | ✅ | ✅ | ✅ |
| Probability Parser | ✅ Test only | ✅ | ✅ | ✅ | ✅ |
| Forecast Comparison Engine | ❌ | ✅ Logging only | ✅ | ✅ Active | ✅ Active |
| Resolution Monitor | ❌ | ✅ | ✅ | ✅ | ✅ |
| Calibration Engine | ❌ | ✅ | ✅ | ✅ | ✅ |
| Paper Trading Engine | ❌ | ❌ | ❌ | ✅ | ✅ |
| Live Trading Module | ❌ | ❌ | ❌ | ❌ | ✅ |
| Calibration Dashboard | ❌ | Minimal report only | Minimal report only | Minimal | Full |

✅ Phase 1 Active: market data, seed construction, simulation, probability parsing, forecast comparison, resolution tracking, calibration reporting.

🔒 Phase 1 Locked: trading module, wallet integration, order placement, live execution, PnL dashboard.

### Layer 1: Narrative Engine (MiroFish / OASIS)

**Purpose:** Transform real-world event seeds into structured probability estimates through multi-agent social simulation.

**Inputs:**
- Seed document (news article, policy draft, earnings report, event description)
- Simulation parameters (agent count, rounds, platforms, prompt recipe)
- Historical calibration data for this event type (from Calibration Engine)

**Process:**
1. GraphRAG extracts entities, relationships, tensions from seed document
2. Agent personas generated with diverse demographics, biases, knowledge levels
3. Dual-platform simulation (Twitter + Reddit style) over multiple interaction rounds
4. Agents post, comment, debate, repost, form coalitions, evolve opinions
5. ReportAgent synthesizes emergent dynamics into structured forecast

**Outputs:**
- Predicted probability of event outcome (e.g., "72% YES")
- Confidence score (0-1, based on agent consensus strength)
- Key narrative turning points and risk scenarios
- Dominant actors and their influence trajectories
- Agent debate log (optional, for deep analysis)

**Integration:**
- MiroFish running as Docker container or local process
- LLM API pointed at LiteLLM → DeepSeek Flash (agent reasoning) + Pro (ReportAgent synthesis)
- Neo4j or Zep Cloud for agent memory
- Simulation triggered via Python subprocess or REST API call

**Cost Estimate:** $2-5 per full simulation (Flash for agents, Pro for report). For 10-event checkpoint: $20-50. For full 20-event calibration study: $40-100 total API cost.

#### ReportAgent Structured Output Contract

Every simulation report must end with a strict JSON block:

```json
{
  "forecast_probability_yes": 0.64,
  "forecast_confidence": 0.58,
  "forecast_direction": "YES",
  "main_reason": "Short explanation of the dominant causal logic.",
  "key_uncertainties": [
    "Uncertainty 1",
    "Uncertainty 2"
  ],
  "agent_disagreement_summary": "Summary of where agents disagreed.",
  "dominant_narrative": "The main narrative that emerged.",
  "contrarian_narrative": "The strongest opposing narrative.",
  "probability_rationale": "Why this probability was chosen instead of market price."
}
```

Rules:
- `forecast_probability_yes` must be a decimal between `0.00` and `1.00`.
- `forecast_confidence` is logged but excluded from decisions until validated.
- JSON must be machine-parseable.
- If JSON parsing fails, the simulation run is marked `failed_parse`.
- No manual probability correction is allowed.

#### Probability Parser Fallback

If MiroFish cannot force structured JSON output, Prophet uses a second-stage probability parser.

Allowed parse methods:

| Method | Priority | Notes |
|---|---:|---|
| Native ReportAgent JSON | 1 | Preferred |
| Regex extraction | 2 | Only if output format is stable |
| LLM extractor | 3 | Acceptable but must be versioned |
| Manual extraction | Forbidden | Would contaminate calibration data |

The parser must return:

```json
{
  "forecast_probability_yes": 0.64,
  "forecast_confidence": 0.58,
  "parse_method": "llm_extractor",
  "parse_success": true
}
```

### Layer 2: Market Lens (Polymarket + Kalshi APIs)

**Purpose:** Provide real-time and historical market data for comparison against simulation outputs.

**Data Sources:**

| Source | Endpoint | Data |
|---|---|---|
| Gamma API | `/markets?active=true` | Active markets, categories, volumes |
| Gamma API | `/markets/{id}` | Market details, outcomes, tokenIDs |
| CLOB API | `/midpoints?token_id={id}` | Current mid-market price |
| CLOB API | `/prices-history?market={id}` | Historical price time series |
| Data API | `/trades?market={id}` | Recent trades, volume |
| Kalshi API | `/markets?status=open` | US-regulated event contracts |
| Kalshi WebSocket | `/ws` | Real-time price updates |

**Normalization:**
- Binary YES/NO prices normalized to 0-1 probability
- Multi-outcome markets: probabilities extracted from winning token price
- Kalshi: yes_ask / (yes_ask + no_ask) for midpoint probability
- Polymarket: token price in USDC cents / 100

**Historical Data:**
- Price history at simulation time (for accurate comparison)
- Resolution data (outcome, resolution time, disputes if any)
- Volume and liquidity at simulation time

### Layer 3: Forecast Comparison Engine

**Purpose:** Compare simulation probability against market probability, compute conviction score.

**Core Calculation:**

```
raw_delta = sim_probability - market_probability

# Phase 1-2: sim_confidence is EXCLUDED from the formula.
# It gets its own tracking column but does not affect decisions.
# It is a logged curiosity, not a signal — until Phase 1 data validates it.
conviction = raw_delta × liquidity_factor × calibration_factor

WHERE:
  liquidity_factor: min(1.0, market_volume / min_volume_threshold)
  calibration_factor: historical_brier_ratio for this event_type
    (calibration_factor > 1.0 if sim historically beats market on this type)

  # Phase 3+: sim_confidence is added as a multiplier ONLY IF
  # Phase 1 data shows Pearson correlation between
  # sim_confidence and sim_accuracy > 0.3.
  # LLM self-reported confidence is systematically miscalibrated.
  # Agent convergence may reflect prompt homogenization, not genuine consensus.
  # Until proven otherwise, it is noise.
```

**Thresholds (initial, to be calibrated in Phase 2):**

| Conviction | Action |
|---|---|
| < 0.05 | No action - signal too weak |
| 0.05 - 0.10 | Log as "observation" - track for calibration |
| 0.10 - 0.15 | Consider paper trade |
| > 0.15 | Trade signal (paper or live, depending on phase) |

### Layer 4: Trading Module [FUTURE — Phase 3 Only]

See [Appendix B: Future Modules](#appendix-b-future-modules). No code for this module should exist in the codebase until Gate G2b is passed.

Phase 1-2 uses only paper positions logged in `prophet.paper_trades`. No order placement, no wallet keys, no live execution.

### Layer 5: Resolution + Calibration Engine

**Purpose:** Transform every resolved event into calibration data that improves future simulations.

**Data Collected Per Event:**

```
simulation_id
├── sim_probability: 0.72
├── sim_confidence: 0.68
├── market_probability_at_sim: 0.58
├── market_probability_at_resolution: 1.0 (if YES)
├── actual_outcome: YES
├── event_type: crypto_protocol
├── event_subtype: blockchain_upgrade
├── days_to_resolution: 14
├── simulation_params: {agents: 500, rounds: 10, model: flash}
├── seed_doc_hash: abc123
├── resolution_notes: "no disputes, clear outcome"
│
├── sim_was_correct: True
├── market_was_correct: True
├── sim_brier_score: 0.0784   # (0.72 - 1.0)^2 = 0.0784
├── market_brier_score: 0.1764 # (0.58 - 1.0)^2 = 0.1764
├── sim_better_than_market: True
└── delta_direction_correct: True  # sim said higher probability than market, and YES happened
```

**Calibration Outputs:**

| Metric | Computation | Used For |
|---|---|---|
| Calibration curve per event type | Brier scores grouped by event_type | Adjusting conviction multiplier |
| Directional accuracy | % of times sim pointed in right direction vs market | Filtering which events to trade |
| Confidence calibration | Does 0.8 confidence actually mean 80% accuracy? | Adjusting sim_confidence weight |
| Time decay | Does accuracy change by days_to_resolution? | Timing entry/exit |

**Feedback Mechanism:**
- Every resolved event updates calibration curves
- Forecast Comparison Engine parameters auto-tune based on rolling 20-event window
- Simulation prompt recipes updated when specific event types underperform
- Agent count/rounds adjusted based on cost-benefit per event type

### Layer 6: Calibration Dashboard

**Purpose:** Visualize calibration metrics — simulations, markets, forecast comparisons.

#### Dashboard Deferral Rule

No full dashboard is built until Prophet has generated a complete 10-event calibration report. Before that point, outputs are limited to:

- CLI logs
- database rows
- Markdown reports
- CSV exports

A dashboard can make the project feel mature before the data is mature. UI work is deferred until the calibration pipeline works.

**Views (all Phase 3+ unless noted):**

| View | Content | Active By |
|---|---|---|
| **Active Simulations** | Running sims, progress, preliminary probabilities | Phase 1 |
| **Market Monitor** | Tracked events, market prices, simulation estimates, delta | Phase 1 |
| **Calibration** | Brier scores by event type, directional accuracy over time, confidence calibration plots | Phase 1 |
| **Event Explorer** | Browse active Polymarket events, filter by category/volume, trigger simulation | Phase 1 |
| **Future Position View** | Current holdings, entry price, PnL | Phase 3+ |
| **Future PnL Tracker** | Cumulative PnL, win rate, Sharpe ratio, max drawdown | Phase 3+ |

---

## First Principles Design

### Core Design Principles

**1. The Data Decides Everything**

No human judgment gates any decision. Every gate is numeric:
- "Is the simulation working?" → Brier score vs market Brier score
- "Should we trade this?" → conviction > threshold AND historical calibration > 1.0
- "Should we exit this position?" → conviction drop > 50% OR event resolved
- "Should we scale up?" → rolling 50-event Sharpe > 1.0

**2. Start With Simulation → Reality → Feedback, Not Trading**

Phase 1 runs zero capital. It's pure observation: "does simulation beat the market?" Trading comes only after that question is answered with data.

**3. Compound the Calibration Data**

Every simulation, every resolution, every trade is logged. This dataset is the moat. A new entrant can't fake 500 events of calibration history. The data compounds even when PnL doesn't.

**4. Simple Components, Clear Interfaces**

Each layer is independently testable:
- Narrative Engine: `input(seed_doc) → output(probability, confidence, report)`
- Market Lens: `input(event_id) → output(price, volume, history)`
- Forecast Comparison Engine: `input(sim_prob, market_prob, metadata) → output(conviction)`
- Trading Module: `input(conviction, event_id, market) → output(position_id)` [Phase 3+]
- Resolution + Calibration Engine: `input(resolution_data) → output(updated_calibration_curves)`

**5. Cheap Models for Agents, Expensive for Synthesis**

Agent reasoning (hundreds of agents × multiple rounds) uses DeepSeek Flash. ReportAgent synthesis (single call per simulation) uses DeepSeek Pro. This keeps costs at ~$2-5 per simulation vs $50-200 if all agents used Pro.

**6. Polymarket First, Kalshi Later**

Polymarket requires no KYC, no geographic restriction (for non-US), public APIs with no auth for market data. It's the path of least resistance. Kalshi adds regulatory complexity that Phase 1 doesn't need.

**7. Favor Asynchronous Over Real-Time**

MiroFish simulations take minutes to hours, not milliseconds. This is correct - the edge is narrative depth, not speed. Events resolve in days to weeks. Batch simulations overnight. Compare to market prices the next morning.

### Reproducibility Requirements

Every simulation run must store:

- seed document hash
- source URLs
- market snapshot timestamp
- model name for agents
- model name for report synthesis
- model provider
- temperature
- max tokens, if available
- agent count
- round count
- random seed
- prompt template version
- agent persona version
- ReportAgent prompt version
- parser version
- MiroFish commit hash or version
- Prophet pipeline commit hash

A simulation result that cannot be reproduced is not valid calibration data.

### What We Measure (and What We Ignore)

**Measured:**
- Brier scores (simulation and market)
- Directional accuracy (sim vs market disagreement resolution)
- Calibration curves per event type
- Cost per simulation
- Time from seed to report
- **Simulation stability** — see dedicated diagnostics (§ Simulation Stability Diagnostics)

**Ignored (at least in Phase 1-2):**
- PnL in dollar terms (irrelevant until Phase 3)
- Sharpe ratio (meaningless with <50 trades)
- "Gut feel" about simulation quality
- Individual agent behavior analysis (fascinating but not decision-relevant)
- sim_confidence (logged but excluded from decisions — see Layer 3 rationale)

### Decision Gates

| Gate | Question | Criteria | Action if Pass | Action if Fail |
|---|---|---|---|---|
| **G0** | Is MiroFish integration contract verified? | 3 manual simulations run, endpoints documented, probability extraction strategy confirmed | Proceed to pipeline development | Debug MiroFish deployment, inspect `/docs`, reverse-engineer frontend calls, or consider browser/file-system automation fallback |
| **G1** | Can we run MiroFish on our infra? | Successful simulation with 100+ agents | Proceed to event selection | Debug deployment |
| **G2a** | Does sim show signal in one narrow category? | Sim Brier < Market Brier on 10 crypto/regulatory narrative events | Expand to 20 events | Analyze failure patterns, check stability diagnostics |
| **G2b** | Does signal hold at scale? | Sim Brier < Market Brier on 20 single-category events AND directional accuracy > 55% | Proceed to Phase 2 | Abandon or re-scope to different category |
| **G3** | Do paper trades show positive expectancy? | Sharpe > 0.5 on 50 paper trades ⚠️ 50 trades is too few for a statistically reliable Sharpe ratio (~±0.5 confidence interval). Treat as directional signal, not a validated metric. Proceed only if supporting metrics (win rate, profit factor) also point in the same direction. | Proceed to Phase 3 | Tune conviction thresholds |
| **G4** | Do live trades maintain paper performance? | 100+ resolved calibration events, positive Brier edge sustained, directional accuracy > 55%, stable diagnostics, paper edge positive after fees/slippage, Sharpe > 0.5 on paper (directional only), no manual probability corrections | Evaluate Phase 4 product direction(s) | Revert to paper, investigate slippage/latency |

---

## Phase 0: Pre-Build Lock

**Duration:** 1–3 days
**Capital at Risk:** $0
**Goal:** Prove that Prophet can run one complete seed-to-report workflow before building the full calibration pipeline.

Phase 0 answers five questions:

1. Can MiroFish run reliably on the existing ClawBot infrastructure?
2. Does MiroFish expose a usable backend API?
3. Can a seed document be submitted programmatically?
4. Can ReportAgent return structured probability output?
5. Can the raw report, structured forecast, simulation config, and seed hash be stored cleanly?

### Phase 0 Required Test

```text
seed_document.md
→ MiroFish/OASIS simulation
→ raw report
→ structured forecast JSON
→ saved database row
```

### Phase 0 Verification Steps

```bash
curl http://localhost:5001/docs
curl http://localhost:5001/openapi.json
```

Then inspect frontend network calls while running one simulation through the UI.

### Phase 0 Exit Criteria

Prophet may enter Phase 1 only if:

* 3 manual simulations complete successfully
* MiroFish integration method is documented
* seed submission method is known
* ReportAgent output format is known
* probability extraction strategy is confirmed
* one test result is saved to Postgres

### Phase 0 Failure Paths

| Failure | Meaning | Action |
|---|---|---|
| Clean HTTP API exists | Best case | Build `mirofish_runner.py` as API adapter |
| Backend endpoints exist but are undocumented | Acceptable | Reverse-engineer frontend calls and document local contract |
| Only UI workflow works | Fragile | Use Playwright/file-system automation only for prototype |
| MiroFish cannot run reliably | Blocking | Pause Prophet or switch to OASIS-direct integration |
| ReportAgent cannot output structured probability | Blocking | Add second-stage probability parser |

---

## Phase 1: Calibration Study

**Duration:** 2-4 weeks
**Capital at Risk:** $0 (observation only)
**Goal:** Answer "Does MiroFish simulation beat Polymarket crowd prices?"

### Phase 1 Hard Constraints (Non-Negotiable)

1. No wallet keys in the codebase or environment.
2. No trading API credentials in any config file.
3. No order placement code anywhere in the repo.
4. No live execution path of any kind.
5. Phase 1 output is a calibration report, not a dashboard.
6. Simulation configs are frozen per run.
7. No mid-study parameter changes without creating a new prompt/config version.
8. All market prices must be captured at simulation trigger time.
9. Failed parses must be logged as failed runs, not manually corrected.
10. Manual seed edits must be flagged in the database.

### Step 1.1: Deploy MiroFish

```bash
# Clone and configure
git clone https://github.com/666ghj/MiroFish ~/mirofish
cd ~/mirofish
cp .env.example .env

# Point at LiteLLM (DeepSeek Flash)
# LLM_API_KEY=<your_key>
# LLM_BASE_URL=http://localhost:4000/v1
# LLM_MODEL_NAME=deepseek/deepseek-v4-flash

# Docker deployment
docker compose up -d
# Frontend: localhost:3000
# Backend: localhost:5001
```

**Validation:** Run a test simulation with a known seed document. Verify agents spawn, interact, and produce a report.

**Alternative:** If Docker is problematic, deploy locally via `npm run setup:all && npm run dev`.

### Step 1.2: Build Pipeline Scripts

```
~/clawbot-v2/prophet/
├── pipeline/
│   ├── __init__.py
│   ├── market_scanner.py        # Discover candidate Polymarket events
│   ├── seed_builder.py          # Build standardized seed docs
│   ├── mirofish_runner.py       # Submit seeds, retrieve reports
│   ├── probability_parser.py    # Extract structured probability JSON
│   ├── forecast_comparison.py   # Compare sim vs market, compute accuracy
│   ├── resolution_monitor.py    # Daily check on unresolved events
│   ├── calibration_report.py    # Generate Phase 1 markdown report
│   ├── logger.py                # Write everything to Postgres
│   └── config.py                # Constants, thresholds
├── sql/
│   └── schema.sql
├── reports/
│   └── phase_1_calibration_report.md
├── seeds/
│   └── sample_seed.md
├── tests/
│   ├── test_market_scanner.py
│   ├── test_seed_builder.py
│   ├── test_probability_parser.py
│   └── test_forecast_comparison.py
└── run_calibration.py           # Main entry point
```

**Key Scripts:**

`market_scanner.py` — discovers candidate Polymarket events and captures market snapshots.

`seed_builder.py` — builds standardized seed documents from source material.

`mirofish_runner.py` — submits seed documents to MiroFish/OASIS and retrieves raw reports.

`probability_parser.py` — extracts structured probability JSON from ReportAgent output.

`forecast_comparison.py` — compares simulation probability with market probability and computes accuracy after resolution.

`resolution_monitor.py` — scheduled daily job that checks unresolved events and writes outcomes to `prophet.resolutions`.

`calibration_report.py` — generates the Phase 1 markdown report.

`logger.py` — writes events, seeds, simulation runs, diagnostics, resolutions, and calibration results to Postgres.

#### Seed Document Template

Every seed document must follow this structure:

```md
# Event Seed Document

## Market Question
[Exact Polymarket question]

## Resolution Criteria
[Exact platform resolution rules]

## Current Market State
- YES price:
- NO price:
- Volume:
- Liquidity:
- Snapshot time:

## Key Facts
- Fact 1
- Fact 2
- Fact 3

## Timeline
- Date: Event
- Date: Event

## Stakeholders
| Stakeholder | Incentive | Likely Position |
|---|---|---|

## Current Narratives

### YES Narrative
[Why YES may happen]

### NO Narrative
[Why NO may happen]

## Key Uncertainties
- Uncertainty 1
- Uncertainty 2

## Source List
- URL 1
- URL 2
- URL 3

## Seed Builder Notes
- Search method:
- Manual edits:
- Source count:
- Seed hash:
```

#### Seed Source Fallback Chain

Fallback chain for seed document sources:

1. **SearXNG** — primary, self-hosted at `localhost:8088`
2. **Tavily API or Brave Search API** — programmatic fallback
3. **Manual seed construction** — allowed only if flagged with `manual_edits = true` and `seed_quality = "manual"`

Perplexity is not treated as a programmatic fallback unless a real API key and implementation are added.

### Step 1.3: Database Schema

```sql
CREATE SCHEMA IF NOT EXISTS prophet;

-- Core event tracking
CREATE TABLE prophet.events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_market_id VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL DEFAULT 'polymarket',
    market_title TEXT NOT NULL,
    market_url TEXT,
    category VARCHAR(100),
    event_type VARCHAR(100),
    resolution_criteria TEXT,
    expected_resolution_time TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Market state at exact timestamps
CREATE TABLE prophet.market_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES prophet.events(id),
    price_yes DECIMAL(5,4),
    price_no DECIMAL(5,4),
    volume_usd DECIMAL(15,2),
    liquidity_usd DECIMAL(15,2),
    orderbook_spread DECIMAL(8,4),
    snapshot_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed document provenance
CREATE TABLE prophet.seeds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES prophet.events(id),
    seed_doc_text TEXT NOT NULL,
    seed_doc_hash VARCHAR(64) NOT NULL,
    source_urls JSONB,
    source_count INTEGER,
    source_time_window TEXT,
    seed_builder_version VARCHAR(50),
    seed_quality VARCHAR(50),
    manual_edits BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Simulation execution records
CREATE TABLE prophet.simulation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES prophet.events(id),
    seed_id UUID REFERENCES prophet.seeds(id),
    market_snapshot_id UUID REFERENCES prophet.market_snapshots(id),

    forecast_probability_yes DECIMAL(5,4),
    forecast_confidence DECIMAL(5,4),
    forecast_direction VARCHAR(10),
    raw_report TEXT,
    structured_forecast JSONB,

    model_name_agents VARCHAR(100),
    model_name_report VARCHAR(100),
    prompt_template_version VARCHAR(50),
    agent_persona_version VARCHAR(50),
    report_agent_prompt_version VARCHAR(50),
    report_parser_version VARCHAR(50),
    temperature_agents DECIMAL(4,3),
    temperature_report DECIMAL(4,3),
    agent_count INTEGER,
    round_count INTEGER,
    random_seed VARCHAR(100),
    mirofish_version VARCHAR(100),
    prophet_commit_hash VARCHAR(100),

    simulation_duration_sec INTEGER,
    simulation_cost_estimate DECIMAL(8,4),
    run_status VARCHAR(50) DEFAULT 'completed',
    error_message TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Stability diagnostics per simulation batch
CREATE TABLE prophet.stability_diagnostics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES prophet.events(id),

    diagnostic_window INTEGER DEFAULT 3,
    probability_iqr DECIMAL(5,4),
    same_seed_variance DECIMAL(8,6),
    convergence_round INTEGER,
    cross_model_probability_delta DECIMAL(5,4),
    cross_model_correlation DECIMAL(5,4),

    hedging_flag BOOLEAN DEFAULT FALSE,
    high_variance_flag BOOLEAN DEFAULT FALSE,
    fast_convergence_flag BOOLEAN DEFAULT FALSE,
    persuasive_wrong_flag BOOLEAN DEFAULT FALSE,
    model_sensitivity_flag BOOLEAN DEFAULT FALSE,

    diagnostic_status VARCHAR(20),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Actual outcomes
CREATE TABLE prophet.resolutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES prophet.events(id),

    actual_outcome BOOLEAN,
    resolution_time TIMESTAMPTZ,
    resolution_source TEXT,
    disputed BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Per-event calibration accuracy
CREATE TABLE prophet.calibration_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_run_id UUID REFERENCES prophet.simulation_runs(id),
    resolution_id UUID REFERENCES prophet.resolutions(id),

    market_brier_score DECIMAL(8,6),
    simulation_brier_score DECIMAL(8,6),
    simulation_better_than_market BOOLEAN,
    market_was_correct BOOLEAN,
    simulation_was_correct BOOLEAN,
    delta_direction_correct BOOLEAN,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Phase 2 only
CREATE TABLE prophet.paper_trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES prophet.events(id),
    simulation_run_id UUID REFERENCES prophet.simulation_runs(id),

    sim_probability DECIMAL(5,4),
    market_price_at_entry DECIMAL(5,4),
    conviction_score DECIMAL(6,4),
    direction VARCHAR(10),

    kelly_sized_position DECIMAL(12,2),
    market_price_at_resolution DECIMAL(5,4),
    paper_pnl DECIMAL(12,2),
    paper_return_pct DECIMAL(8,4),
    won BOOLEAN,

    entry_timestamp TIMESTAMPTZ,
    exit_timestamp TIMESTAMPTZ,
    exit_reason VARCHAR(100),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_events_external_market_id ON prophet.events(external_market_id);
CREATE INDEX idx_market_snapshots_event_id ON prophet.market_snapshots(event_id);
CREATE INDEX idx_seeds_event_id ON prophet.seeds(event_id);
CREATE INDEX idx_simulation_runs_event_id ON prophet.simulation_runs(event_id);
CREATE INDEX idx_stability_event_id ON prophet.stability_diagnostics(event_id);
CREATE INDEX idx_resolutions_event_id ON prophet.resolutions(event_id);
CREATE INDEX idx_calibration_results_run_id ON prophet.calibration_results(simulation_run_id);
CREATE INDEX idx_paper_trades_event_id ON prophet.paper_trades(event_id);
```

**Schema design principle:**

- `events` stores the market/event being tracked.
- `market_snapshots` stores price and liquidity at exact timestamps.
- `seeds` stores input documents and source provenance.
- `simulation_runs` stores each simulation execution. Multiple runs per event are expected.
- `stability_diagnostics` stores failure-mode checks across reruns/models.
- `resolutions` stores ground truth.
- `calibration_results` stores forecast accuracy.
- `paper_trades` is Phase 2-only and must not be used in Phase 1.

**Atomic upsert note:** Calibration aggregates must be computed from `calibration_results` or updated using atomic Postgres `INSERT ... ON CONFLICT DO UPDATE`. Avoid read-then-write updates from Python workers, because concurrent resolution jobs can create race conditions.

### Step 1.4: Select Target Events — Narrow First, Expand Later

**Principle:** Start with one category where narrative matters most and resolution is clearest. Mixed categories introduce noise that makes bad results uninterpretable.

**Primary category: Crypto / company / regulatory narrative events.**

Why this category:
- Public discussion is visible and well-documented (Twitter, forums, news)
- Narratives demonstrably move prices (protocol upgrades, ETF decisions, regulatory rulings)
- Polymarket has deep liquidity in crypto verticals
- Resolution criteria tend to be clear (binary: did the ETF approve? did the fork succeed?)
- Our AI/infra expertise gives us an edge in constructing seed docs for this domain

**Event count: 10 first, then 20 if signal is present.**

A strong result on 10 narrow-category events is more informative than a muddy result on 20 mixed events. If sim beats market on 10 single-category events, we expand to 20 in the same category. If the pattern holds, the signal is category-specific and real. If not, the hypothesis fails faster with less sunk cost.

**Excluded permanently until Phase 3:**
- Sports (retail-dominated, different dynamics, crowded markets)
- Pure macro prints (CPI, NFP — too efficient, low narrative component)
- Elections (noisy, politically motivated liquidity, long resolution windows)

**Selection Criteria:**
- Active on Polymarket, binary (YES/NO) outcome
- Volume > $50,000 (meaningful liquidity)
- 7-60 days to resolution (time for narrative to evolve)
- Current probability between 15% and 85% (information still being discovered)
- Narrative-rich by nature: the outcome depends on how stakeholders interpret events, not just mechanical triggers
- Clear, unambiguous resolution criteria

**Event Examples (illustrative, not final):**
- Crypto: "Will Ethereum Pectra upgrade complete by X date?" "Will Solana file for a spot ETF before December 2026?"
- Regulatory: "Will the SEC approve a spot XRP ETF in Q3 2026?" "Will the EU finalize MiCA stablecoin rules by July?"
- Company: "Does the shareholder vote pass?" "Will the merger close by the deadline?"

*Final event list determined against live Polymarket data at Phase 1 start.*

### Step 1.5: Run and Track

For each event:
1. Build seed document from current news using the seed document template.
2. **Market Snapshot Timing Rule:** Capture market price at the exact time the simulation is triggered. The comparison baseline is `market_price_at_sim_time`, not the price when the seed was built, when the report was parsed, or at end of day. All Brier comparisons use the market probability from the simulation trigger timestamp.
3. Run MiroFish simulation (100-500 agents, 8-12 rounds).
4. Extract probability + confidence via the probability parser (Layer 1 contract).
5. Record Polymarket mid-market price at simulation time.
6. Log to Postgres (events, seeds, market_snapshots, simulation_runs, stability_diagnostics).
7. Monitor for resolution via `resolution_monitor.py`.

### Step 1.6: Analyze Results

**Checkpoint at 10 events:** Run all stability diagnostics first. If any stability metric is in the red zone, halt and fix before continuing (see § Simulation Stability Diagnostics). If stability passes, evaluate Brier score comparison. If sim beats market on 10 events, expand to 20. If not, reconsider category choice or abandon.

At 20 resolved events, compute:

| Metric | Threshold for Phase 2 |
|---|---|
| Sim Brier score < Market Brier score | Must be true |
| Directional accuracy (sim vs market disagreements) | > 55% |
| Sim accuracy (probability > 0.5 matched outcome) | > Market accuracy |
| Stability diagnostics (5 failure modes) | All must pass (see § Simulation Stability Diagnostics) |
| "Sim was hedging" check | IQR of sim probabilities > 0.20 |

**Decision:** If all metrics pass and stability diagnostics are green → Phase 2. If not → analyze failure patterns, iterate on simulation parameters, run next 20 events.

**Disclosure:** Phase 1-2 results are not published, shared, or discussed publicly until G3 is passed. A positive Phase 1 result that becomes public before you've built a trading position is a result you've given away.

*(Cross-reference: see Risk Register R11 — Premature disclosure of Phase 1-2 results.)*

#### Phase 1 Output Artifact

The output of Phase 1 is:

```text
reports/phase_1_calibration_report.md
```

The report must include:

| Event | Category | Market Prob | Sim Prob | Actual | Market Brier | Sim Brier | Sim Better? | Stability Flags |
|---|---|---|---|---|---|---|---|---|

This report — not a dashboard, not a model, not a trading signal — is the deliverable of Phase 1.

Gate G2b passes only if this report shows simulation Brier score beating market Brier score with no major unresolved stability flags.

### Simulation Stability Diagnostics

A simulation that beats the market on Brier score but is unstable under small perturbations is not a reliable signal. These failure modes are tracked independently from the core hypothesis test and flagged as disqualifying regardless of raw Brier scores.

| Failure Mode | What It Looks Like | Minimum Bar to Proceed | Action if Failed |
|---|---|---|---|
| **Probability clustering near 50%** | Sim probabilities cluster in 0.40-0.60 range while market shows more extreme values | Sim's 20-event IQR > 0.20 | Redesign ReportAgent prompt to penalize hedging; add relative confidence framing |
| **High variance across runs** | Two runs of the same simulation with the same seed produce materially different probabilities (>0.15 delta) | Same-seed variance < 0.07 Brier across 3 re-runs | Lock random seeds; increase agent count; homogenize prompt template |
| **Fast convergence without informative disagreement** | Agents all agree in <3 rounds and produce unanimous reports | At least 3 rounds of measurable disagreement before final report | Increase agent persona diversity; add contrarian agent roles; lower temperature of holdouts |
| **Persuasive reports, weak accuracy** | ReportAgent produces coherent narrative probability reports, but forecasts are systematically wrong — the simulation "sounds smart" but predicts poorly | Sim Brier must be meaningfully < market Brier (not just equal) across the full sample | Flag as critical; halt on any single event where report is compelling but forecast is inverted (p > 0.7 on outcome that resolves opposite) |
| **Model sensitivity** | Different LLM backends (Flash vs Pro vs Kimi) produce significantly different probabilities for the same seed event | Cross-model correlation of sim probabilities > 0.80 | Standardize on one model for all Phase 1 runs; if model choice flips the direction, the signal is not from simulation mechanics |

**Rule:** If any stability metric is in the red zone after the first 10 events, the Brier score comparison is unreliable and Phase 1 must be re-run with corrected parameters before any pass/fail judgment. False confidence is Prophet's biggest risk. These diagnostics exist to prevent it.

### Interpreting Ambiguous Phase 1 Results

Ambiguous results (sim beats market ~50-65% of events, no clear signal) are the most dangerous outcome. Without a pre-specified interpretation framework, a motivated builder will always find a narrative to explain away failures and proceed anyway.

| Pattern | Interpretation | Action |
|---|---|---|
| Sim better on politics/macro, worse on crypto/sports | Event type signal — sim may work on narrative-rich events only | Run 20 more events on qualifying types only, exclude underperformers |
| Sim randomly better/worse, no category pattern | Likely noise — hypothesis weak at this config | Halt. Redesign simulation parameters (agent count, rounds, seed construction) before running more events |
| Sim consistently wrong (worse than market 15+/20) | Hypothesis falsified for current configuration | Major iteration on simulation design, or document negative finding and reconsider approach |
| Sim better 15+/20 in a single category | Strong signal for that category | Gate G2b passed — expand to broader categories |
| Sim probability always closer to 50% than market (regression to mean) | Sim may be producing "safe" middle probabilities, not real forecasts | Check if sim probabilities cluster near 50% — if so, sim is hedging, not predicting. Redesign ReportAgent prompt |

**The rule:** if you can't articulate the pattern in the data without using words like "promising," "interesting," or "potential," you're rationalizing. Re-run with stricter criteria.

---

## Phase 1.5: Retrospective Sanity Check

**Duration:** 1 week
**Capital at Risk:** $0
**Goal:** Expose obvious systematic failures before waiting weeks for live events to resolve.

### Scope

Run Prophet against 3–5 already-resolved events where historical market prices are available.

### Process

1. Select resolved events from the same category used in Phase 1.
2. Choose a historical simulation timestamp.
3. Pull historical market probability at that timestamp using price history.
4. Reconstruct the seed document using only information available before that timestamp.
5. Run the simulation.
6. Compare simulation probability, historical market probability, and actual outcome.

### Anti-Leakage Rule

Historical replay is valid only if the seed document excludes information published after the chosen simulation timestamp. Any event with possible information leakage is excluded.

### Interpretation

Phase 1.5 is a sanity check, not final validation. It can reveal:

- regression to 50%
- obvious model instability
- poor seed reconstruction
- systematic wrong-way forecasts
- sensitivity to source selection

### Pass Condition

Prophet may proceed to Phase 2 only if:

- Phase 1 live results are positive or directionally useful
- Phase 1.5 does not contradict Phase 1
- no major stability diagnostics fail

---

## Phase 2: Paper Trading

Phase 2 begins only after:

1. Gate G0 passes.
2. Gate G2a produces a complete 10-event calibration report.
3. Gate G2b confirms the result across 20 events if the 10-event result is positive.
4. Simulation Brier score beats market Brier score.
5. Directional accuracy is above 55%.
6. Stability diagnostics are green or explainable.
7. Phase 1.5 retrospective sanity check does not contradict the live result.
8. All Phase 1 data is stored in Postgres and reproducible.

**Duration:** 2-4 weeks
**Capital at Risk:** $0 (simulated trading only)
**Goal:** "If we had traded on divergence signals, what would the returns be?"

### Step 2.1: Forecast Comparison Engine

Implement full conviction scoring (see Architecture Layer 3).

### Step 2.2: Paper Trading Engine

```python
# For each new event that passes conviction threshold:
# 1. Record "entry" price and size (as if we traded)
# 2. Track simulated PnL through price changes
# 3. Record "exit" on resolution or stop-loss
# 4. Compute paper trade metrics

paper_trades = {
    'event_id': ...,
    'entry_probability': market_price_at_entry,
    'sim_probability': sim_prob,
    'conviction': conviction_score,
    'direction': 'YES' if sim_prob > market_prob else 'NO',
    'position_size': kelly_sized,
    'pnl': final_pnl,
    'won': outcome_matched_direction
}
```

### Step 2.3: Performance Metrics

| Metric | Target |
|---|---|
| Win rate | > 55% |
| Average return per trade | > 2% |
| Sharpe ratio (annualized from paper trades) | > 0.5 ⚠️ 50-sample Sharpe has wide confidence intervals (~±0.5 at 95% CI). Treat as directional signal only |
| Max drawdown | < 15% |
| Profit factor (gross wins / gross losses) | > 1.3 |
| Conviction correlation | Higher conviction → higher win rate |

### Step 2.4: Calibrate Thresholds

Use paper trading data to tune:
- Conviction threshold for trade signals
- Kelly fraction multiplier
- Max position size
- Event type filters (only trade types where sim historically beats market)

**Decision:** If paper metrics pass → Phase 3 (live trading with small capital).

---

## Phase 3: Live Trading

**Duration:** Ongoing
**Capital at Risk:** Small (initial: $500-$1000 USDC)
**Goal:** Validate that paper performance translates to live execution.

Gate G4 unlock requires all of:

- 100+ resolved calibration events
- positive Brier edge over market sustained across event batches
- directional accuracy > 55% sustained
- stable simulation diagnostics with no systematic red flags
- paper trading edge positive after estimated fees and slippage
- Sharpe > 0.5 on paper trades, treated only as directional evidence
- no unresolved data-quality issues in seed provenance
- no manual probability corrections in the dataset

### Step 3.1: Polymarket CLOB Integration

See [Appendix B: Future Modules](#appendix-b-future-modules). Order placement code is not written until Gate G2b passes.

### Step 3.2: Risk Limits

| Limit | Value |
|---|---|
| Initial bankroll | $500-1000 USDC |
| Max per-event exposure | 5% of bankroll |
| Max concurrent positions | 5 |
| Daily loss circuit breaker | 3% of bankroll |
| Stop-loss | Exit if conviction drops >50% |
| Slippage tolerance | 2% from mid-market |
| Minimum liquidity | $10,000 in order book |

### Step 3.3: Monitoring

- Track every trade in Postgres
- Compare live vs paper execution (slippage analysis)
- Alert on circuit breaker triggers

### Step 3.4: Scaling Criteria

Scale capital only when:
- 50+ live trades executed
- Live Sharpe > 0.5
- Live win rate > 55%
- Live slippage < 1% on average
- No circuit breaker triggers

---

## Phase 4: Productization (Deferred — For Reference Only)

**Trigger:** Phase 3 Sharpe > 1.0 over 100+ live trades with positive expectancy.

Two product paths remain open at Phase 3 exit:

**Path A: Calibration-backed scenario intelligence**
Decision tool for narrative-heavy events such as product launches, regulatory decisions, protocol upgrades, policy shifts, and company controversies. More defensible, faster to market, less dependent on direct trading edge.

**Path B: Trading signals / autonomous fund**
Higher ceiling, longer path, more operational and regulatory complexity. Includes simulation-calibrated conviction scores as a subscription API for prediction market traders, or a scaled autonomous fund.

Neither path is committed until Phase 3 data exists. *Designing products before you have calibration data is writing a pitch deck for a company that may not exist.*

---

## Technical Reference

### Key Repositories

| Repository | URL | Role |
|---|---|---|
| MiroFish | github.com/666ghj/MiroFish | Swarm simulation engine |
| CAMEL-AI OASIS | github.com/camel-ai/oasis | Multi-agent social simulation |
| CAMEL-AI Framework | github.com/camel-ai/camel | Agent framework ecosystem |
| Polymarket CLOB Client | github.com/Polymarket/py-clob-client | Python SDK for trading |
| Kalshi Python | github.com/kalshi/kalshi-python | Python SDK for Kalshi |

### Key API Documentation

| API | Documentation URL |
|---|---|
| Polymarket Docs | docs.polymarket.com |
| Polymarket Quickstart | docs.polymarket.com/quickstart |
| Polymarket Rate Limits | docs.polymarket.com/api-reference/rate-limits |
| Polymarket Builder Tiers | docs.polymarket.com/builders/tiers |
| Kalshi API | trading-api.readme.io/reference/introduction |

### Existing Infrastructure (Reused)

| Component | Host/Port | Role in Prophet |
|---|---|---|
| LiteLLM | localhost:4000 | LLM API proxy (Flash for agents, Pro for reports) |
| Postgres | localhost:5432 | Simulation + trade persistence |
| Redis | localhost:6379 | Job queue, caching |
| Qdrant | localhost:6333 | Semantic search for seed doc construction |
| SearXNG | localhost:8088 | Multi-engine news search |
| FastAPI | localhost:8000 | Pipeline orchestration (extend existing API) |
| RQ Worker | Docker | Background simulation execution |
| Docker Compose | - | Container orchestration |

### Cost Model

| Component | Cost | Notes |
|---|---:|---|
| MiroFish agent reasoning | ~$2/sim | Flash model estimate |
| ReportAgent synthesis | ~$0.50/sim | Pro model estimate |
| Polymarket market data | Free | Public endpoints |
| Postgres/Redis/Qdrant | $0 marginal | Existing infra |
| Infrastructure | $0 marginal | Existing droplet |
| **Per simulation** | **~$2.50** | Estimated API cost only |
| **Phase 1 checkpoint — 10 events** | **~$25** | API costs only |
| **Phase 1 total — 20 events** | **~$50** | API costs only |

---

## Risk Register

| # | Risk | Probability | Impact | Mitigation | Contingency |
|---|---|---|---|---|---|
| R1 | MiroFish deployment fails on existing infra | High | Very High — blocks Phase 1; OASIS fallback is a materially different engineering effort, not a quick swap | Test with minimal config first; use offline variant if needed. Plan for 1-2 days of debugging per simulation type in week 1. | Use OASIS directly as fallback; budget 1-2 weeks for OASIS integration separately |
| R2 | Simulations are too expensive at scale | Low | Medium | Flash for agents, Pro only for synthesis; batch overnight | Reduce agent count, rounds |
| R3 | Simulation accuracy doesn't beat market | Medium | High (invalidates core hypothesis) | Track per-event-type accuracy; identify where sim works best | Narrow scope to specific event types, or publish negative result as valuable finding |
| R4 | Polymarket API changes or rate limits tighten | Low | Medium | Use WebSocket where possible; join Builder Program for elevated limits | Switch focus to Kalshi API |
| R5 | CFTC regulatory crackdown on prediction markets | Low | High | Operate on Polymarket only (global, crypto-native); no Kalshi in Phase 1-2 | Withdraw to research-only mode |
| R6 | Live trading losses exceed risk limits | Medium | Medium | Strict position sizing, circuit breakers, daily loss limits | Halt trading, review all signals |
| R7 | Event resolution disputes or ambiguity | Medium | Low | Only trade events with clear, unambiguous resolution criteria | Exclude disputed events from calibration |
| R8 | Agent homogenization degrades simulation quality | Low | Medium | OASIS has built-in diversity mechanisms; monitor agent behavior diversity | Increase agent persona variance, add noise to LLM temperature |
| R9 | Market moves against position before resolution | High | Low | This is expected — binary options are volatile. Hold to resolution unless stop-loss triggered. | Accept volatility as normal; sizing limits contain damage |
| R10 | Smart contract risk (Polymarket) | Very Low | High | Use only spot USDC, no leverage; keep funds on platform only when actively trading | Withdraw to wallet between trades |
| R11 | Premature disclosure of Phase 1-2 results before building a trading position | Low | Very High — gives away the signal before capturing any value | Results not published, shared, or discussed publicly until G3 is passed (enforced in Phase 1.6) | If accidentally disclosed, accelerate to Phase 3 live trading to capitalize before others follow |

---

## Required Build Order

Prophet must be built in this order:

1. `PHASE_0_SPEC.md`
2. `schema.sql`
3. `market_scanner.py`
4. `seed_builder.py`
5. `mirofish_runner.py`
6. `probability_parser.py`
7. `logger.py`
8. `resolution_monitor.py`
9. `forecast_comparison.py`
10. `calibration_report.py`
11. `run_calibration.py`

Explicitly deferred:

- dashboard
- paper trading
- live execution
- wallet integration
- order placement
- full product UI
- Kalshi integration

---

## Appendix A: Research Sources

### Prediction Markets
- MEXC Learn: "Best Prediction Market Platforms 2026"
- QuantVPS: "Prediction Markets Volume Compared"
- CryptoTimes: "Polymarket vs Kalshi vs Augur - Which Wins in 2026"
- PredictStreet: "The Great Prediction War of 2026"
- TS Imagine: "Global Regulation of Prediction Event Markets"
- MetaMask: "Prediction Market Overview & Trends 2026"
- TRM Labs: "How Prediction Markets Scaled to $21B Monthly Volume in 2026"
- Stanford Law: "Prediction Markets Are Surging - Here's What You Need to Know"
- CFTC Press Releases: 9194-26, 9193-26
- Federal Register: "Prediction Markets" (March 16, 2026)
- Greenberg Traurig: "CFTC Regulatory Developments on Prediction Markets" (March 2026)
- Sullivan & Cromwell: "CFTC Updates Enforcement Priorities" (April 2026)
- Lowenstein Sandler: "CFTC and Kalshi Enforcement Actions"

### MiroFish & OASIS
- MiroFish Official Site: mirofish.my
- MiroFish GitHub: github.com/666ghj/MiroFish
- MiroFish Offline: github.com/nikmcfly/MiroFish-Offline
- CAMEL-AI OASIS: github.com/camel-ai/oasis
- CAMEL-AI Framework: github.com/camel-ai/camel
- FlowZap: "MiroFish - Build Your Own Synthetic Focus Group"
- Emelia.io: "MiroFish AI Swarm Prediction"
- Blocmates: "What Is MiroFish - The Agent Engine That Can Predict Anything"
- Dev.to: "MiroFish - The Open Source AI Engine That Builds Digital Worlds"

### AI Agents & DeFAI
- KuCoin: "Will AI Agents Take Over DeFi - 2026-2030 Predictions"
- Galaxy Research: "Predictions 2026 - Crypto, Bitcoin, DeFi"
- WEEX: "5 Best AI Agents in 2026"
- Crypto.news: "8 Leading AI Trading Bots for May 2026"

### Academic
- Taylor & Francis (2026): "Manipulation in Prediction Markets - An Agent-Based Modeling Experiment"
- University of Bristol: "Price Drivers in Prediction Markets"
- Koa et al. (2024): LLM-powered agents in market simulation
- Stanford/Simudyne: Agent-based modeling in capital markets

### Polymarket API & Tools
- Polymarket Documentation: docs.polymarket.com
- Polymarket Quickstart: docs.polymarket.com/quickstart
- Polymarket py-clob-client: github.com/Polymarket/py-clob-client
- AgentBets: "Prediction Market Trading Layer"
- FutureSearch: "Kalshi Trader Case Study"

---

## Appendix B: Future Modules

These modules are not part of Phase 1, Phase 1.5, Phase 2, or early Phase 3. They are documented for reference only.

No code for these modules should exist in the codebase until Gate G2b is passed.

### Future Trading Module

Includes:
- wallet integration
- CLOB authentication
- order placement
- position sizing
- live risk controls
- stop-loss logic
- live PnL tracking

**Kelly Sizing (reference only):**
```
edge = |sim_probability - market_probability|
odds = market_probability / (1 - market_probability)  # for YES positions
kelly_fraction = edge - ((1 - edge) / odds)
position_size = bankroll × (kelly_fraction × risk_multiplier)

WHERE:
  risk_multiplier: 0.25 (quarter-Kelly - conservative)
  max_position: 5% of bankroll (hard cap)
  min_position: 0.1% of bankroll (noise floor)
```

**Order Execution (Polymarket CLOB):**
```python
from py_clob_client import ClobClient
from py_clob_client.clob_types import OrderArgs

# Place limit order at mid-market or slightly better
order = client.create_and_post_order(OrderArgs(
    token_id=token_id,
    price=limit_price,
    size=position_size,
    side="BUY"
))

# Monitor via WebSocket for fills
# Exit conditions: resolution OR conviction collapse OR stop-loss
```

**Risk Controls:**
- Max single-event exposure: 5% of bankroll
- Max concurrent positions: 10
- Max daily loss: 3% of bankroll (circuit breaker)
- Stop-loss: exit if conviction drops >50% from entry
- Resolution-only exit: hold unless stop-loss triggered
- No leverage, no margin, spot USDC only

### Future Dashboard Views

Includes:
- open positions
- live PnL
- realized/unrealized returns
- slippage analysis
- capital allocation
- trade history

### Future Kalshi Integration

Kalshi integration is deferred because Phase 1 does not need regulated trading infrastructure. Polymarket market data is enough for calibration.

---

## Document History

| Version | Date | Changes |
|---|---|---|
| 1.0 | May 11, 2026 | Initial blueprint — complete research synthesis, architecture, roadmap |
| 1.1 | May 11, 2026 | Reframed Prophet as calibration lab; narrowed Phase 1 to crypto/company/regulatory narrative events; added stability diagnostics |
| 1.2 | May 12, 2026 | Added Phase 0 integration proof, layer renames, 8-table schema split, seed provenance, simulation versioning, Phase 1 hard constraints, Future Modules appendix, Phase 1.5 retrospective sanity check, resolution monitor, calibration report output, ReportAgent contract, probability parser, seed template, SearXNG fallback fix, gate G0, no-dashboard rule, dashboard deferral rule, required build order, strengthened Phase 2 entry criteria, expanded Gate G4 prerequisites, and fixed duplicate cost rows |

*This is a living document. Version history will grow with the project. All future changes — parameter tuning, implementation decisions, resolved risks — are recorded here.*

---

*This document is the single source of truth for the Prophet project. All implementation decisions reference this blueprint. Update it as the system evolves.*
