---
name: worktree-deploy-hazard
description: Avoid silently breaking production when a git checkout doubles as a live deploy source (a server serves files straight from the working tree). Use before running git checkout/switch in any repo where a running service reads the working directory, or when setting up parallel work in one — switch branches in a temporary git worktree instead, and flag deploy-coupled checkouts in project docs.
---

# Worktree Deploy Hazard — when a checkout IS production

Some setups serve files **straight out of a git working tree**: a web server
with its document root pointing at the checkout, a bind-mount into a container, a
process that imports modules from the working directory. In those setups the
working tree is not just source — **it is production.**

That creates a quiet, dangerous coupling: **`git checkout` / `git switch` changes
what is live.** A second session (a teammate, another agent, a scheduled job)
that switches branches in that same checkout to do unrelated work silently
swaps production to whatever that branch contains — a half-finished feature, an
old commit, a different site entirely — with no deploy step and no warning. The
files on disk changed, so the server is now serving them.

## The rule

- **Never `git checkout` / `git switch` branches in a shared checkout that is a
  live deploy source.** The working tree's current branch is load-bearing for a
  running service; changing it is a deploy, whether you meant one or not.
- **For parallel work, use a temporary worktree** instead of switching branches
  in place:

  ```
  git worktree add /tmp/work-myfeature my-branch   # or a new branch:
  git worktree add -b feat/thing /tmp/work-thing origin/main
  # ...do your work in /tmp/work-thing, commit, push...
  git worktree remove /tmp/work-thing              # clean up when done
  ```

  A worktree is a second working directory on a different branch that shares the
  same repository. The deploy-source checkout keeps its branch — production is
  untouched — while you build and commit elsewhere.
- **Clean up worktrees when finished** (`git worktree remove`, or
  `git worktree prune` for stale ones) so they don't accumulate.
- **Merging deploys, too.** In a repo where merging to the served branch is the
  deploy, only a human should merge, and the merge should be a deliberate
  release — never an incidental side effect of finishing a PR.

## Flag it loudly in project docs

The hazard is invisible from the repo alone — nothing about a checkout announces
"a server serves me." So **make it explicit** wherever agents and teammates
look first:

- Put a prominent warning in the project's `AGENTS.md` / `README` / `CLAUDE.md`:
  *"This checkout at `<path>` is the live deploy source for `<service>`. Do NOT
  `git checkout`/`switch` here — use `git worktree add` for parallel work. Merges
  to `<branch>` deploy."*
- Name the exact path, the service it feeds, and the branch that is "live."
- If a directory being recreated by a checkout can orphan a nested bind-mount
  (a mountpoint inside the working tree), say so and note the recovery step
  (usually: restart the serving process to re-establish the mount).

## Why it bites

The failure is silent and shared-state: nothing errors, no deploy runs, and the
person who switched branches may never realize they changed what the world sees —
they were doing unrelated work in "just a git repo." The cost lands on whoever
notices production changed. A one-line warning in the docs and a habit of
`git worktree add` for anything parallel prevents the whole class of incident.
