# Update Shipkit

Update shipkit to the latest version. Use when user says "update shipkit", "upgrade shipkit", "check for updates", or "get latest shipkit".

## Overview

Updates the shipkit package from its origin repository, then re-syncs registered projects so they pick up new/improved guidelines rules and skills.

Since core content (guidelines, skills) lives in the shipkit package — not user content — updating is conflict-free. User content (personal overrides, project config, knowledge) is never touched by updates.

## Workflow

### 1. Locate Installation

Find the shipkit installation and determine the update path.

**Constraints:**
- Run `python -c "import shipkit; import pathlib; print(pathlib.Path(shipkit.__file__).parent.parent)"` to find the package root
- Check if it's a git repo: look for `.git/` in the package root
- If git clone: update via git (proceed to step 2)
- If installed via uv/pip: tell user to run `uv pip install --upgrade shipkit` or `uv sync --upgrade-package shipkit`, then skip to step 5
- Check for uncommitted local changes to the shipkit repo and warn

### 2. Check for Updates

Compare local vs upstream version.

**Constraints:**
- Fetch from origin: `git fetch origin`
- Compare versions: read local `shipkit/__init__.py` vs `git show origin/main:shipkit/__init__.py`
- If already up to date, tell user and stop
- If a `CHANGELOG.md` exists upstream, extract entries between current and latest version
- Present what changed: new skills, guidelines improvements, bug fixes, breaking changes
- You MUST NOT proceed without user confirmation

### 3. Apply Update

Pull the latest code.

**Constraints:**
- Run `git pull --rebase origin main`
- If conflicts occur (rare — users shouldn't modify package code):
  - List conflicted files
  - Ask user how to resolve each
  - Recommend taking upstream for package code
  - Offer `git rebase --abort` as escape hatch
- After successful pull, run `uv sync` to update dependencies

### 4. Verify

Confirm the update succeeded.

**Constraints:**
- Run `shipkit --version` to verify the new version
- Run `shipkit doctor` to check everything is healthy
- If doctor reports issues, help resolve them

### 5. Re-sync Projects

Updated package means new/improved core content — projects need re-syncing.

**Constraints:**
- Ask user: re-sync all projects, just the current one, or skip?
- Run `shipkit sync` for selected projects
- Report what changed in the compiled output (new skills added, guidelines updated, etc.)

### 6. Summary

Present what happened.

**Format:**
```
Shipkit updated: v0.1.0 → v0.2.0

What's new:
  + New skill: /debug — systematic debugging workflow
  + Improved: /commit — better merge commit handling
  + New guidelines: sustainability.md — cognitive budget management

Projects re-synced:
  + my-api — 5 commands updated
  + frontend — 5 commands updated

Your user content is untouched.
```

## Examples

### Clean Update

```
User: "update shipkit"
Agent: [locates installation, fetches origin]

       "You're on v0.1.0, latest is v0.2.0.

       What's new:
       - New 'debug' skill for systematic debugging
       - sustainability.md guidelines rule
       - commit skill: better merge commit handling

       Update now?"

User: "yes"
Agent: [git pull --rebase, uv sync]
       [shipkit --version confirms v0.2.0]
       [shipkit doctor — all clear]

       "Updated to v0.2.0. Want to re-sync your projects?"

User: "yes, all"
Agent: [shipkit sync in each project]
       "Done. 2 projects re-synced. Your user content is untouched."
```
