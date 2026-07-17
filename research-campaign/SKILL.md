---
name: research-campaign
description: Run a disciplined strategy-discovery research campaign so its findings are trustworthy. Use when searching for a trading/quant strategy (or any noisy-signal discovery loop) and results must survive scrutiny — preregistered promotion manifests written before results exist, gauntlet + holdout gates, a priori kill criteria, and forward-paper validation with automated parity/reconcile checks before any promotion. Method only.
---

# Research Campaign — discovery you can trust

A strategy-discovery loop that searches many candidates will *always* find
something that looks good in-sample. The discipline that separates a real
finding from a lucky one is procedural, and it has to be set up **before** you
look at results. This skill is that procedure: preregister the bar, run every
candidate through one honest gauntlet, keep a sequestered holdout, declare kill
criteria in advance, and validate survivors in forward-paper before anything is
promoted.

The whole method exists to defeat one failure mode: **choosing the success
criterion after seeing which candidate you want to win.** Everything below makes
that impossible.

## 1. Preregister the promotion manifest (before any results exist)

Write a manifest — a versioned, committed document — that fixes the campaign's
rules **before running it**. Once committed it is **binding**: changing any bar
invalidates the campaign and starts a new one.

The manifest must state, a priori:

- **Campaign id and the seed hypothesis** — the specific family/idea being
  tested and why, in one falsifiable sentence.
- **The universe and windows** — the data, the train windows (span several
  regimes, including bad ones), and the **holdout window** (see §3).
- **The threshold set** — every numeric bar a candidate must clear, each with the
  **anchor that justifies it**. Anchor bars to references and controls (a
  buy-and-hold, a timed benchmark, the risk of a known index) and to the
  null distribution — **never to the measured winner.** A bar tuned to admit the
  candidate you already found is not a bar.
- **The search space** — the exact grid/parameter space. A session knob (plateau
  cap, iteration limit) must not silently shrink the declared space; if it does,
  that's a disclosed deviation, not a quiet truncation.
- **Success / failure interpretation** — what each possible outcome *means* and
  what it triggers, written now (see §5).

**Validate the bars themselves before launch**, and commit the evidence:

- **Positive control:** sane reference strategies (index hold, EW basket, a
  timed benchmark) must **pass** the bars, and a deliberately weak reference must
  **fail**. This catches both failure modes of bar design — unpassable bars, and
  bars fitted to the winner.
- **Null calibration:** run ~20 skill-free / randomized candidates through the
  full gauntlet on these exact bars. Expect **0/20** to pass. If nulls pass, the
  gauntlet can't tell skill from luck — fix it before running the real campaign.

## 2. One gauntlet for every candidate

Every candidate goes through the **same** evaluation pipeline — no hand-promotion,
no side doors. The gauntlet must include all of:

- **Point-in-time, survivorship-complete data** (delisted names included).
- **Honest per-name costs** (spread/impact + short borrow under stress), not
  flat-bps or zero.
- **A variance-aware baseline gate** — beat a benchmark/control by a margin that
  accounts for noise, not just by a point estimate.
- **Multiple train windows** spanning regimes, plus **leakage checks** (0
  violations).
- **Null-calibrated pass bars** — the bars validated in §1.

Score candidates so that **progress through gates is measurable** (credit each
gate cleared), so a plateau counter measures real stalling rather than
misfiring while coverage of the declared space is still incomplete.

Decouple expensive arms where possible: run the cheap mechanical evaluation
first, and only spend the expensive resource (an LLM overlay, a slow simulation)
on candidates whose cheap twin already clears the absolute bars. Dead candidates
should cost nothing.

## 3. Holdout discipline

- The holdout is **strictly forward of all selection data** (and, for
  model-driven work, after the model's knowledge cutoff), and **untouched by
  every experiment** until a candidate has passed selection.
- It carries a **touch budget** (e.g. ≤3 evaluations, median-of-replications).
  Spend a touch only on a selection survivor.
- **No re-rolls.** A holdout failure after a selection pass is an
  overfit-to-train verdict: record the death, decrement the budget, move on.
  Tuning-and-retrying against the holdout destroys it.

## 4. Kill criteria, declared in advance

Before launch, write the conditions under which the campaign (or a candidate)
**dies**, so no result is kept alive by hope:

- **Excluded families/regions** are enforced in state; drifting into one **pauses
  for human review** rather than silently exploring off-plan.
- **A priori outcome branches** (§5) — including "this whole basin is dead" — are
  named now, each pointing to either a clean stop or a *new* preregistration
  (never a threshold edit on the current one).
- A budget cap (compute/credits/time) that pauses cleanly and resumes, so cost
  never pressures a premature "good enough."

## 5. Declare what each outcome means (a priori)

Write the interpretation of every outcome before you have it:

- **Survivor through selection + holdout** → the first validated finding on
  honest foundations → it earns a forward-paper bridge (§6). Nothing skips
  straight to production.
- **Mechanically viable but the expensive overlay adds nothing** → the finding is
  "the mechanical strategy is the alpha; the overlay is null" — promote the
  mechanical strategy to forward-paper and record the overlay null honestly.
  (Make your pipeline able to *represent* this verdict — it's a real and common
  result.)
- **All deaths at the first gate** → the basin doesn't survive honest
  constraints → trigger a *new* preregistered branch (a different family, an
  engine capability you don't yet have), not a softened bar here.
- **Holdout failure after a selection pass** → overfit-to-train; candidate dies.

## 6. Forward-paper validation before promotion

A selection+holdout survivor is a *candidate for forward paper*, not a production
strategy. Run it **paper-only, live-forward** and gate production promotion on
pre-registered forward criteria:

- **Pre-register graduation/kill criteria for the paper run**: a minimum number
  of trading days AND completed round-trips before it can be graded, plus
  drawdown and divergence limits that retire it early.
- **Automated parity / reconcile checks**: every session, reconcile the paper
  book against an independent broker/mirror computation and flag divergence. A
  strategy whose live behavior diverges from its own model spec is not ready,
  whatever its P&L. Watch for calendar-aware staleness (weekends/holidays are not
  a stalled feed) and partial-fill handling, which are common sources of false
  divergence.
- **Grade against the benchmark/control sleeves** (index-hold, cash,
  random-entry matched to risk) once the minimums are met. Retire anything that
  loses to buy-and-hold-or-cash on risk-adjusted terms.
- Only a paper survivor that clears its pre-registered forward criteria is
  eligible for production — and **make production unreachable by any other
  path**, so nothing gets hand-promoted around the gauntlet.

## Standing checklist

1. Write + commit the preregistration manifest (id, hypothesis, universe,
   windows, bars-with-anchors, search space, outcome branches). It's binding.
2. Commit positive-control + null-calibration evidence for the bars (nulls 0/20).
3. Run every candidate through the one gauntlet (PIT/survivorship data, honest
   costs, variance-aware baseline, null-calibrated bars).
4. Touch the sequestered holdout only for selection survivors, within budget,
   no re-rolls.
5. Interpret the outcome by the a-priori branch; a dead basin triggers a *new*
   prereg, not a bar edit.
6. Forward-paper survivors with pre-registered graduation/kill criteria and
   automated parity/reconcile checks; grade against benchmarks; promote only
   through this path.
