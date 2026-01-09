# “fully-fledged autonomous research system” idea

What I want:

> build → choose symbols → choose intervals → backtest → review → expand → optimize → iterate

This **is doable**, but with **constrain agency**.

---

### Idea: “The system should choose symbols & intervals by itself”

Partially correct — but not blindly.

#### Correct approach

The system should choose **candidates**, not roam freely.

That choice must be:

* Spec-driven
* Hypothesis-driven
* Budgeted

Example:

Spec metadata:

```json
{
  "style": "mean_reversion",
  "holding_period": "short",
  "volatility_preference": "high",
  "market_type": "equities"
}
```

From this, rules (code, not LLM):

* Mean reversion → lower TFs first
* Short holding → avoid daily
* High vol → prefer mid-cap / volatile names

LLM:

* Ranks symbol candidates
* Explains why expansion makes sense

Code:

* Executes
* Enforces budget
* Stops explosion

---

### Idea: “System should detect sector/industry edge”

This is reasonable — but subtle.

Do **not** let the LLM discover this from raw PnL.

Instead:

* You compute performance by sector
* You compute stability across symbols
* You pass *aggregates* to LLM

LLM answers:

* “Is this concentration meaningful or noise?”
* “Should we expand or constrain universe?”

---

## Key correction

> “More autonomy = better research”
That’s false.

**Better constraints = better research**.

Autonomy without:

* gates
* budgets
* invariants

just accelerates overfitting.

The design is *good* — but only if:

* LLMs reason
* Code enforces
* Specs constrain


# 1. The architecture / workflow

What you will be building is a **closed-loop research system with constrained autonomy**.

### High-level loop (single sentence)

> **LLM proposes intent → deterministic system executes → deterministic gates judge → LLM reasons about next move → system enforces limits**

### Expanded workflow (step-by-step)

```
┌────────────────────────────┐
│ 1. User Strategy Idea      │
│    (text / pseudo / Pine)  │
└─────────────┬──────────────┘
              ↓
┌────────────────────────────┐
│ 2. Translator Agent (LLM)  │
│    - Extract intent        │
│    - Normalize logic       │
│    - Classify strategy     │
└─────────────┬──────────────┘
              ↓
┌────────────────────────────┐
│ 3. Strategy Spec (JSON)    │
│    - Declarative           │
│    - Versioned             │
│    - Immutable intent      │
└─────────────┬──────────────┘
              ↓
┌────────────────────────────┐
│ 4. Compiler (deterministic)│
│    - Spec → Base subclass  │
│    - Indicator wiring      │
│    - Param validation      │
└─────────────┬──────────────┘
              ↓
┌────────────────────────────┐
│ 5. Research Director       │
│    (hybrid: code + LLM)    │
│    - Select symbols        │
│    - Select intervals      │
│    - Enforce budgets       │
└─────────────┬──────────────┘
              ↓
┌────────────────────────────┐
│ 6. Execution Engine        │
│    (your current system)  │
│    - Download data (if req)│
│    - Run backtest          │
│    - Produce metrics       │
└─────────────┬──────────────┘
              ↓
┌────────────────────────────┐
│ 7. Reviewer (deterministic)│
│    - Hard gates            │
│    - Reject garbage early  │
└─────────────┬──────────────┘
              ↓
┌────────────────────────────┐
│ 8. Reviewer (LLM layer)    │
│    - Diagnose behavior     │
│    - Match intent vs result│
└─────────────┬──────────────┘
              ↓
┌────────────────────────────┐
│ 9. Director Decision       │
│    - Expand universe?      │
│    - Change timeframe?     │
│    - Optimize params?      │
│    - Kill strategy?        │
└─────────────┬──────────────┘
              ↓
        (loop or terminate)
```

**Key rule:**
👉 *Only steps 2, 8, 9 involve LLMs, and 5 hybrid code-LLM*
Everything else is deterministic and auditable.

---

# 2. Constraints: gates, budgets, invariants (this is the core)

Without these, autonomy = self-delusion at scale.

## A. Gates (binary kill switches)

Gates are **non-negotiable**.
If a gate fails → **strategy dies immediately**. No reasoning, no optimization.

### Example gate categories

#### 1. Statistical viability gates

