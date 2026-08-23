# Graph taxonomy and color-coding (`graph.json` anatomy)

Deterministic tooling for an Obsidian vault's graph-view color groups and its
category structure. Prefer `../scripts/obsidian_graph.py` over hand-editing
JSON — the file format has two traps (a decimal color format and an
order-dependent match rule) that make manual edits silently wrong.

## When to use

- Creating a new vault category (a folder, its index note, its navigation link,
  and its graph color).
- Color-coding the knowledge graph: adding, updating, removing, or reordering
  color groups, or changing a group's color.
- Auditing that the graph groups are ordered correctly (no shadowed groups).
- Any taxonomy reorg that touches which folders exist and how they're colored.

## graph.json anatomy

Graph settings live in `<vault>/.obsidian/graph.json` — a **flat JSON object**.
Color groups sit under the key `colorGroups`, an array of:

```json
{ "query": "path:\"Projects\"", "color": { "a": 1, "rgb": 14767961 } }
```

- **`rgb` is a decimal integer**, the base-10 form of `0xRRGGBB`
  (e.g. `#E15759` → `0xE15759` → `14767961`). The script converts hex for you.
- **First match wins.** Obsidian colors each node by the *first* group whose
  query matches. So a **narrower path must appear before its parent path** —
  e.g. `Projects/Archive` must be listed *before* `Projects`, or Archive notes
  take the Projects color and the Archive group is dead. This is the single most
  important invariant; the script's insertion logic and `check` lint both
  enforce it.
- **Preserve every other key.** Physics/display settings (`repelStrength`,
  `scale`, `nodeSizeMultiplier`, …) live in the same object. Only ever touch
  `colorGroups`; leave the rest byte-for-byte. The script rewrites the file with
  every non-`colorGroups` key intact.
- **Obsidian rewrites graph.json from memory** whenever graph settings change or
  on exit. If Obsidian is running when you edit the file externally, your change
  can be silently clobbered. Check with `pgrep -i obsidian`; if it's running,
  **restart Obsidian** so it both applies and stops overwriting your edit. The
  script warns automatically.
- The file **may not exist** until the graph view has been opened at least once.

## Query types: `path:` vs `tag:`

- Use **`path:"..."`** for category coloring — one path per category folder.
  Combine sibling folders with `OR`:
  `path:"Reference" OR path:"People"`.
- Reach for **`tag:#...`** only for genuinely **cross-cutting** concerns that
  span multiple folders and can't be expressed as a path — e.g.
  `tag:#status/done` to gray out completed notes vault-wide. Tags earn their
  keep when a color should follow a *property* of notes rather than their
  location. For normal one-folder-one-color taxonomy, prefer `path:`.
  Tag and path groups still obey first-match-wins against each other.

## Command reference

Script: `../scripts/obsidian_graph.py` (python3, stdlib only). The vault comes
from `$VAULT_PATH`, the categories root from `$VAULT_CATEGORIES_ROOT` (empty =
vault root), the TOC from `$VAULT_TOC`. Override any with `--vault`,
`--categories-root`, `--toc`. **These are required, not defaulted:** an unset
`VAULT_PATH`, a target with no `.obsidian/` directory, a categories root that
does not exist, or a missing TOC each stop the run at exit 2 with nothing
written. All mutating commands back up `graph.json` to
`graph.json.bak`, write pretty JSON (2-space indent) preserving all
non-`colorGroups` keys, warn if Obsidian is running, and accept `--dry-run`.

```
# inspect
python3 obsidian_graph.py list           # index, #RRGGBB, query, in order
python3 obsidian_graph.py check          # validate + ordering lint (exit 1 on warnings)

# color groups
python3 obsidian_graph.py set 'path:"Projects"' '#E15759'
python3 obsidian_graph.py set 'tag:#status/done' '#8C8C8C'
python3 obsidian_graph.py remove 'path:"Projects"'

# end-to-end category creation (folder + note + TOC link + color group)
python3 obsidian_graph.py new-category 'Reference'
python3 obsidian_graph.py new-category 'Finances' --color '#3CB44B'
python3 obsidian_graph.py new-category 'Scratch' --no-note   # folder + group only

# preview anything without writing
python3 obsidian_graph.py set 'path:"Projects/X"' '#123456' --dry-run
```

- `set` updates a group's color in place if the query already exists; otherwise
  it inserts the new group **before the first existing group that is a parent
  path** of the new query (children stay ahead of parents), else appends.
- `new-category` picks the first unused color from a built-in ~20-color
  categorical palette when `--color` is omitted, creates the folder + index
  note, **appends a path-qualified wikilink to the TOC (satisfying the vault
  navigation rule)**, inserts the color group in the right position, then prints
  reminders to run the link checker and restart Obsidian.

## Vault navigation rule (why `new-category` links the TOC)

Every note must be reachable from the Table of Contents via wikilinks.
`new-category` handles this automatically for a new category's index note. After
any category creation, verify with the link checker:

```
python3 ../scripts/vault-link-check.py     # 0 = clean, 1 = orphans, 2 = setup error
```

Read the orphan list, not the exit code alone, and set
`VAULT_INVENTORY_DIR` / `VAULT_INVENTORY_HUB` if your vault has an
auto-inventoried folder — without them that hub is not synced and its new notes
show up as orphans.

## Hand-editing fallback

Prefer the script. For an exotic query the script can't express, edit
`graph.json` by hand — but first `cp graph.json graph.json.bak`, keep the array
ordered children-before-parents, use the decimal `rgb` int, leave all other keys
untouched, run `check` afterward, and restart Obsidian.
