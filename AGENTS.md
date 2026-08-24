# agent-skills — Agent Guide

This repository is model- and harness-agnostic. `AGENTS.md` is the portable
entrypoint for Codex, Hermes, Claude Code, and any future assistant harness.

## Project

Portable, harness-neutral agent skills: Obsidian vault management, secure secret
intake, standing artifacts, and quant research rigor.

Layout: each top-level folder is one skill — a `SKILL.md` (YAML front-matter:
`name`, `description`) plus optional `scripts/` (Python 3 stdlib only) and
`references/`. `install.sh` symlinks the skill folders into agent skill
directories. There is no build step; scripts have no third-party dependencies.
Keep every skill genericized and free of machine-specific paths or private data
(this repo is public — use placeholders like `$VAULT_PATH`).

## Rules

- **Maintainer machine only:** if this checkout lives under `/home/dyadmin`,
  read `/home/dyadmin/AGENTS.md` first — that is the machine-level contract and
  it outranks this file. It is not present on a fresh clone, and its absence is
  not an error; skip this rule if the file does not exist. (Without it, a
  harness whose instruction loader is bounded by the repo root runs here with
  zero standing rules.)
- Read this repo's `README.md`, manifests, scripts, and tests before changing
  behavior.
- Never read, print, commit, or publish secrets, local `.env` values,
  credentials, or private user data.
- Keep durable state in repo files and deterministic scripts, not in one
  harness's memory or chat history.
- Use the project's native test/build commands for validation; document any
  missing or unavailable checks.

## Git Workflow
- Default branch: main (protected, PR-only, squash merge)
- Branches: feat/ fix/ chore/ docs/ exp/ (+ agent/<harness>/ optional)
- Commits: Conventional Commits; hooks must pass; never --no-verify
- Review: BEFORE opening a PR, get an adversarial branch review from something
  that did not write the code, using the active harness's native mechanism;
  address every finding. Docs-only diffs may record `docs-only, no review`.
- Merge: routine reviewed agent PRs may be machine-merged; deploy-coupled or
  unreviewed PRs go to David through the approval relay.
- Deploy coupling: none (this repo ships skill files; nothing is deployed on merge)
- Long-lived branch exceptions: none