```text
min_trades_per_year ≥ 100
max_drawdown ≤ 25%
avg_trade_return ≥ 0.2%
```

#### 2. Distribution sanity gates

* Top 5 trades contribute ≤ X% of total PnL
* No single day/week dominates equity curve
* Trade spacing not absurdly clustered

#### 3. Robustness gates

* Performance does not collapse (>50%) across:

  * train / test
  * first half / second half
  * random subsample

#### 4. Complexity gates

* Max indicators: e.g. 5
* Max conditions per side: e.g. 6
* Max parameters optimized: e.g. 6

If any gate fails:

```
status = DEAD
reason = <which gate failed>
```

LLM is **not consulted** here.

---

## B. Invariants (rules that must *never* be violated)

Invariants protect you from silent research corruption.

### Examples (non-exhaustive)

* Strategy logic cannot change after first review
  (only parameters may change)
* Indicators cannot be added after initial compile
* Timeframe changes must follow allowed ladder (e.g. 5m → 15m → 1h)
* Optimization cannot start until OOS pass
* Reviewer cannot approve strategy it didn’t reject first

Think of invariants as **constitutional law**.

---

## C. Budgets (this is where most people fail)

Budgets limit **exploration**, not quality.

### Core insight

> You don’t prevent overfitting by being smart.
> You prevent it by **running out of budget before nonsense explodes**.

---

# 3. Research budget system (anti-combinatorial-explosion)

This is the most important part of your question.

## A. What causes combinatorial explosion?

Let’s be explicit:

* Symbols ×
* Timeframes ×
* Parameter combinations ×
* Regimes ×
* Re-runs after optimization

Without limits, this grows **exponentially**.

---

## B. Introduce a “research currency”

Every action **costs credits**.

### Example budget model

```python
TOTAL_BUDGET = 1_000 credits
```

### Cost table (example)

| Action                            | Cost |
| --------------------------------- | ---- |
| Initial backtest (1 symbol, 1 TF) | 10   |
| Add new symbol                    | 5    |
| Add new timeframe                 | 8    |
| Parameter optimization run        | 20   |
| Walk-forward test                 | 25   |
| Regime expansion                  | 15   |
| Re-optimization                   | 30   |

---

## C. Director must justify spending budget

Before an action, the **Director Agent** must produce:

```json
{
  "action": "expand_symbol_universe",
  "cost": 25,
  "expected_information_gain": "validate sector robustness",
  "justification": "strategy shows stable behavior in 3/5 stocks of same sector"
}
```

Then:

* Code checks budget
* Action executes
* Budget decremented
* Decision logged

If budget exhausted → strategy frozen.

---

## D. Budget reset rules (important)

You do **not** reset budget on:

* Minor metric improvement
* Optimization success
* Better Sharpe

You **may** reset or extend budget only if:

* Strategy passes all gates
* Shows stability across *new dimension* (e.g. sector)
* Director explicitly promotes it to “candidate library”

This forces **promotion discipline**.

---

# 4. How autonomy actually works (corrected intuition)

Wanted:

> “full-fledged autonomous research”

Here’s the corrected version:

* LLMs **hypothesize**
* Code **tests**
* Gates **kill**
* Budgets **limit**
* Invariants **protect**
* LLMs **interpret**
* Director **chooses next experiment**
* System **stops itself**

That’s autonomy **with brakes**.

---

# 5. points to note

### 1.
LLM should not explore widely to find hidden edges.
Edges emerge from **constraint-guided exploration**, not randomness.

---

### 2.
Optimization should not be aggressive once something works.
Optimization is where most strategies die *quietly*.

---

### 3.
> “If LLM explains it well, it’s probably real”
This narrative is cheap.
Stability is expensive.

---

# 6. Current system is already 70% there

Already have:

* A clean `Base` class
* Deterministic execution
* Optimization hooks
* Indicator separation

What you’re adding is **governance**, not magic.

---

## Final distilled blueprint

* **Architecture**: Spec-driven, engine-isolated, loop-controlled
* **Gates**: Binary, harsh, early
* **Invariants**: Constitutional, never overridden
* **Budgets**: Credit-based, action-priced
* **LLMs**: Reason, decide, explain — never measure or execute
