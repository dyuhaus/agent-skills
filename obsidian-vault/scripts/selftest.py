#!/usr/bin/env python3
"""Self-test for the fail-closed guards in this scripts/ directory.

These two scripts create folders and notes inside a user's vault, so the
failure that matters is not a crash — it is a run that exits 0 having written
to the wrong tree because an environment variable was never exported. Every
case below asserts on the artifact (what exists on disk afterwards), not only
on the exit code.

Stdlib only. Run: python3 selftest.py   ->   exit 0 = all guards hold.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GRAPH = HERE / "obsidian_graph.py"
LINKCHECK = HERE / "vault-link-check.py"

FAILURES = []


def run(script, *argv, cwd=None, env=None):
    e = {k: v for k, v in os.environ.items()
         if not k.startswith("VAULT_")}
    e.update(env or {})
    return subprocess.run([sys.executable, str(script), *argv],
                          cwd=cwd, env=e, capture_output=True, text=True)


def check(name, cond, detail=""):
    if cond:
        print(f"  ok    {name}")
    else:
        print(f"  FAIL  {name}  {detail}")
        FAILURES.append(name)


def make_vault(root: Path) -> dict:
    (root / ".obsidian").mkdir(parents=True)
    (root / ".obsidian" / "graph.json").write_text('{"colorGroups": []}\n')
    (root / "2 - Categories" / "Navigation").mkdir(parents=True)
    (root / "2 - Categories" / "Navigation" / "TOC.md").write_text("# TOC\n")
    (root / "0 - Daily Notes").mkdir()
    (root / "0 - Daily Notes" / "2026-01-01.md").write_text("# day\n")
    (root / "2 - Categories" / "Navigation" / "Daily.md").write_text("# Daily\n")
    (root / "2 - Categories" / "Navigation" / "TOC.md").write_text(
        "# TOC\n\n- [[2 - Categories/Navigation/Daily]]\n")
    return {
        "VAULT_PATH": str(root),
        "VAULT_CATEGORIES_ROOT": "2 - Categories",
        "VAULT_TOC": "2 - Categories/Navigation/TOC.md",
    }


def test_graph_fails_closed(tmp: Path):
    print("obsidian_graph.py — fail closed")
    empty = tmp / "not-a-vault"
    empty.mkdir()

    # 1. no configuration at all, run from an arbitrary directory
    r = run(GRAPH, "new-category", "Knowledge/Robotics", cwd=str(empty))
    wrote = sorted(p.name for p in empty.iterdir())
    check("unset VAULT_PATH exits 2", r.returncode == 2, r.stderr.strip())
    check("unset VAULT_PATH writes nothing", wrote == [], f"found {wrote}")

    # 2. a real directory that is not a vault
    r = run(GRAPH, "new-category", "X", env={"VAULT_PATH": str(empty),
                                             "VAULT_CATEGORIES_ROOT": "",
                                             "VAULT_TOC": "TOC.md"})
    check("non-vault target exits 2", r.returncode == 2, r.stderr.strip())
    check("non-vault target writes nothing",
          sorted(p.name for p in empty.iterdir()) == [], "directory was touched")

    vault = tmp / "vault"
    env = make_vault(vault)

    # 3. the reviewer's case: categories root forgotten inside a real vault
    partial = {k: v for k, v in env.items() if k != "VAULT_CATEGORIES_ROOT"}
    r = run(GRAPH, "new-category", "Knowledge/Robotics", env=partial)
    check("missing VAULT_CATEGORIES_ROOT exits 2", r.returncode == 2,
          r.stderr.strip())
    check("missing VAULT_CATEGORIES_ROOT creates no folder",
          not (vault / "Knowledge").exists(), "wrong folder was created")

    # 4. typo'd categories root
    bad = dict(env, VAULT_CATEGORIES_ROOT="2 - Categoriez")
    r = run(GRAPH, "new-category", "Robotics", env=bad)
    check("nonexistent categories root exits 2", r.returncode == 2,
          r.stderr.strip())

    # 5. TOC that does not exist -> refused, not warned
    bad = dict(env, VAULT_TOC="Navigation/Missing.md")
    r = run(GRAPH, "new-category", "Robotics", env=bad)
    check("missing TOC exits 2", r.returncode == 2, r.stderr.strip())
    check("missing TOC creates no folder",
          not (vault / "2 - Categories" / "Robotics").exists(),
          "an unlinkable category was created")

    # 6. positive control: fully configured, it still does the job
    r = run(GRAPH, "new-category", "Knowledge/Robotics", env=env)
    note = vault / "2 - Categories" / "Knowledge" / "Robotics" / "Robotics.md"
    toc = (vault / env["VAULT_TOC"]).read_text(encoding="utf-8")
    check("configured run exits 0", r.returncode == 0, r.stderr.strip())
    check("configured run creates the note", note.is_file(), str(note))
    check("configured run appends the hub link",
          "2 - Categories/Knowledge/Robotics/Robotics" in toc, toc)


def test_linkcheck_inventory(tmp: Path):
    print("vault-link-check.py — inventory sync")
    vault = tmp / "vault2"
    env = make_vault(vault)
    inv = {"VAULT_INVENTORY_DIR": "0 - Daily Notes",
           "VAULT_INVENTORY_HUB": "2 - Categories/Navigation/Daily.md"}

    # a new dated note is an orphan until the hub is synced
    (vault / "0 - Daily Notes" / "2026-01-02.md").write_text("# day 2\n")

    r = run(LINKCHECK, env=dict(env, **inv))
    check("configured run syncs the hub",
          "2026-01-02" in (vault / inv["VAULT_INVENTORY_HUB"]).read_text(),
          r.stdout)
    check("configured run reports no orphan for the dated note",
          "2026-01-02.md" not in r.stdout, r.stdout)

    # half a pair must not silently skip the sync
    half = dict(env, VAULT_INVENTORY_DIR=inv["VAULT_INVENTORY_DIR"])
    r = run(LINKCHECK, env=half)
    check("half-configured inventory exits 2", r.returncode == 2,
          r.stdout + r.stderr)

    # a configured-but-missing hub is a setup error, not a skip
    bad = dict(env, **inv)
    bad["VAULT_INVENTORY_HUB"] = "2 - Categories/Navigation/Nope.md"
    r = run(LINKCHECK, env=bad)
    check("missing inventory hub exits 2", r.returncode == 2,
          r.stdout + r.stderr)


def main() -> int:
    for script in (GRAPH, LINKCHECK):
        if not script.is_file():
            print(f"ERROR: {script} not found", file=sys.stderr)
            return 2
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        test_graph_fails_closed(tmp)
        test_linkcheck_inventory(tmp)
    if FAILURES:
        print(f"\n{len(FAILURES)} guard(s) FAILED: {', '.join(FAILURES)}")
        return 1
    print("\nall guards hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
