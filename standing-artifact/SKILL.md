---
name: standing-artifact
description: Maintain a recurring report (status page, dashboard, digest) at a single stable published URL. Use when a report is refreshed on a cadence and the audience keeps a saved link — republish to the SAME URL, keep a ledger of runs, and use the headless→interactive publish handoff when a scheduled session can't publish. Running example is a weekly status report.
---

# Standing Artifact — one stable URL, many refreshes

A "standing artifact" is a report that gets **regenerated on a cadence but lives
at one permanent URL**, so whoever bookmarked it always sees the latest version.
The discipline that keeps it trustworthy is: always republish to the same URL,
keep a durable ledger of what each run did, and have a clean handoff for when the
session that generates the report can't publish it.

Running example throughout: a **weekly status report** — a page summarizing the
week's progress that a team keeps a standing link to.

## The three rules

### 1. Republish to the SAME URL (never mint a new one)

The audience's value comes from the link being stable. Every refresh must
redeploy to the existing artifact/page URL, not create a new one.

- **Record the canonical URL and identifiers in this skill** (or a sibling
  config file) so every run — including a fresh session with no memory of prior
  runs — targets the same destination.
- Keep the **publish identity stable** across refreshes: same title form, same
  favicon/icon, same slug. A changed icon or title reads as "a different page"
  to someone scanning their tabs.
- Treat "just give me the link" as a **distinct, no-rebuild request**: answer
  with the standing URL and the date of the last refresh. Only run the full
  regeneration when fresh content is actually wanted.
- **Mirror the last published bytes to a local file** (e.g. `live.html`) right
  after each publish, byte-identical to what went live. The next run then starts
  from ground truth instead of guessing what is currently deployed — essential
  when a run only tweaks part of the page.

### 2. Keep a ledger of runs

A standing artifact accumulates history that the live page itself does not show.
Maintain an append-only **ledger** (a markdown or CSV file under version control
or in a notes vault) so every run is accountable and future runs can diff
against the past.

- One entry per run: date, what changed, key counts/metrics, and a pointer to
  any archived full copy of that run's content.
- **Append-only** — never rewrite history. If a run supersedes an earlier one,
  add a new line saying so; don't edit the old line away.
- When the report's content is itself a rolling dataset (items that should each
  appear once, ever), the ledger is also the **dedupe key store**: read it
  before generating to exclude already-seen items, append newly included items
  after publishing. A run that skips the append silently breaks the guarantee
  for every later run.
- Each refresh's reply should say **what changed since the previous run** — the
  ledger (or the previous archived copy) is what you diff against.

### 3. The headless → interactive publish handoff

Scheduled/headless sessions (a cron job, a CI run, a timer) often **cannot
publish** to the hosting surface or reach interactive-only services. Don't let
that silently drop a refresh. Split the work:

**Headless run does everything except publish:**

1. Do all the real work: gather content, update the ledger, rebuild the page
   from its canonical template, and validate it (syntax-check any embedded
   script, render/screenshot it headless and actually inspect it).
2. Stage the verified page as a **pending-publish file**, e.g.
   `pending-publish-<YYYY-MM-DD>.html`. Do NOT overwrite the `live.html` mirror
   — that must keep reflecting what is *actually* live until the real publish
   happens.
3. Leave a **durable note** (a memory note, an issue, a checklist file) that
   says a publish is pending and lists anything else the headless session had to
   skip (e.g. a follow-up check that needs an interactive integration).

**Next interactive session finishes it:**

4. On finding a `pending-publish-*` file (or being asked to "publish the pending
   report"): publish it to the standing URL with the stable icon/title, copy the
   published bytes over `live.html`, delete the pending file, run any skipped
   steps the note listed, then clear the note.

This makes scheduled generation and interactive publishing two halves of one
reliable pipeline instead of a single point of failure.

## Rebuild discipline

- Rebuild from a **canonical template file that lives with the skill**, not from
  a session scratchpad — scheduled runs are fresh sessions with empty
  scratchpads. Keep the page **data-driven**: swap a data array / front-matter
  block and leave the presentation code untouched.
- **Validate before every publish**: syntax-check embedded scripts, and render
  the page (headless browser screenshot) and look at it. Layout regressions are
  invisible in the source and obvious in a screenshot.
- Preserve any **permanent features** the audience relies on (filters, saved
  state, toggles) across rebuilds — enumerate them so a rebuild never quietly
  drops one.

## Standing checklist per refresh

1. Link-only request? Reply with the standing URL + last-refresh date. Stop.
2. Read the ledger (and any dedupe keys). Gather fresh content.
3. Archive the run's content; append the ledger entry.
4. Rebuild from the canonical template; validate (syntax + rendered screenshot).
5. Publish to the SAME URL with stable icon/title. Mirror bytes to `live.html`.
6. If headless and unable to publish: stage `pending-publish-*`, leave the note,
   stop — an interactive session finishes it.
7. Report what changed since the previous run + the standing URL.
