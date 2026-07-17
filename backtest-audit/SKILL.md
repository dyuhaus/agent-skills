---
name: backtest-audit
description: Audit a trading model or backtest before trusting its results. Use before promoting, funding, or relying on any strategy backtest — a checklist for detecting lookahead/hindsight mining, survivorship bias, missing dividend adjustment, exit-geometry artifacts, optimistic costs, multiple-testing inflation, and holdout discipline. Method and how-to-test guidance only; no strategy specifics.
---

# Backtest Audit — before you trust a backtest

A backtest that looks spectacular is usually lying, and the ways it lies are
finite and well-known. This is a checklist for auditing a trading model or
backtest before you promote it, fund it, or trust its number. Work top to
bottom; a single un-cleared item is enough to disqualify a headline result.

The mindset: **a backtest is a claim about the future made from the past, and
almost every failure is some form of the past leaking information it wouldn't
have had in real time.** Your job is to find the leak.

## Tell-tale signs (triage first)

If any of these are present, treat the result as suspect until proven otherwise:

- **Absurd compounding** — turning a tiny stake into an enormous one in a short
  window on few trades. Astronomical returns are a symptom, not an achievement.
- **No out-of-sample split, no benchmark, no costs** stated anywhere.
- **The rule was authored after seeing the period it's tested on** ("the switch
  fires every August" — written after observing an August failure).
- **A pass that barely clears the bar** (e.g. reliability 75.3 against a 75.0
  floor) after a large search — that's the search finding noise at the threshold.

## The audit checklist

### 1. Lookahead / hindsight mining

The cardinal sin: the strategy uses information not available at decision time.

- **Point-in-time data.** Every input at bar *t* must have been knowable at *t* —
  no restated fundamentals, no as-of-today index membership, no future bars in an
  indicator window.
- **Decision/execution separation.** Signals computed on a bar's close must fill
  at the *next* bar's open (or later), never at the same close. Same-bar fills are
  a common silent lookahead.
- **Hindsight oracle paths.** Beware a "strategy" that is really a filter applied
  on top of a known-good trade path. If the trade sequence was selected with
  knowledge of outcomes and the rule just gates it, the backtest measures the
  oracle, not the rule.
- **Identity/memorization leakage (for LLM- or ML-driven selection).** A model
  that has seen the tickers/period can "recall" winners rather than reason.
  *Test:* run an anonymized variant (strip identifying labels) and a
  recall-probe; a large gap between identified and anonymized runs is
  memorization, not skill.

*How to test:* re-run the exact rules on a strictly point-in-time corpus and
watch the return collapse. The size of the collapse is the size of the leak.

### 2. Survivorship bias

If the universe only contains names that still exist, every result is inflated by
the losers you silently deleted.

- The universe must include **delisted, merged, and bankrupt names**, present
  during the window they traded and gone after.
- *Test:* run the strategy with and without the delisted-inclusive universe; the
  difference is the survivorship inflation. It is rarely small.

### 3. Dividend / corporate-action adjustment

- Prices must be **total-return / dividend-adjusted** (and split-adjusted), or
  long strategies systematically understate drawdowns and overstate/misstate
  returns, and short strategies ignore the dividends they'd owe.
- Watch for **ticker-reuse and splice anomalies** (a symbol reassigned to a
  different company, bad split flags) that create phantom gaps or jumps.

### 4. Costs and turnover

- **Optimistic costs are the biggest single inflator after lookahead.** Flat
  low-bps or zero costs can add tens of points of fake return; honest per-name
  costs (spread + impact + borrow for shorts) are often 5–10× worse.
- Model **per-name, not per-portfolio** costs, and include short **borrow fees
  under stress**, not just general-collateral rates.
- Stress the cost assumption (e.g. 1.5×) and require the edge to survive it. A
  strategy that only works at zero cost doesn't work.
- High turnover multiplies every cost error — check trades-per-period.

### 5. Exit-geometry artifacts

A high win-rate can be manufactured entirely by the *shape* of the exits, with no
predictive entry edge at all.

- The pattern to catch: **a run of "true positives" that are an exit-geometry
  artifact** — e.g. wide take-profit + tight stop + short hold produces a stream
  of small wins with a near-breakeven expectancy once the occasional large loss
  and costs are counted. "5 for 5" means nothing if breakeven is ~97%.
- *Test:* compute the **breakeven win-rate implied by the TP/SL/hold geometry**
  and compare it to the observed win-rate. If the strategy's win-rate is barely
  above the geometric breakeven, the "accuracy" is structural, not predictive.
- Also run a **random-entry control with the same exit geometry and risk
  profile.** If random entries produce a similar record, the exits — not the
  signal — are doing the work.

### 6. Multiple-testing / selection inflation

- A search over thousands of configurations with **no multiple-testing
  correction** and a first-past-the-post stop will surface noise that clears any
  fixed bar. Count the trials.
- Require a **null calibration**: run many skill-free / randomized candidates
  through the *exact same* selection gauntlet and measure how many pass. If
  skill-free candidates pass at a meaningful rate, the gauntlet can't distinguish
  skill from luck, and neither can the headline result. A well-built gate passes
  ~0 of ~20 nulls.

### 7. Baselines, benchmarks, and controls

- Every result needs a **benchmark** (buy-and-hold of the relevant index) and a
  **cash baseline** to answer "is this alpha, beta, or noise?" A backtest with a
  `null` benchmark field is ungradable.
- Add a **random-entry control matched to the strategy's risk profile** as a
  first-class comparison, not an afterthought.

### 8. Holdout discipline

- Reserve a **sequestered holdout** window that is strictly forward of all
  selection data (and, for model-driven work, after the model's knowledge
  cutoff). It must be **untouched by every experiment** until the end.
- Give the holdout a **touch budget** (e.g. ≤3 evaluations) and spend it only
  after selection passes. Repeatedly peeking at the holdout turns it into
  another training set.
- **No re-rolls.** A holdout failure after a selection pass is an overfit-to-
  train verdict — record the death, decrement the budget, and stop; don't tune
  and retry.

## Verdict framing

State the result honestly:

- **Which items are un-cleared**, and the **measured inflation** each contributes
  where you could quantify it (the collapse when you re-ran on clean data).
- Whether the thing is a **validated edge**, a **clearly-labeled diagnostic /
  forward probe**, or a **benchmark/control** — never let a diagnostic be read as
  a validated edge.
- Remember the forward-record caveat: a handful of live sessions and a few dozen
  round-trips is **not statistically gradable** — don't over-read early P&L in
  either direction.
