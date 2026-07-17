#!/usr/bin/env bash
# TEMPLATE — adapt the marked sections, keep the contract intact.
# Checklist-style secure intake: menu (resume/start-over/view/specific/quit),
# skippable prompts, silent secret entry, masked status, validate-then-save,
# mode-600 target, apply-on-change.
set -euo pipefail

# ── ADAPT: target file + what "apply" means ─────────────────────────────────
ENV_FILE="$HOME/.config/example-app/secrets.env"
apply_changes() {
  # e.g.: docker compose -f ... restart <service>; systemctl --user restart <unit>
  :
}
post_apply_status() {
  # e.g.: docker exec <container> <status command>
  :
}
# ── ADAPT: items — letter, label, env key, secret?, then a fill_X below ─────
LETTERS=(A B)   # extend: (A B C D E ...)

CHANGED=0
bold() { printf '\033[1m%s\033[0m\n' "$*"; }
ok()   { printf '  \033[32m✔\033[0m %s\n' "$*"; }
bad()  { printf '  \033[31m✘\033[0m %s\n' "$*"; }
note() { printf '  \033[33m•\033[0m %s\n' "$*"; }

[ -f "$ENV_FILE" ] || { bad "$ENV_FILE not found"; exit 1; }

get_env() { grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2- || true; }

set_env() { # KEY  (value via NEWVAL env var, never argv)
  python3 - "$ENV_FILE" "$1" <<'PY'
import sys, os
path, key = sys.argv[1], sys.argv[2]
value = os.environ["NEWVAL"]
lines = open(path).read().splitlines()
out, done = [], False
for ln in lines:
    if ln.startswith(key + "="):
        out.append(f"{key}={value}"); done = True
    else:
        out.append(ln)
if not done:
    out.append(f"{key}={value}")
open(path, "w").write("\n".join(out) + "\n")
PY
  chmod 600 "$ENV_FILE"
  CHANGED=1
}

mask() {
  local v="$1"
  if [ -z "$v" ]; then echo "(not set)"
  elif [ ${#v} -le 8 ]; then echo "set (hidden)"
  else echo "${v:0:5}…${v: -3} (hidden)"
  fi
}

# ── ADAPT: status lines, one per item; mask every secret ────────────────────
item_status() {
  printf "  A) Example API key            %s\n" "$(mask "$(get_env EXAMPLE_API_KEY)")"
  printf "  B) Example plain setting      %s\n" "$(get_env EXAMPLE_SETTING)"
}

# ── ADAPT: is_set per item ───────────────────────────────────────────────────
is_set() {
  case "$1" in
    A) [ -n "$(get_env EXAMPLE_API_KEY)" ] ;;
    B) [ -n "$(get_env EXAMPLE_SETTING)" ] ;;
  esac
}

# ── ADAPT: one fill_X per item. Secrets: read -r -s. Validate, then save. ───
fill_A() {
  bold "A) Example API key (where to get it)"
  while true; do
    read -r -s -p "   Key (Enter to skip): " KEY; echo
    [ -z "$KEY" ] && { note "skipped — asked again next run"; return 0; }
    # Live validation here; on success save, on failure loop:
    NEWVAL="$KEY" set_env EXAMPLE_API_KEY; ok "saved"; return 0
  done
}

fill_B() {
  bold "B) Example plain setting"
  local cur; cur=$(get_env EXAMPLE_SETTING)
  read -r -p "   Value [${cur:-none}] (Enter keeps/skips): " V
  [ -z "$V" ] && { note "unchanged"; return 0; }
  NEWVAL="$V" set_env EXAMPLE_SETTING; ok "saved"
}

# ── Generic machinery below: usually no changes needed ──────────────────────
run_items() { local L; for L in "$@"; do "fill_$L"; echo; done; }

finish() {
  if [ "$CHANGED" = 1 ]; then
    bold "Applying changes..."
    apply_changes
    post_apply_status || true
  else
    note "Nothing changed; nothing restarted."
  fi
  local missing=() L
  for L in "${LETTERS[@]}"; do is_set "$L" || missing+=("$L"); done
  echo
  if [ ${#missing[@]} -eq 0 ]; then bold "All items are set."
  else bold "Still missing: ${missing[*]} — run this again any time to continue."; fi
}

while true; do
  bold "Secure intake — setup"
  echo "  1) Pick up where I left off (ask only for missing items)"
  echo "  2) Start over (walk through every item; Enter keeps existing values)"
  echo "  3) View the item list and what's already assigned"
  echo "  4) Fill specific items (e.g. 'A C')"
  echo "  q) Quit"
  read -r -p "Choice: " choice
  echo
  case "$choice" in
    1)
      todo=(); for L in "${LETTERS[@]}"; do is_set "$L" || todo+=("$L"); done
      if [ ${#todo[@]} -eq 0 ]; then ok "Nothing missing — every item is assigned."; echo
      else run_items "${todo[@]}"; fi
      finish; exit 0 ;;
    2) run_items "${LETTERS[@]}"; finish; exit 0 ;;
    3) item_status; echo ;;
    4)
      read -r -p "Which items (letters separated by spaces): " picks
      sel=(); for L in $picks; do
        U=${L^^}
        if printf '%s\n' "${LETTERS[@]}" | grep -qx "$U"; then sel+=("$U"); else bad "Unknown item: $L"; fi
      done
      [ ${#sel[@]} -gt 0 ] && { echo; run_items "${sel[@]}"; finish; exit 0; }
      echo ;;
    q|Q) exit 0 ;;
    *) bad "Pick 1, 2, 3, 4, or q"; echo ;;
  esac
done
