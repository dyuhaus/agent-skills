---
name: secure-intake
description: Build an interactive terminal script for the user to enter secrets or private values that the agent must never see (API keys, passwords, tokens, credentials, .env values). Use whenever a task needs the user to supply sensitive input — never ask for secrets in chat; generate a checklist-style intake script instead, and verify by presence/behavior rather than by printing values.
---

# Secure Intake — collecting values the agent shouldn't see

When a task requires the user to provide secrets (API keys, app passwords,
tokens, webhook signing keys, any credential or private value), do NOT ask for
them in the conversation. Anything typed into chat lands in the transcript on
disk. Instead, generate an interactive intake script the user runs in a plain
shell, then verify the *result* (service reachable, mode changed, file
populated) without ever reading the secret values back.

## Procedure

1. **Enumerate the items.** List every value needed: a letter (A, B, C…), a
   human label, the destination (env file key, config field), whether it is
   secret (silent input + masked display) or plain, and how to validate it
   live if possible (an API ping, a login attempt, a regex).
2. **Generate the script** from `template.sh` in this skill's directory.
   Adapt: the `ENV_FILE` target, the items table, per-item `fill_X`
   validators, and the `apply_changes` hook (restart a service, re-run a
   deploy — whatever makes the new values take effect).
3. **Install it** somewhere on the user's PATH (`~/bin/<name>-setup`), make it
   executable, `bash -n` it, and test the non-secret menu paths
   non-interactively (e.g. `printf '3\nq\n' | bash <script>`) against a COPY
   of the target file — never run write-paths against the real target in
   testing.
4. **Tell the user** to run it in a normal shell session, and explicitly warn
   them not to paste the secrets into chat. Afterward, verify outcomes only
   (service status, "mode: active", HTTP 200s) — never `cat` the secrets.

## Required script behavior (the contract)

- **Opening menu**: 1) Pick up where I left off (ask only missing items),
  2) Start over (every item; Enter keeps existing), 3) View item list with
  assignment status, 4) Fill specific items by letter, q) Quit.
- **Every prompt skippable** with Enter; a skipped item stays unset and is
  asked again on the next "pick up where I left off" run.
- **Secrets**: `read -r -s` (no echo), passed to helpers via environment
  variables — never argv (argv is visible in `ps` and shell history).
- **Status display masks secrets**: show `(not set)` / `set (hidden)` /
  first-5…last-3 for long keys. Never print a full secret.
- **Validate before saving** when a live check exists; on failure re-prompt,
  with Enter always available as the escape hatch.
- **Dependencies**: if item C needs item B (e.g. password needs username),
  detect and say "needs item B first" instead of failing the validation.
- **Target file** written atomically per key, kept at mode 600.
- **Apply only on change**: track a CHANGED flag; restart/reload only if
  something was written, and report it. Exit by listing still-missing items.

## After the script runs

Check only derived state: service status output, a health endpoint, an API
"mode" field. If validation must happen later (the user filled items while
the agent wasn't running), the script's own validators already covered it.

## Worked example (what the template becomes)

A filled-in script typically has items A–E: an API key (validated by a live
authenticated ping to the provider), a service username + password pair (item C
depends on item B; password validated by an actual login attempt), a plain
setting, and an `apply_changes` hook that restarts the service
(`systemctl --user restart <unit>` or `docker compose restart <service>`) only
when something changed. `template.sh` in this directory is that pattern with the
adaptable sections marked `── ADAPT ──`; the machinery below those markers
usually needs no changes.
