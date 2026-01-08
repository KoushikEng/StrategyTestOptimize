# AI closed-loop trading strategies research system

## The correct mental model

You’re building a **closed-loop research system**, not “adding AI”.

This is closer to:

> AutoML + compiler + QA + optimizer
> Than:
> ChatGPT writes strategies

---

## High-level architecture (what actually works)

```txt
┌─────────────┐
│ User Input  │  ← text / pseudocode / PineScript
└─────┬───────┘
      ↓
┌──────────────────┐
│ Strategy Parser  │  (LLM)
│ - Extract rules  │
│ - Normalize idea │
└─────┬────────────┘
      ↓
┌──────────────────┐
│ Strategy Builder │  (LLM + templates)
│ - Python code    │
│ - Indicator code │
│ - Constraints    │
└─────┬────────────┘
      ↓
┌──────────────────┐
│ Execution Layer  │  (deterministic)
│ - Backtest       │
│ - Error logs     │
│ - Metrics        │
└─────┬────────────┘
      ↓
┌──────────────────┐
│ Reviewer Agent   │
│ - Read metrics   │
│ - Spot pathologies
│ - Reject garbage │
└─────┬────────────┘
      ↓
┌──────────────────┐
│ Optimizer Agent  │
│ - Param bounds   │
│ - Regime tests   │
│ - Penalize BS    │
└─────┬────────────┘
      ↓
┌──────────────────┐
│ Gatekeeper       │
│ - Accept / reject
│ - Archive logic  │
└──────────────────┘
```

**Only one place touches real money logic:**
👉 the execution layer (pure Python, no LLM).

---

## Agent roles (THIS is critical)

### 1. Strategy Translator Agent

**Input**

* Plain English
* Pseudocode
* PineScript

**Output**

* A *formal, machine-readable strategy spec*

Example:

```json
{
  "entry": [
    "ema_fast > ema_slow",
    "rsi < 30"
  ],
  "exit": [
    "rsi > 60",
    "stoploss = 1.5 * atr"
  ],
  "timeframe": "5m",
  "filters": ["session != asia"]
}
```

This agent **does NOT write code**.
It produces **intent**, not implementation.

---

### 2. Strategy Compiler Agent

Takes the spec and:

* Maps to your backtest API
* Writes indicator functions if missing
* Enforces *your* framework rules

This agent is **sandboxed**:

* No creativity
* No “clever” logic
* Only allowed constructs

Think of it like a **DSL compiler**.

---

### 3. Debug / Repair Agent

Triggered only if:

* Python throws
* NaNs
* No trades
* Lookahead detected

It reads:

* Stack traces
* Logs
* Data shapes

And produces:

* Minimal diffs
  Not rewrites.

---

### 4. Strategy Reviewer Agent (MOST IMPORTANT)

This one is **hostile**.

It asks:

* Is win rate fake?
* Is trade count too low?
* Are returns coming from 2 trades?
* Does performance collapse OOS?

If yes → **reject**, no optimization allowed.

---

### 5. Optimizer Agent (optional but powerful)

Only runs if reviewer approves.

Rules:

* Bounded parameters only
* Penalize:

  * Drawdown
  * Trade clustering
  * Sensitivity
* Enforce:

  * Minimum trades
  * Stability across splits

This agent **never edits logic**, only parameters.

---

## Fitness function (don’t screw this up)

You already sensed this earlier, so let me be blunt:

### Sharpe is trash for what you want

A sane composite:

```txt
score =
  CAGR
- α * max_drawdown
+ β * win_rate
- γ * parameter_sensitivity
- δ * equity_curve_entropy
```

Add **hard gates**, not soft penalties:

* min trades per year
* min avg R multiple
* max DD %

If a gate fails → score = -∞

---

## TradingView PineScript input (important)

DO NOT try to convert Pine → Python directly.

Correct flow:

1. LLM extracts **logic**, not syntax
2. You re-express logic in your system
3. Ignore:

   * repainting
   * security() calls
   * barstate tricks

Otherwise you’ll import garbage strategies.

---

## Tools / frameworks (no hype)

* **LLM orchestration**:

  * LangGraph

* **Execution**:

  * Pure Python + NumPy/Numba
  * Zero LLM involvement

* **Search**:

  * Bayesian optimization / CMA-ES
  * Not “LLM guessing numbers”

---

## Failure modes you MUST guard against

1. **Self-confirming loops**
   Agent optimizes → reviews itself → approves trash

2. **Strategy bloat**
   More indicators ≠ better
   Enforce max complexity

3. **Regime overfitting**
   Always test:

   * trend
   * chop
   * volatility spikes

4. **Narrative seduction**
   Agent explains why it “makes sense”
   → explanation ≠ edge

Kill any strategy that sounds smart but behaves fragile.

## Recommended architecture (clean, scalable)

### 1. Convert existing project into a **pure engine**

Minimal changes:

* Keep:

  * `main.py`
  * `optimize.py`
  * `indicators/`
  * `strategies/Base.py`
* Treat it as:

  > a deterministic research engine

---

### 2. Add a separate layer: `research_agent/`

```
research_agent/
├── translator.py      # text / pine → spec
├── spec_schema.py     # validation rules
├── compiler.py        # spec → Strategy class
├── reviewer.py        # metrics sanity checks
├── optimizer.py       # param search (calls optimize.py)
├── runs/
│   ├── specs/
│   ├── logs/
│   └── results/
```

This layer:

* Imports your engine
* Never modifies it
* Treats it as a black box

---

### 3. How they interact (very important)

```txt
User text
   ↓
Translator Agent
   ↓
Spec JSON  ← persisted, versioned
   ↓
Compiler
   ↓
Generated strategy class (temporary)
   ↓
Your existing backtest engine
   ↓
Metrics
   ↓
Reviewer / Optimizer
```

If the agent goes insane, **your engine remains sane**.

---

