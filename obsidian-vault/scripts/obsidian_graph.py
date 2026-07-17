#!/usr/bin/env python3
"""obsidian-graph: manage Obsidian graph-view color groups and category
creation for a vault, deterministically.

Stdlib only. See ../SKILL.md for the domain knowledge and usage.

Configure the vault with the VAULT_PATH environment variable or --vault, the
category root folder with --categories-root, and the table-of-contents note
with --toc.

graph.json anatomy (flat JSON object at <vault>/.obsidian/graph.json):
  - colorGroups: [ {"query": "<search query>", "color": {"a": 1, "rgb": <int>}} ]
    where rgb is the decimal form of 0xRRGGBB.
  - Obsidian applies FIRST MATCH WINS: a node is colored by the first group whose
    query matches, so narrower paths must sit before their parent paths.
  - All other keys (physics, display settings) are preserved untouched.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

DEFAULT_VAULT = os.environ.get("VAULT_PATH", ".")
# Root folder (relative to the vault) that holds category folders. Empty means
# categories are folders directly under the vault root.
DEFAULT_CATEGORIES_ROOT = os.environ.get("VAULT_CATEGORIES_ROOT", "")
DEFAULT_TOC_REL = os.environ.get("VAULT_TOC", "Table of Contents.md")

# ~20-color categorical palette (hex). new-category auto-picks the first color
# here not already used by an existing group.
PALETTE = [
    "#E6194B", "#3CB44B", "#FFE119", "#4363D8", "#F58231",
    "#911EB4", "#42D4F4", "#F032E6", "#BFEF45", "#FABED4",
    "#469990", "#DCBEFF", "#9A6324", "#800000", "#AAFFC3",
    "#808000", "#FFD8B1", "#000075", "#A9A9A9", "#F0A0FF",
]

PATH_RE = re.compile(r'path:"([^"]*)"')


# --------------------------------------------------------------------------
# color helpers
# --------------------------------------------------------------------------
def hex_to_int(hexstr):
    h = hexstr.strip().lstrip("#")
    if len(h) != 6 or any(c not in "0123456789abcdefABCDEF" for c in h):
        raise ValueError("color must be a 6-digit hex like #RRGGBB (got %r)" % hexstr)
    return int(h, 16)


def int_to_hex(rgb):
    try:
        return "#%06X" % int(rgb)
    except (TypeError, ValueError):
        return "#??????"


# --------------------------------------------------------------------------
# path / query helpers
# --------------------------------------------------------------------------
def query_paths(query):
    """Return the list of path:"..." values in a query (may be empty)."""
    return PATH_RE.findall(query or "")


def is_proper_path_prefix(a, b):
    """True if path a is a proper path-prefix (parent) of path b.

    Segment-aware so 'Projects' is NOT a prefix of 'ProjectsArchive'.
    """
    ap = [s for s in a.split("/") if s != ""]
    bp = [s for s in b.split("/") if s != ""]
    return len(ap) < len(bp) and bp[: len(ap)] == ap


def group_is_parent_of(parent_group, child_query):
    """True if any path in parent_group is a proper prefix of any path in the
    child query (i.e. parent_group would shadow the child)."""
    for pp in query_paths(parent_group.get("query", "")):
        for cp in query_paths(child_query):
            if is_proper_path_prefix(pp, cp):
                return True
    return False


# --------------------------------------------------------------------------
# io helpers
# --------------------------------------------------------------------------
def graph_path(vault):
    return os.path.join(vault, ".obsidian", "graph.json")


def load_graph(path, allow_missing=False):
    if not os.path.exists(path):
        if allow_missing:
            return {"colorGroups": []}, False
        raise SystemExit(
            "error: %s does not exist. Open the graph view in Obsidian once to "
            "create it." % path
        )
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise SystemExit("error: %s is not a JSON object" % path)
    data.setdefault("colorGroups", [])
    return data, True


def obsidian_running():
    try:
        out = subprocess.run(
            ["pgrep", "-i", "obsidian"], capture_output=True, text=True
        )
        return out.returncode == 0 and out.stdout.strip() != ""
    except FileNotFoundError:
        return False


def warn_if_obsidian_running():
    if obsidian_running():
        sys.stderr.write(
            "WARNING: Obsidian appears to be running. It rewrites graph.json "
            "from memory on graph-settings change or exit, which can clobber "
            "external edits. Restart Obsidian for changes to take effect.\n"
        )


def write_graph(path, data, dry_run=False):
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if dry_run:
        print("--- DRY RUN: would write %s ---" % path)
        print(text, end="")
        return
    if os.path.exists(path):
        shutil.copy2(path, path + ".bak")
        print("backed up -> %s.bak" % path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote %s" % path)


def category_rel(categories_root, *parts):
    """Join the category root with folder parts into a vault-relative path."""
    segs = [s for s in ([categories_root] + list(parts)) if s]
    return "/".join(segs)


# --------------------------------------------------------------------------
# subcommands
# --------------------------------------------------------------------------
def cmd_list(args):
    data, _ = load_graph(graph_path(args.vault))
    groups = data.get("colorGroups", [])
    if not groups:
        print("(no color groups)")
        return 0
    for i, g in enumerate(groups):
        q = g.get("query", "")
        rgb = (g.get("color") or {}).get("rgb")
        print("%2d  %-8s  %s" % (i, int_to_hex(rgb), q))
    return 0


def cmd_check(args):
    path = graph_path(args.vault)
    if not os.path.exists(path):
        print("FAIL: %s does not exist" % path)
        return 1
    try:
        data, _ = load_graph(path)
    except (ValueError, json.JSONDecodeError) as e:
        print("FAIL: cannot parse %s: %s" % (path, e))
        return 1

    warnings = []
    groups = data.get("colorGroups", [])
    for i, g in enumerate(groups):
        if not g.get("query"):
            warnings.append("group %d has no query" % i)
        color = g.get("color")
        if not isinstance(color, dict) or "rgb" not in color:
            warnings.append("group %d (%r) has no valid color/rgb"
                            % (i, g.get("query")))

    # ordering lint: an earlier group whose path is a proper prefix of a later
    # group's path shadows that later group (first match wins).
    for i in range(len(groups)):
        for j in range(i + 1, len(groups)):
            if group_is_parent_of(groups[i], groups[j].get("query", "")):
                warnings.append(
                    "ordering: group %d %r shadows later group %d %r "
                    "(parent path listed before child; child is unreachable)"
                    % (i, groups[i].get("query"), j, groups[j].get("query"))
                )

    if warnings:
        for w in warnings:
            print("WARN: " + w)
        print("check: %d warning(s)" % len(warnings))
        return 1
    print("check: OK (%d groups, ordering clean)" % len(groups))
    return 0


def _find_insert_index(groups, new_query):
    """Index before the first existing group that is a proper path-parent of
    new_query (keeps the narrower child ahead of its parent). None => append."""
    for i, g in enumerate(groups):
        if group_is_parent_of(g, new_query):
            return i
    return None


def cmd_set(args):
    path = graph_path(args.vault)
    data, existed = load_graph(path, allow_missing=True)
    if not existed:
        sys.stderr.write("note: %s did not exist; creating a new one.\n" % path)
    groups = data.setdefault("colorGroups", [])
    rgb = hex_to_int(args.color)
    query = args.query

    # update in place if the query already exists
    for g in groups:
        if g.get("query") == query:
            old = int_to_hex((g.get("color") or {}).get("rgb"))
            g["color"] = {"a": 1, "rgb": rgb}
            print("update: %r  %s -> %s" % (query, old, int_to_hex(rgb)))
            warn_if_obsidian_running()
            write_graph(path, data, dry_run=args.dry_run)
            return 0

    new_group = {"query": query, "color": {"a": 1, "rgb": rgb}}
    idx = _find_insert_index(groups, query)
    if idx is None:
        groups.append(new_group)
        print("add: %r %s (appended at index %d)"
              % (query, int_to_hex(rgb), len(groups) - 1))
    else:
        groups.insert(idx, new_group)
        print("add: %r %s (inserted at index %d, before parent %r)"
              % (query, int_to_hex(rgb), idx, groups[idx + 1].get("query")))
    warn_if_obsidian_running()
    write_graph(path, data, dry_run=args.dry_run)
    return 0


def cmd_remove(args):
    path = graph_path(args.vault)
    data, _ = load_graph(path)
    groups = data.get("colorGroups", [])
    before = len(groups)
    kept = [g for g in groups if g.get("query") != args.query]
    if len(kept) == before:
        print("remove: no group with query %r" % args.query)
        return 1
    data["colorGroups"] = kept
    print("remove: %r (%d -> %d groups)" % (args.query, before, len(kept)))
    warn_if_obsidian_running()
    write_graph(path, data, dry_run=args.dry_run)
    return 0


def _used_rgbs(groups):
    used = set()
    for g in groups:
        rgb = (g.get("color") or {}).get("rgb")
        if rgb is not None:
            used.add(int(rgb))
    return used


def _pick_auto_color(groups):
    used = _used_rgbs(groups)
    for hexc in PALETTE:
        if hex_to_int(hexc) not in used:
            return hexc
    return PALETTE[0]  # palette exhausted; reuse first


def _toc_link_line(rel_path, leaf):
    return "- [[%s|%s]]" % (rel_path, leaf)


def cmd_new_category(args):
    vault = args.vault
    categories_root = args.categories_root
    raw = args.name.strip().strip("/")
    if not raw:
        raise SystemExit("error: category name/path is empty")
    parts = [p for p in raw.split("/") if p != ""]
    leaf = parts[-1]
    rel_folder = category_rel(categories_root, *parts)
    abs_folder = os.path.join(vault, *rel_folder.split("/"))
    note_rel = "%s/%s" % (rel_folder, leaf)
    abs_note = os.path.join(abs_folder, leaf + ".md")
    query = 'path:"%s"' % rel_folder

    # color
    gpath = graph_path(vault)
    data, existed = load_graph(gpath, allow_missing=True)
    groups = data.setdefault("colorGroups", [])
    color_hex = args.color if args.color else _pick_auto_color(groups)
    rgb = hex_to_int(color_hex)

    # plan the graph mutation (same insertion logic as `set`)
    exists_in_graph = any(g.get("query") == query for g in groups)

    print("=== new-category plan ===")
    print("folder:   %s" % abs_folder)
    if not args.no_note:
        print("note:     %s" % abs_note)
        print("toc link: %s" % _toc_link_line(note_rel, leaf))
    print("group:    %s  %s" % (query, int_to_hex(rgb)))
    if args.dry_run:
        print("(dry-run: nothing written)")

    # 1. folder
    if not args.dry_run:
        os.makedirs(abs_folder, exist_ok=True)
        print("created folder %s" % abs_folder)

    # 2. index note + TOC link
    if not args.no_note:
        if os.path.exists(abs_note):
            print("note already exists, leaving as-is: %s" % abs_note)
        elif not args.dry_run:
            with open(abs_note, "w", encoding="utf-8") as f:
                f.write("# %s\n\n_Placeholder index note for the %s category._\n"
                        % (leaf, leaf))
            print("created note %s" % abs_note)

        # append TOC link if not already present
        toc_abs = os.path.join(vault, *args.toc.split("/"))
        link_line = _toc_link_line(note_rel, leaf)
        if os.path.exists(toc_abs):
            with open(toc_abs, "r", encoding="utf-8") as f:
                toc_text = f.read()
            if note_rel in toc_text:
                print("TOC already links %s, skipping" % note_rel)
            elif not args.dry_run:
                sep = "" if toc_text.endswith("\n") else "\n"
                with open(toc_abs, "a", encoding="utf-8") as f:
                    f.write(sep + link_line + "\n")
                print("appended TOC link -> %s" % toc_abs)
        else:
            sys.stderr.write("WARNING: TOC not found at %s; add the hub link "
                             "manually.\n" % toc_abs)

    # 3. color group
    if exists_in_graph:
        for g in groups:
            if g.get("query") == query:
                g["color"] = {"a": 1, "rgb": rgb}
        print("graph: updated existing group %r" % query)
    else:
        new_group = {"query": query, "color": {"a": 1, "rgb": rgb}}
        idx = _find_insert_index(groups, query)
        if idx is None:
            groups.append(new_group)
            print("graph: appended group %r at index %d" % (query, len(groups) - 1))
        else:
            groups.insert(idx, new_group)
            print("graph: inserted group %r at index %d (before parent %r)"
                  % (query, idx, groups[idx + 1].get("query")))
    warn_if_obsidian_running()
    if not existed:
        sys.stderr.write("note: graph.json did not exist; creating a new one.\n")
    write_graph(gpath, data, dry_run=args.dry_run)

    # 4. reminders
    print("")
    print("REMINDER: verify hub-linking with vault-link-check.py "
          "(in this scripts/ directory), e.g.:")
    print("  python3 vault-link-check.py --vault %r --toc %r" % (vault, args.toc))
    print("REMINDER: restart Obsidian so it picks up the graph.json change "
          "(and does not overwrite it).")
    return 0


# --------------------------------------------------------------------------
# cli
# --------------------------------------------------------------------------
def build_parser():
    p = argparse.ArgumentParser(
        prog="obsidian_graph.py",
        description="Manage Obsidian graph-view color groups and vault categories.",
    )
    p.add_argument("--vault", default=DEFAULT_VAULT,
                   help="vault root (default: $VAULT_PATH, else current dir)")
    p.add_argument("--categories-root", default=DEFAULT_CATEGORIES_ROOT,
                   help="folder (relative to the vault) that holds category "
                        "folders; empty = vault root (default: $VAULT_CATEGORIES_ROOT)")
    p.add_argument("--toc", default=DEFAULT_TOC_REL,
                   help="table-of-contents note, relative to the vault "
                        "(default: $VAULT_TOC or 'Table of Contents.md')")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="list color groups in order")
    sub.add_parser("check", help="validate + ordering lint")

    s = sub.add_parser("set", help="add or update a color group")
    s.add_argument("query")
    s.add_argument("color", help="#RRGGBB (with or without #)")
    s.add_argument("--dry-run", action="store_true")

    r = sub.add_parser("remove", help="remove a color group by exact query")
    r.add_argument("query")
    r.add_argument("--dry-run", action="store_true")

    n = sub.add_parser("new-category", help="create a category folder+note+group")
    n.add_argument("name", help="Name or Nested/Path under the categories root")
    n.add_argument("--color", help="#RRGGBB (auto-picked from palette if omitted)")
    n.add_argument("--no-note", action="store_true",
                   help="skip index note + TOC link")
    n.add_argument("--dry-run", action="store_true")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    handlers = {
        "list": cmd_list,
        "check": cmd_check,
        "set": cmd_set,
        "remove": cmd_remove,
        "new-category": cmd_new_category,
    }
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
