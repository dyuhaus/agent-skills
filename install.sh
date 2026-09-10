#!/usr/bin/env bash
# install.sh — symlink each skill folder in this repo into your agent skill
# directories so an agent harness can discover them.
#
# Idempotent and safe:
#   - creates the target skill directories if missing
#   - (re)points a symlink we own to this repo's skill folder
#   - NEVER clobbers a real directory or a symlink pointing somewhere else
#     (it skips those with a warning; use --force to replace a foreign symlink,
#      but real directories are never removed)
#
# Usage:
#   ./install.sh                 # install into the default targets below
#   ./install.sh --targets DIR   # install into DIR only (repeatable)
#   ./install.sh --force         # replace symlinks that point elsewhere
#   ./install.sh --uninstall     # remove only the symlinks this repo installed
#   ./install.sh --dry-run       # print actions, change nothing
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default install targets. Override with one or more --targets DIR.
DEFAULT_TARGETS=("$HOME/.codex/skills" "$HOME/skills")
TARGETS=()
FORCE=0
DRY_RUN=0
UNINSTALL=0

while [ $# -gt 0 ]; do
  case "$1" in
    --targets) shift; [ $# -gt 0 ] || { echo "--targets needs a DIR" >&2; exit 2; }; TARGETS+=("$1") ;;
    --force)   FORCE=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --uninstall) UNINSTALL=1 ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done
[ ${#TARGETS[@]} -gt 0 ] || TARGETS=("${DEFAULT_TARGETS[@]}")

info() { printf '  %s\n' "$*"; }
run()  { if [ "$DRY_RUN" = 1 ]; then info "[dry-run] $*"; else eval "$*"; fi; }

# A folder is a skill if it contains SKILL.md.
mapfile -t SKILLS < <(
  for d in "$REPO_DIR"/*/; do
    [ -f "${d}SKILL.md" ] && basename "$d"
  done | sort
)
[ ${#SKILLS[@]} -gt 0 ] || { echo "No skill folders (with SKILL.md) found in $REPO_DIR" >&2; exit 1; }

for target in "${TARGETS[@]}"; do
  echo "Target: $target"
  if [ "$UNINSTALL" = 0 ]; then
    run "mkdir -p '$target'"
  elif [ ! -d "$target" ]; then
    info "(target does not exist; nothing to uninstall)"
    continue
  fi

  for name in "${SKILLS[@]}"; do
    src="$REPO_DIR/$name"
    link="$target/$name"

    if [ "$UNINSTALL" = 1 ]; then
      # Only remove a symlink that points back into this repo.
      if [ -L "$link" ] && [ "$(readlink -f "$link")" = "$(readlink -f "$src")" ]; then
        run "rm '$link'"; info "removed symlink $name"
      else
        info "skip $name (not a symlink we installed)"
      fi
      continue
    fi

    if [ -L "$link" ]; then
      current="$(readlink -f "$link" || true)"
      if [ "$current" = "$(readlink -f "$src")" ]; then
        info "ok $name (already linked)"
        continue
      fi
      if [ "$FORCE" = 1 ]; then
        run "rm '$link'"; run "ln -s '$src' '$link'"; info "relinked $name (was -> $current)"
      else
        info "SKIP $name (symlink points elsewhere: $current; use --force to replace)"
      fi
    elif [ -e "$link" ]; then
      # A real file or directory — never clobber it.
      info "SKIP $name (a real path exists at $link; not touching it)"
    else
      run "ln -s '$src' '$link'"; info "linked $name -> $src"
    fi
  done
done

echo "Done."
