---
name: obsidian-vault
description: Manage an Obsidian vault with an AI agent so it stays navigable and consistent — every note reachable from a Table of Contents through domain hubs, path-qualified wikilinks added on creation, verified with a link-check script, plus deterministic graph-view color-coding and taxonomy tooling. Use when creating vault notes or categories, auditing navigation/orphans, or color-coding the knowledge graph.
---

# Obsidian Vault — agent-managed navigation and taxonomy

An Obsidian vault that an agent writes to will silently rot: notes get created
in the right folder but linked from nowhere, categories multiply without a
color, and the graph view turns into confetti. This skill keeps a vault
navigable and consistent by enforcing one rule and providing two deterministic
scripts.

The whole method rests on a single invariant:

> **Every note must be reachable from the Table of Contents by following
> wikilinks through the domain hubs.**

Everything else — how you link, how you name, how you color — serves that
invariant.

## Setup (parameterize for your vault)

The scripts take your vault via flag or environment variable so nothing is
hardcoded. Set these once per shell (or pass the flags each call):

```
export VAULT_PATH="$HOME/path/to/YourVault"       # vault root
export VAULT_TOC="Table of Contents.md"           # your TOC note (vault-relative)
export VAULT_CATEGORIES_ROOT=""                    # folder holding categories; "" = vault root
export VAULT_INVENTORY_DIR="Journal"               # optional: auto-inventoried folder
export VAULT_INVENTORY_HUB="Journal/Journal.md"    # optional: the hub that lists it
```

**These are configuration, not defaults with a fallback.**
`obsidian_graph.py` fails closed: an unset `VAULT_PATH` is an error (exit 2),
not "the current directory", and it refuses any target without an `.obsidian/`
directory. `new-category` additionally requires `VAULT_CATEGORIES_ROOT` (pass
`--categories-root ''` to mean the vault root — that is a choice, not an
omission) and a `VAULT_TOC` that exists, because a category note that is not
hub-linked is an orphan the moment it is created. A forgotten export cannot
quietly build a category tree in the wrong place.

The last two are only needed if your vault has an auto-inventoried folder — see
"Verify reachability". Set **both or neither**; half a pair is a setup error.

`python3 scripts/selftest.py` exercises every one of those guards (stdlib only,
temp vault, exits 0 when they all hold).

The running examples below use a small generic taxonomy — adapt the names to
your own:

```
YourVault/
├── Table of Contents.md        # the single root every note hangs off
├── Projects/                   # domain hub folders...
│   ├── Projects.md             #   (a hub/index note per domain)
│   └── Archive/
├── Reference/
│   └── Reference.md
├── People/
│   └── People.md
└── Journal/                    # dated notes: YYYY-MM-DD.md
    └── Journal.md
```

## The navigation rule (in practice)

- **Table of Contents** is the root. It links to each **domain hub**
  (`Projects.md`, `Reference.md`, `People.md`, `Journal.md`).
- A **domain hub** inventories its whole subtree — either it links each note
  directly, or it links to a sub-hub that does. A note placed in a subtree its
  hub already inventories inherits reachability for free.
- **When you create a note, in the same task add a path-qualified wikilink to
  it** from the appropriate hub (or place it in an already-inventoried subtree).
  Do not defer this — an unlinked note is an orphan the moment it is written.
- Then **verify** with the link checker (below). Exit 0 means clean.

### Linking and naming conventions

- Use **path-qualified wikilinks** in navigation notes so links survive
  duplicate basenames: `[[Projects/Archive/Old Migration|Old Migration]]`.
- Descriptive **Title Case** filenames with spaces; prefix dated records with
  `YYYY-MM-DD`.
- **Avoid duplicate basenames** across the vault — the link checker can only
  auto-resolve an unqualified `[[Name]]` when exactly one note has that
  basename.
- Isolated subtrees (a walled-off area you deliberately keep separate) are fine
  as long as there is exactly one boundary link into them from the TOC or a hub,
  so the subtree's own root stays reachable.

### Verify reachability

`scripts/vault-link-check.py` (stdlib only) BFS-walks the link graph from the
TOC and lists any orphan notes:

```
python3 scripts/vault-link-check.py                 # uses $VAULT_PATH / $VAULT_TOC
python3 scripts/vault-link-check.py --vault "$HOME/YourVault" --toc "Table of Contents.md"
```

Exit codes: `0` clean, `1` orphans found (listed with a remediation hint),
`2` setup error (TOC not found, or half an inventory pair — check your paths).
Read the orphan list, not the exit code alone: a vault with known, accepted
orphans exits `1` on a perfectly healthy run, and a `2` means it never walked
the vault at all. Run it after any note or category creation. A daily scheduled
run (cron / systemd timer) is a good way to catch drift; wire the same command
into whatever scheduler you use.

If your vault has a dated-journal folder you want a hub to inventory
automatically, point the checker at it and it will keep the hub in sync
(additive, idempotent) before the walk:

```
python3 scripts/vault-link-check.py \
  --inventory-dir "Journal" --inventory-hub "Journal/Journal.md"

# or set VAULT_INVENTORY_DIR / VAULT_INVENTORY_HUB once and just run:
python3 scripts/vault-link-check.py
```

**Configure it, or that sync does not happen.** With neither the flags nor the
variables, the checker walks the vault without touching the hub, so every note
added to the inventoried folder since the hub was last written is reported as
an orphan. The bare command is only equivalent to the flagged one while the hub
happens to be up to date. Set the pair in the environment for the vault you
manage, and the plain invocation stays correct.

## Graph taxonomy and color-coding

The second half of vault hygiene is the **graph view**: category folders each
get one color, driven by `<vault>/.obsidian/graph.json`. That file has sharp
edges (a decimal-integer color format and an order-dependent "first match wins"
rule) that make hand-editing error-prone. Use `scripts/obsidian_graph.py`, and
read **`references/graph-taxonomy.md`** for the full `graph.json` anatomy, the
first-match-wins ordering invariant, and the new-category flow that
auto-hub-links.

Quick reference:

```
# inspect
python3 scripts/obsidian_graph.py list      # groups in order: index, #RRGGBB, query
python3 scripts/obsidian_graph.py check      # validate + ordering lint (exit 1 on warnings)

# color a category (path query); children must be listed before parents
python3 scripts/obsidian_graph.py set 'path:"Projects"' '#E15759'
python3 scripts/obsidian_graph.py set 'path:"Projects/Archive"' '#8C8C8C'

# create a whole category: folder + index note + TOC link + graph color, in one step
python3 scripts/obsidian_graph.py new-category 'Reference'
python3 scripts/obsidian_graph.py new-category 'Projects/Archive' --color '#8C8C8C'
```

`new-category` is the payoff of merging the two halves: it creates the folder
and index note, **appends the path-qualified TOC link (satisfying the
navigation rule)**, and inserts the graph color group in the correct
children-before-parents position — then reminds you to run the link checker and
restart Obsidian. It is the one command to reach for when growing the taxonomy.

## Standing checklist

1. Create the note in its correct folder with a Title Case name.
2. Add a path-qualified wikilink from the domain hub (or use `new-category` for
   a whole new category, which does this for you).
3. `python3 scripts/vault-link-check.py` (with the inventory pair configured,
   if your vault uses one) → expect no orphan naming the note you just created.
   Exit `0` on a vault with no accepted orphans; on a vault that carries known
   ones, expect exit `1` listing exactly those. Exit `2` is a setup error.
4. If you touched categories/colors: `obsidian_graph.py check` → expect
   "ordering clean", then restart Obsidian so it does not clobber the edit.
