# agent-skills

A portable, harness-neutral collection of **agent skills** — self-contained
folders that teach an AI coding agent how to do a specific job well, with the
deterministic scripts and checklists to do it reliably.

Each skill is a directory with a `SKILL.md` (YAML front-matter naming the skill
and describing when to use it) plus any `scripts/` or `references/` it needs. The
format is deliberately plain markdown + stdlib scripts so it works across
harnesses (Claude Code, Codex, and anything that can read a file), not just one
vendor's tooling.

These were extracted and genericized from a working single-operator homelab, then
scrubbed of anything machine-specific so a stranger with none of that
infrastructure can pick them up. Paths are placeholders (`$VAULT_PATH`,
`~/.config/...`) you point at your own setup.

## Skills

| Skill | What it does |
| --- | --- |
| [`obsidian-vault`](obsidian-vault/) | Manage an Obsidian vault with an agent: keep every note reachable from a Table of Contents through domain hubs (verified by a link-check script), and color-code the graph / grow the taxonomy deterministically. |
| [`secure-intake`](secure-intake/) | Never accept secrets in chat. Generate a checklist-style interactive terminal script for the user to enter API keys / passwords, and verify by presence/behavior — never by printing values. |
| [`standing-artifact`](standing-artifact/) | Maintain a recurring report at one stable published URL: republish-to-same-URL discipline, an append-only ledger of runs, and a headless→interactive publish handoff. |
| [`backtest-audit`](backtest-audit/) | A checklist for auditing a trading model / backtest before trusting it: lookahead & hindsight-mining detection, survivorship bias, dividend adjustment, exit-geometry artifacts, costs, multiple-testing, and holdout discipline. |
| [`research-campaign`](research-campaign/) | Run a strategy-discovery campaign whose findings survive scrutiny: preregistered promotion manifests, one gauntlet + sequestered holdout, a-priori kill criteria, and forward-paper validation with automated parity/reconcile checks. |
| [`worktree-deploy-hazard`](worktree-deploy-hazard/) | Avoid silently breaking production when a git checkout doubles as a live deploy source — use `git worktree` for parallel work instead of `git checkout`, and flag deploy-coupled checkouts in project docs. |

## Install

Clone the repo and run the installer. It symlinks each skill folder into your
agent skill directories (`~/.claude/skills/` and `~/skills/` by default),
creating them if missing and never clobbering a real directory:

```bash
git clone https://github.com/dyuhaus/agent-skills.git
cd agent-skills
./install.sh                      # install into the default targets
./install.sh --targets ~/.claude/skills   # or a specific directory
./install.sh --dry-run            # preview without changing anything
./install.sh --uninstall          # remove only the symlinks it created
```

The installer is idempotent: re-running it is a no-op for already-linked skills,
it skips (with a warning) any symlink pointing elsewhere unless you pass
`--force`, and it never removes a real file or directory.

Skills that ship scripts (`obsidian-vault`) use only the Python 3 standard
library — no dependencies to install. Point them at your own vault via the
`VAULT_PATH` environment variable or `--vault` flag, as documented in each
skill's `SKILL.md`.

## Companion project

For the two-model development method these skills were built alongside —
planning with a reasoning model and building with a coding model, configured as a
portable primitive — see [`dyuhaus/dev-primitive`](https://github.com/dyuhaus/dev-primitive).

## License

MIT © 2026 David Yuhaus. See [LICENSE](LICENSE).
