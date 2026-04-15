---
name: update-shipkit
description: Update shipkit to the latest version from PyPI. Handles uv/pip upgrade and core content refresh. Use when update notification appears or user wants latest features.
---

# Update Shipkit Skill

Automated shipkit upgrade workflow.

## When To Use

- When you see: "There's a new shipkit version available"
- When user says: "update shipkit", "upgrade shipkit", "get latest shipkit"
- Periodically to stay current with new features

## Workflow

### Step 1: Check Current Version

```bash
shipkit --version
```

### Step 2: Detect Installation Method

Determine how shipkit was installed so we use the right upgrade command:

```bash
# Find the package location
python3 -c "import shipkit; from pathlib import Path; p = Path(shipkit.__file__).parent.parent; print(p); print('git' if (p / '.git').exists() else 'pip')"
```

```bash
# Also check if installed via uv tool
uv tool list 2>/dev/null | grep shipkit
```

- If the package root has `.git/`: it's a **local git clone** (most common for development)
- If `uv tool list` shows shipkit: it's a **uv tool install**
- Otherwise: it's a **pip install** (from PyPI or local)

### Step 3: Check for Updates

**Git clone install:**
```bash
cd <package-root>
git fetch origin
git log HEAD..origin/main --oneline
```
If no new commits, tell user and stop.
Show what changed (new commits, CHANGELOG entries).

**PyPI install:**
```bash
uv pip index versions shipkit 2>/dev/null || pip index versions shipkit
```
Compare current vs available. If already on latest, tell user and stop.

### Step 4: Confirm Upgrade

Show user what's new and ask to proceed.

### Step 5: Upgrade

**Git clone install:**
```bash
cd <package-root>
git pull --rebase origin main
pip install --force-reinstall .
```
`--force-reinstall` is required because pip doesn't detect changes in a local clone
unless the version number bumped. Without it, pip sees "same version" and skips.

**uv tool install:**
```bash
uv tool upgrade shipkit
```

**pip from PyPI:**
```bash
pip install --upgrade shipkit
```

### Step 6: Refresh Core Content

After upgrading the package, refresh core content in ~/.config/shipkit/:

```bash
shipkit upgrade
```

This copies latest core/experimental/advanced from the updated package to user space and recreates symlinks.

### Step 7: Verify

```bash
shipkit --version
```

Should show new version.

### Step 8: Next Steps

Tell user:
```
Shipkit upgraded: 0.1.2 -> 0.1.5

Changes take effect:
- New skills: Available immediately (already symlinked)
- New hooks: Take effect on next Claude restart
- Updated agent: Run 'shipkit sync' in your projects

Restart Claude Code to activate new hooks.
```

## Error Handling

**"No newer version available"**
-> "Already on latest version (0.1.5)"

**"Upgrade failed"**
-> Show error, suggest: `uv pip install --upgrade --force-reinstall shipkit` or `pip install --upgrade --force-reinstall shipkit`

**"shipkit upgrade failed"**
-> Show error, may need manual cleanup of ~/.config/shipkit/

## Key Principles

- Detect installation method before upgrading (uv tool vs uv pip vs pip)
- Always show what's changing (version numbers)
- Run `shipkit upgrade` after package upgrade (refreshes core content)
- Remind to restart Claude (hooks)
- Test that upgrade worked (verify version)
