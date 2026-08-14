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
- Review: run `/code-reviewer` (the code-reviewer specialist, on `fable`)
  before opening a PR — since CodeRabbit's removal on 2026-07-29 it is the
  only review a PR gets; then request David's approval (agent PRs require it)
- Deploy coupling: none (this repo ships skill files; nothing is deployed on merge)
- Long-lived branch exceptions: none
