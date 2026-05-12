# Prophet — Blueprint

## A Simulation-Calibrated Prediction Market System

**Author:** ClawBot + Akshar  
**Date:** May 11, 2026  
**Status:** Research Complete — Phase 1 Ready  
**Version:** 1.0

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [The Three Domains](#the-three-domains)
3. [The Gap](#the-gap)
4. [Why No One Is Building This](#why-no-one-is-building-this)
5. [Prophet Architecture](#prophet-architecture)
6. [First Principles Design](#first-principles-design)
7. [Phase 1: Calibration Study](#phase-1-calibration-study)
8. [Phase 2: Paper Trading](#phase-2-paper-trading)
9. [Phase 3: Live Trading](#phase-3-live-trading)
10. [Phase 4: Productization](#phase-4-productization)
11. [Technical Reference](#technical-reference)
12. [Risk Register](#risk-register)
13. [Appendix: Research Sources](#appendix-research-sources)

---

## Executive Summary

**Prophet** is a system that bridges two disconnected worlds: **swarm intelligence simulation** (MiroFish/OASIS — thousands of AI agents modeling narrative formation) and **prediction markets** (Polymarket/Kalshi — crowd beliefs aggregated into prices).

The core bet: *A swarm simulation that models how narratives form, spread, and converge through social dynamics can predict event outcomes more accurately than prediction market prices — especially for narrative-rich, multi-stakeholder events where the crowd systematically underweights second-order effects.*

If true, Prophet generates compounding alpha. If false, the experiment generates a unique dataset (simulation vs market vs reality) that no one else has.

**No one is building this.** The skill stack (multi-agent simulation + prediction market mechanics + crypto infrastructure + production backend) doesn't exist in any single team, and the incentive structures of every relevant actor push away from this exact integration.

---

## The Three Domains

### Domain 1: Prediction Markets (2026 State of Play)

**Scale:** $20B+/month in global volume. Up from $73M (Polymarket, 2023). A legitimate financial primitive — the Federal Reserve cites Kalshi as a superior macro expectations benchmark.

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
- **Mar 11-12, 2026:** Opened ANPRM for public comment — signaling "responsible innovation"
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
| **Narrative Blind Spots** | Markets price events but don't model second-order narrative effects | This is Prophet's core edge — modeling what the crowd hasn't processed yet |
| **Retail Dominance** | 90% of sports volume is retail gambling, embedding systematic biases | Simulation models institutional-quality analysis, not retail emotion |

---

### Domain 2: MiroFish — Swarm Intelligence Simulation

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

**LLM Integration:** Supports any OpenAI SDK-format API. Defaults to Alibaba Qwen-Plus. Compatible with DeepSeek Flash/Pro via LiteLLM. This makes simulation costs manageable — Flash is approximately 12x cheaper than Pro.

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
- Investors can buy "agent shares" — own pieces of AI revenue streams
- Specialist bots outpacing generalists in specific niches

**Agent Identity & Payments:**
- KYA (Know Your Agent) replacing KYC — cryptographic signatures establish trustworthy AI identities
- x402 standard enabling high-frequency microtransactions between agents
- Projected 30% of Base daily transactions and 5% of Solana non-vote transactions in 2026

**Emerging Risk — Algorithmic Resonance:**
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

### What Each Approach Does — and Doesn't Do

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
- **Doesn't:** Model narratives. No understanding of WHY prices move. Can't simulate counterfactuals. Purely reactive — responds to what IS, not what WILL BE.

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

**MiroFish / Shanda Group:** Their incentive is platform adoption — more users uploading docs, more simulations run. Building a proprietary trading system doesn't grow their user base. It would be a conflict (using their engine to extract value from markets, rather than selling the engine).

**CAMEL-AI / OASIS:** Academic consortium. Incentives: citations, papers, community contributions. A trading system is outside their scope and doesn't advance their research agenda. No academic reward for building a prediction market bot.

**Polymarket / Kalshi:** Their incentive is volume and liquidity. They want MORE traders, not smarter ones. A tool that helps specific traders systematically beat the market potentially triggers adverse selection — retail realizes they're the dumb money and leaves. Platforms have a structural incentive to keep the playing field level enough that retail participation doesn't collapse.

**Quant funds / professional traders:** If they build anything like this, they keep it proprietary. The few people capable of building this have the strongest incentive to hide it. The absence of public evidence isn't evidence of absence — it's evidence of secrecy.

**Open-source AI community:** Building this requires domain knowledge in binary options pricing, order book mechanics, USDC settlement, CFTC regulation, and event contract resolution — none of which are in the typical open-source AI dev's toolkit. And the payoff is niche alpha, not GitHub stars or academic citations or conference talks. Way more grinding for way less prestige.

**Retail / indie builders:** The people who DO build prediction market bots are crypto-native degens optimizing for speed and arbitrage. Their mental model is "read prices, find edge, trade." The conceptual leap to "simulate social dynamics, compare to prices, THEN trade" is a paradigm shift most traders never make. Conversely, the people who understand simulation (AI researchers) typically don't trade prediction markets at all.

### 3. The Time Horizon Mismatch

| What Needs to Happen | Time Required | Who Can't Afford This |
|---|---|---|
| Build simulation pipeline | 2-4 weeks | — (anyone can) |
| Run simulations on real events | Ongoing | — |
| **Wait for events to resolve** | **Days to months** | Startups (18-month VC cycles), academics (conference deadlines) |
| Compare simulation vs reality | Ongoing accumulation | Anyone needing a paper/demo/raise in <6 months |
| Tune parameters from calibration data | Months to years | Anyone optimizing for quarterly results |
| Compound the learning loop | Years | Almost everyone |

The payoff curve is back-loaded. Year 1: generating calibration data, eating losses. Year 2: system starts outperforming. Year 3-5: data moat is deep enough that new entrants can't replicate. This is a power-law compounding curve that looks flat for the first 12-18 months. No VC-funded startup can sell that to a board. No academic can publish that before tenure. No indie hacker can survive that long without revenue.

### 4. The "MiroFish is Brand New" Factor

MiroFish's GitHub was created in April 2026 — barely a month old. The community is still figuring out basic reliability, debating deployment tradeoffs, sharing prompt recipes. Financial use cases are experimental GitHub issues, not production systems. The window is open *right now*. In 6-12 months, someone will have productionized this — either a startup, a hedge fund, or a well-funded solo builder.

### 5. The Cold Start Bootstrap Problem

```
To know if simulations beat markets → you need calibration data
To get calibration data → you need to run simulations on real events
To run meaningful simulations → you need a tuned simulation pipeline
To tune the pipeline → you need calibration data
```

Someone must bootstrap this cold. That means running early simulations knowing they'll be inaccurate, eating API costs with no immediate return, recording everything systematically even when the signal looks noisy, and trusting the learning curve exists before you can see it. Most builders hit this loop, see early noise, conclude "it doesn't work," and leave. They never discover whether the noise was the bootstrapping phase or the steady state. The difference between "it doesn't work" and "it doesn't work YET" is months of systematic logging — and almost nobody bridges that gap.

### 6. The Gambling Stigma

Despite being cited by the Federal Reserve, regulated by the CFTC, backed by ICE at $9B, and doing $20B+/month in volume — prediction markets carry a gambling stigma. Serious AI/ML engineers associate them with crypto degens and political betting, not legitimate information aggregation. The people with the technical skills to build this are often the most reputation-conscious. This creates a talent vacuum at the exact intersection where the most interesting work is possible.

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
│  │ NARRATIVE       │   │ MARKET LENS     │   │ DIVERGENCE      │   │
│  │ ENGINE          │──▶│                 │──▶│ CALCULATOR      │   │
│  │                 │   │                 │   │                 │   │
│  │ MiroFish/OASIS  │   │ Polymarket APIs │   │ sim probability │   │
│  │ agent swarm     │   │ + Kalshi APIs   │   │ vs              │   │
│  │ simulation      │   │                 │   │ market price    │   │
│  │                 │   │ market prices   │   │                 │   │
│  │ seed → report   │   │ order books     │   │ conviction      │   │
│  │ → probability   │   │ historical data │   │ score           │   │
│  └─────────────────┘   └─────────────────┘   └───────┬─────────┘   │
│                                                       │             │
│                       ┌───────────────────────────────┘             │
│                       ▼                                              │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐   │
│  │ EXECUTION       │   │ LEARNING LOOP   │   │ DASHBOARD       │   │
│  │ ENGINE          │──▶│                 │   │                 │   │
│  │                 │   │                 │   │ active sims     │   │
│  │ Kelly sizing    │   │ sim vs actual   │   │ open positions  │   │
│  │ order placement │   │ resolution      │   │ PnL tracker     │   │
│  │ position mgmt   │   │                 │   │ calibration     │   │
│  │ risk limits     │   │ Brier scores    │   │ metrics         │   │
│  │                 │   │ → calibrate sim │   │ divergence map  │   │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    DATA LAYER (Postgres + Redis + Qdrant)    │    │
│  │  simulations | markets | positions | resolutions | feedback  │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### Layer 1: Narrative Engine (MiroFish / OASIS)

**Purpose:** Transform real-world event seeds into structured probability estimates through multi-agent social simulation.

**Inputs:**
- Seed document (news article, policy draft, earnings report, event description)
- Simulation parameters (agent count, rounds, platforms, prompt recipe)
- Historical calibration data for this event type (from Learning Loop)

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

**Cost Estimate:** $2-5 per full simulation (Flash for agents, Pro for report). For 20-event calibration study: $40-100 total API cost.

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

### Layer 3: Divergence Calculator

**Purpose:** Compare simulation probability against market probability, compute conviction score.

**Core Calculation:**

```
raw_delta = sim_probability - market_probability

conviction = raw_delta × sim_confidence × liquidity_factor × calibration_factor

WHERE:
  sim_confidence: ReportAgent's self-assessed confidence (0-1)
  liquidity_factor: min(1.0, market_volume / min_volume_threshold)
  calibration_factor: historical_brier_ratio for this event_type
    (calibration_factor > 1.0 if sim historically beats market on this type)
```

**Thresholds (initial, to be calibrated in Phase 2):**

| Conviction | Action |
|---|---|
| < 0.05 | No action — signal too weak |
| 0.05 - 0.10 | Log as "observation" — track for calibration |
| 0.10 - 0.15 | Consider paper trade |
| > 0.15 | Trade signal (paper or live, depending on phase) |

### Layer 4: Execution Engine

**Purpose:** Translate conviction signals into sized, placed, and monitored positions.

**Position Sizing (Kelly Criterion, fractional):**

```
edge = |sim_probability - market_probability|
odds = market_probability / (1 - market_probability)  # for YES positions
kelly_fraction = edge - ((1 - edge) / odds)
position_size = bankroll × (kelly_fraction × risk_multiplier)

WHERE:
  risk_multiplier: 0.25 (quarter-Kelly — conservative)
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
    price=limit_price,    # mid-market or better
    size=position_size,   # USDC amount
    side="BUY"            # BUY or SELL
))

# Monitor via WebSocket for fills
# Exit conditions: resolution OR conviction collapse OR stop-loss
```

**Risk Controls:**
- Max single-event exposure: 5% of bankroll
- Max concurrent positions: 10
- Max daily loss: 3% of bankroll (circuit breaker)
- Stop-loss: exit if conviction drops >50% from entry
- Resolution-only exit: hold unless stop-loss triggered (long-term events)
- No leverage, no margin, spot USDC only

### Layer 5: Learning Loop

**Purpose:** Transform every resolved event into calibration data that improves future simulations.

**Data Collected Per Event:**

```
simulation_id
├── sim_probability: 0.72
├── sim_confidence: 0.68
├── market_probability_at_sim: 0.58
├── market_probability_at_resolution: 1.0 (if YES)
├── actual_outcome: YES
├── event_type: political_election
├── event_subtype: presidential_primary
├── days_to_resolution: 14
├── simulation_params: {agents: 500, rounds: 10, model: flash}
├── seed_doc_hash: abc123
├── resolution_notes: "no disputes, clear outcome"
│
├── sim_was_correct: True
├── market_was_correct: True
├── sim_brier_score: 0.0784   # (0.72 - 1.0)² = 0.0784
├── market_brier_score: 0.1764 # (0.58 - 1.0)² = 0.1764
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
- Conviction Calculator parameters auto-tune based on rolling 20-event window
- Simulation prompt recipes updated when specific event types underperform
- Agent count/rounds adjusted based on cost-benefit per event type

### Layer 6: Dashboard

**Purpose:** Visualize the entire system state — simulations, markets, positions, and calibration metrics.

**Views:**

| View | Content |
|---|---|
| **Active Simulations** | Running sims, progress, preliminary probabilities |
| **Open Positions** | Current holdings, entry price, current PnL, conviction score |
| **Market Monitor** | Tracked events, market prices, simulation estimates, delta |
| **Calibration** | Brier scores by event type, directional accuracy over time, confidence calibration plots |
| **PnL Tracker** | Cumulative PnL, win rate, Sharpe ratio, max drawdown |
| **Event Explorer** | Browse active Polymarket events, filter by category/volume, trigger simulation |

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
- Divergence Calculator: `input(sim_prob, market_prob, metadata) → output(conviction)`
- Execution Engine: `input(conviction, event_id, market) → output(position_id)`
- Learning Loop: `input(resolution_data) → output(updated_calibration_curves)`

**5. Cheap Models for Agents, Expensive for Synthesis**

Agent reasoning (hundreds of agents × multiple rounds) uses DeepSeek Flash. ReportAgent synthesis (single call per simulation) uses DeepSeek Pro. This keeps costs at ~$2-5 per simulation vs $50-200 if all agents used Pro.

**6. Polymarket First, Kalshi Later**

Polymarket requires no KYC, no geographic restriction (for non-US), public APIs with no auth for market data. It's the path of least resistance. Kalshi adds regulatory complexity that Phase 1 doesn't need.

**7. Favor Asynchronous Over Real-Time**

MiroFish simulations take minutes to hours, not milliseconds. This is correct — the edge is narrative depth, not speed. Events resolve in days to weeks. Batch simulations overnight. Compare to market prices the next morning.

### What We Measure (and What We Ignore)

**Measured:**
- Brier scores (simulation and market)
- Directional accuracy (sim vs market disagreement resolution)
- Calibration curves per event type
- Cost per simulation
- Time from seed to report

**Ignored (at least in Phase 1-2):**
- PnL in dollar terms (irrelevant until Phase 3)
- Sharpe ratio (meaningless with <50 trades)
- "Gut feel" about simulation quality
- Individual agent behavior analysis (fascinating but not decision-relevant)

### Decision Gates

| Gate | Question | Criteria | Action if Pass | Action if Fail |
|---|---|---|---|---|
| **G1** | Can we run MiroFish on our infra? | Successful simulation with 100+ agents | Proceed to event selection | Debug deployment |
| **G2** | Does simulation beat market on 20 events? | Sim Brier < Market Brier AND directional accuracy > 55% | Proceed to Phase 2 | Analyze failure patterns, iterate |
| **G3** | Do paper trades show positive expectancy? | Sharpe > 0.5 on 50 paper trades | Proceed to Phase 3 | Tune conviction thresholds |
| **G4** | Do live trades maintain paper performance? | 50 live trades with Sharpe > 0.5 | Scale capital, add Kalshi | Revert to paper, investigate slippage/latency |

---

## Phase 1: Calibration Study

**Duration:** 2-4 weeks  
**Capital at Risk:** $0 (observation only)  
**Goal:** Answer "Does MiroFish simulation beat Polymarket crowd prices?"

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
│   ├── market_scanner.py      # Polymarket Gamma API integration
│   ├── seed_builder.py        # Construct seed docs from SearXNG/news
│   ├── mirofish_runner.py     # Launch simulation, parse report
│   ├── divergence.py          # Compare sim vs market
│   ├── logger.py              # Postgres persistence
│   └── config.py              # Constants, thresholds
├── sql/
│   └── schema.sql             # Simulations + resolutions tables
├── tests/
│   └── test_pipeline.py
└── run_calibration.py         # Main entry point
```

**Key Scripts:**

`market_scanner.py` — Discovers active Polymarket events suitable for simulation:
- Filter: active=true, volume > $50K, binary outcomes
- Exclude: sports (retail-dominated, different dynamics), events <7 days to resolution, events at >95% probability
- Return: event_id, title, outcomes, current prices, volume, category, resolution date

`seed_builder.py` — Constructs seed documents from news sources:
- For each target event, search SearXNG for related news articles
- Extract key facts, stakeholder positions, timeline, disputed claims
- Assemble into structured seed document (markdown)
- Include: event context, key actors, current state, what's at stake, uncertainty factors

`mirofish_runner.py` — Launches simulations and parses output:
- POST seed document to MiroFish backend API
- Wait for simulation completion (poll or webhook)
- Parse ReportAgent output to extract probability, confidence, narrative summary
- Store full simulation log for audit

`logger.py` — Persists everything to Postgres:
- Simulation runs (input, output, timing, cost)
- Market snapshots (prices at simulation time)
- Resolution tracking (outcome, timing, disputes)

### Step 1.3: Database Schema

```sql
-- Core simulation tracking
CREATE TABLE prophet.simulations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(255) NOT NULL,            -- Polymarket event ID
    market_title TEXT NOT NULL,
    market_url TEXT,
    category VARCHAR(100),                     -- politics, crypto, macro, etc.
    
    -- Market state at simulation time
    polymarket_price_yes DECIMAL(5,4),         -- e.g., 0.5800
    polymarket_volume_usd DECIMAL(15,2),
    polymarket_liquidity_usd DECIMAL(15,2),
    market_snapshot_at TIMESTAMPTZ,
    
    -- Simulation outputs
    mirofish_probability DECIMAL(5,4),         -- e.g., 0.7200
    mirofish_confidence DECIMAL(5,4),          -- 0-1 self-assessed confidence
    mirofish_raw_report TEXT,                  -- Full ReportAgent output
    simulation_params JSONB,                   -- agents, rounds, model, prompt_recipe
    simulation_duration_sec INTEGER,
    simulation_cost_estimate DECIMAL(8,4),
    
    -- Derived
    raw_delta DECIMAL(5,4),                    -- sim - market
    event_type VARCHAR(50),
    seed_doc_hash VARCHAR(64),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Resolution tracking
CREATE TABLE prophet.resolutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id UUID REFERENCES prophet.simulations(id),
    
    -- Actual outcome
    actual_outcome BOOLEAN,                    -- TRUE = YES resolved, FALSE = NO
    resolution_time TIMESTAMPTZ,
    resolution_source TEXT,                    -- polymarket, manual, etc.
    disputed BOOLEAN DEFAULT FALSE,
    
    -- Accuracy metrics
    sim_was_correct BOOLEAN,                   -- sim_prob > 0.5 matched outcome?
    market_was_correct BOOLEAN,                -- market > 0.5 matched outcome?
    sim_brier_score DECIMAL(8,6),              -- (prob - outcome)²
    market_brier_score DECIMAL(8,6),
    sim_better_than_market BOOLEAN,
    delta_direction_correct BOOLEAN,           -- sim pointed in right direction vs market
    
    resolved_at TIMESTAMPTZ DEFAULT NOW()
);

-- Calibration aggregates (materialized per event type)
CREATE TABLE prophet.calibration (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) UNIQUE,
    event_count INTEGER DEFAULT 0,
    sim_accuracy DECIMAL(5,4),                 -- % correct at >0.5 threshold
    market_accuracy DECIMAL(5,4),
    sim_mean_brier DECIMAL(8,6),
    market_mean_brier DECIMAL(8,6),
    directional_accuracy DECIMAL(5,4),         -- % sim points in right direction
    mean_confidence DECIMAL(5,4),              -- for calibration curve
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_simulations_event_id ON prophet.simulations(event_id);
CREATE INDEX idx_simulations_created ON prophet.simulations(created_at);
CREATE INDEX idx_simulations_event_type ON prophet.simulations(event_type);
CREATE INDEX idx_resolutions_sim_id ON prophet.resolutions(simulation_id);
```

### Step 1.4: Select 20 Target Events

**Selection Criteria:**
- Active on Polymarket, binary (YES/NO) outcome
- Volume > $50,000 (meaningful liquidity)
- 7-60 days to resolution (time for narrative to evolve)
- Current probability between 15% and 85% (information still being discovered)
- Narrative-rich: politics, macro, policy, technology, crypto (not sports)
- Clear, unambiguous resolution criteria

**Initial Candidate Categories (to be finalized against live Polymarket data):**
- Political: election outcomes, legislative votes, confirmation odds
- Macro: Fed rate decisions, CPI prints, GDP forecasts
- Crypto: protocol upgrades, ETF approvals, token price thresholds
- Technology: regulatory decisions, company milestones, product launches
- Geopolitical: sanctions, agreements, conflict developments

### Step 1.5: Run and Track

For each event:
1. Build seed document from current news
2. Run MiroFish simulation (100-500 agents, 8-12 rounds)
3. Extract probability + confidence from ReportAgent
4. Record Polymarket mid-market price at simulation time
5. Log to Postgres
6. Monitor for resolution

### Step 1.6: Analyze Results

At 20 resolved events, compute:

| Metric | Threshold for Phase 2 |
|---|---|
| Sim Brier score < Market Brier score | Must be true |
| Directional accuracy (sim vs market disagreements) | > 55% |
| Sim accuracy (probability > 0.5 matched outcome) | > Market accuracy |
| Event type breakdown | Identify which types sim excels at |

**Decision:** If metrics pass → Phase 2. If not → analyze failure patterns, iterate on simulation parameters, run next 20 events.

---

## Phase 2: Paper Trading

**Duration:** 2-4 weeks  
**Capital at Risk:** $0 (simulated trading only)  
**Goal:** "If we had traded on divergence signals, what would the returns be?"

### Step 2.1: Divergence Calculator

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
| Sharpe ratio (annualized from paper trades) | > 0.5 |
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

### Step 3.1: Polymarket CLOB Integration

```python
from py_clob_client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType

# Initialize authenticated CLOB client
client = ClobClient(
    host="https://clob.polymarket.com",
    chain=CHAIN_ID,  # Polygon: 137
    signer=wallet_client,
    creds=api_credentials,
    signature_type=0,  # EOA
)

# Place order
order = client.create_and_post_order(OrderArgs(
    token_id=token_id,
    price=limit_price,
    size=size,
    side="BUY",
    order_type=OrderType.GTC,  # Good-til-cancelled
))
```

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
- Real-time PnL dashboard
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

## Phase 4: Productization

**Trigger:** 6+ months of live trading with positive expectancy.

### Potential Products

| Product | Description | Target User |
|---|---|---|
| **Prophet Signals API** | REST/WebSocket API serving simulation-calibrated probability estimates | Quant funds, professional traders |
| **Prophet Dashboard** | Self-serve platform to run simulations on any Polymarket event | Retail analysts, researchers |
| **Prophet Fund** | Autonomous prediction fund — MiroFish simulations → automated trading | Passive capital allocators |
| **Prophet Research** | Publish calibration study results, advance "simulation finance" as a field | Academic/industry |

### Infrastructure Scaling

- MiroFish simulation scheduling and queuing (RQ worker integration)
- Parallel simulation execution (multiple events simultaneously)
- Automated seed document generation (news monitoring → automatic simulation triggers)
- Cross-platform execution (add Kalshi, other prediction markets)
- Simulation parameter optimization (genetic algorithms over agent configs)

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
| Docker Compose | — | Container orchestration |

### Cost Model

| Component | Cost | Notes |
|---|---|---|
| MiroFish agent reasoning | ~$2/sim (Flash) | 500 agents × 10 rounds × cheap model |
| ReportAgent synthesis | ~$0.50/sim (Pro) | Single Pro call per simulation |
| Polymarket market data | Free | No auth required for public endpoints |
| Polymarket trading fees | 0-1.5% | Fee-free or low-fee markets |
| Postgres/Redis/Qdrant | $0 (existing) | Already running |
| Infrastructure | $0 marginal | Existing droplet capacity |
| **Total per simulation** | **~$2.50** | |
| **Phase 1 total (20 events)** | **~$50** | API costs only |

---

## Risk Register

| # | Risk | Probability | Impact | Mitigation | Contingency |
|---|---|---|---|---|---|
| R1 | MiroFish deployment fails on existing infra | Medium | High (blocks Phase 1) | Test with minimal config first; use offline variant if needed | Use OASIS directly without MiroFish frontend |
| R2 | Simulations are too expensive at scale | Low | Medium | Flash for agents, Pro only for synthesis; batch overnight | Reduce agent count, rounds |
| R3 | Simulation accuracy doesn't beat market | Medium | High (invalidates core hypothesis) | Track per-event-type accuracy; identify where sim works best | Narrow scope to specific event types, or publish negative result as valuable finding |
| R4 | Polymarket API changes or rate limits tighten | Low | Medium | Use WebSocket where possible; join Builder Program for elevated limits | Switch focus to Kalshi API |
| R5 | CFTC regulatory crackdown on prediction markets | Low | High | Operate on Polymarket only (global, crypto-native); no Kalshi in Phase 1-2 | Withdraw to research-only mode |
| R6 | Live trading losses exceed risk limits | Medium | Medium | Strict position sizing, circuit breakers, daily loss limits | Halt trading, review all signals |
| R7 | Event resolution disputes or ambiguity | Medium | Low | Only trade events with clear, unambiguous resolution criteria | Exclude disputed events from calibration |
| R8 | Agent homogenization degrades simulation quality | Low | Medium | OASIS has built-in diversity mechanisms; monitor agent behavior diversity | Increase agent persona variance, add noise to LLM temperature |
| R9 | Market moves against position before resolution | High | Low | This is expected — binary options are volatile. Hold to resolution unless stop-loss triggered. | Accept volatility as normal; sizing limits contain damage |
| R10 | Smart contract risk (Polymarket) | Very Low | High | Use only spot USDC, no leverage; keep funds on platform only when actively trading | Withdraw to wallet between trades |

---

## Appendix: Research Sources

### Prediction Markets
- MEXC Learn: "Best Prediction Market Platforms 2026"
- QuantVPS: "Prediction Markets Volume Compared"
- CryptoTimes: "Polymarket vs Kalshi vs Augur — Which Wins in 2026"
- PredictStreet: "The Great Prediction War of 2026"
- TS Imagine: "Global Regulation of Prediction Event Markets"
- MetaMask: "Prediction Market Overview & Trends 2026"
- TRM Labs: "How Prediction Markets Scaled to $21B Monthly Volume in 2026"
- Stanford Law: "Prediction Markets Are Surging — Here's What You Need to Know"
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
- FlowZap: "MiroFish — Build Your Own Synthetic Focus Group"
- Emelia.io: "MiroFish AI Swarm Prediction"
- Blocmates: "What Is MiroFish — The Agent Engine That Can Predict Anything"
- Dev.to: "MiroFish — The Open Source AI Engine That Builds Digital Worlds"

### AI Agents & DeFAI
- KuCoin: "Will AI Agents Take Over DeFi — 2026-2030 Predictions"
- Galaxy Research: "Predictions 2026 — Crypto, Bitcoin, DeFi"
- WEEX: "5 Best AI Agents in 2026"
- Crypto.news: "8 Leading AI Trading Bots for May 2026"

### Academic
- Taylor & Francis (2026): "Manipulation in Prediction Markets — An Agent-Based Modeling Experiment"
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

## Document History

| Version | Date | Changes |
|---|---|---|
| 1.0 | May 11, 2026 | Initial blueprint — complete research synthesis, architecture, roadmap |

---

*This document is the single source of truth for the Prophet project. All implementation decisions reference this blueprint. Update it as the system evolves.*
