#!/usr/bin/env python3
"""Vault navigation-reachability check.

Vault rule: every Markdown note must be reachable from a single Table of
Contents note by following wikilinks through the domain hubs. This script
builds the link graph, BFS-walks it from the TOC, and reports orphans (notes
that no link chain reaches).

Configure the vault path with the VAULT_PATH environment variable or --vault.
Configure the TOC and (optional) auto-inventoried folder with the flags below.

Exit codes: 0 = fully reachable, 1 = orphans found, 2 = setup error.

Usage:
  vault-link-check.py [--vault PATH] [--toc REL] [--quiet]
                      [--inventory-dir REL --inventory-hub REL]

  --vault PATH          Vault root (default: $VAULT_PATH, else current dir).
  --toc REL             Table-of-contents note, relative to the vault root
                        (default: "Table of Contents.md").
  --inventory-dir REL   Optional folder whose notes are auto-listed in a hub
                        (e.g. a dated-journal folder). Requires --inventory-hub.
  --inventory-hub REL   Hub note that inventories --inventory-dir. When both are
                        given, the hub is kept in sync with the folder's notes
                        (additive, idempotent) before the reachability walk.
  --quiet               Suppress the remediation hint on failure.
"""

import argparse
import os
import re
import sys
from collections import deque
from pathlib import Path

WIKILINK = re.compile(r"\[\[([^\]|#^]+)")
MDLINK = re.compile(r"\]\(([^)]+\.md)\)")


def sync_inventory_hub(vault: Path, inv_dir: str, inv_hub: str) -> int:
    """Ensure the hub explicitly inventories every note in inv_dir.

    Lists all notes in inv_dir, sorted, as path-qualified wikilinks below any
    existing hub content. Additive and idempotent. Returns links added."""
    hub = vault / inv_hub
    folder = vault / inv_dir
    if not hub.is_file() or not folder.is_dir():
        return 0
    notes = sorted(p.stem for p in folder.glob("*.md"))
    lines = hub.read_text(encoding="utf-8").splitlines()
    head = [ln for ln in lines if not ln.startswith("- [[")]
    while head and not head[-1].strip():
        head.pop()
    existing = {ln for ln in lines if ln.startswith("- [[")}
    wanted = [f"- [[{inv_dir}/{d}]]" for d in notes]
    added = len([w for w in wanted if w not in existing])
    hub.write_text("\n".join(head + [""] + wanted) + "\n", encoding="utf-8")
    return added


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", default=os.environ.get("VAULT_PATH", "."))
    ap.add_argument("--toc", default="Table of Contents.md")
    ap.add_argument("--inventory-dir")
    ap.add_argument("--inventory-hub")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    vault = Path(args.vault).expanduser()
    toc = args.toc
    if not (vault / toc).is_file():
        print(f"ERROR: TOC not found at {vault / toc}", file=sys.stderr)
        print("Set --vault / VAULT_PATH and --toc to your vault and TOC note.",
              file=sys.stderr)
        return 2

    if args.inventory_dir and args.inventory_hub:
        added = sync_inventory_hub(vault, args.inventory_dir, args.inventory_hub)
        if added:
            print(f"Inventory hub: added {added} missing link(s).")

    notes = {p.relative_to(vault).as_posix(): p
             for p in vault.rglob("*.md")
             if not any(part.startswith(".") for part in p.parts)}
    by_basename: dict[str, list[str]] = {}
    for rel in notes:
        by_basename.setdefault(Path(rel).stem.lower(), []).append(rel)

    def resolve(target: str) -> str | None:
        target = target.strip().removesuffix(".md")
        if (cand := f"{target}.md") in notes:
            return cand
        matches = by_basename.get(Path(target).stem.lower(), [])
        return matches[0] if len(matches) == 1 else None

    seen = {toc}
    queue = deque([toc])
    while queue:
        rel = queue.popleft()
        text = notes[rel].read_text(encoding="utf-8", errors="replace")
        for pat in (WIKILINK, MDLINK):
            for m in pat.findall(text):
                if (dest := resolve(m)) and dest not in seen:
                    seen.add(dest)
                    queue.append(dest)

    orphans = sorted(set(notes) - seen)
    if orphans:
        print(f"ORPHANS: {len(orphans)} of {len(notes)} notes unreachable "
              f"from {toc}:")
        for rel in orphans:
            print(f"  {rel}")
        if not args.quiet:
            print("\nFix: link each note from its domain hub, or place it in a "
                  "subtree an already-reachable hub inventories.")
        return 1
    print(f"OK: all {len(notes)} notes reachable from {toc}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
