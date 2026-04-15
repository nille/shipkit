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
# Check if installed via uv tool
uv tool list 2>/dev/null | grep shipkit

# Check if installed in a uv-managed environment
pip show shipkit 2>/dev/null | grep Location
```

- If `uv tool list` shows shipkit: it's a **uv tool install**
- If location is inside a `.venv`: it's a **uv/pip project install**
- Otherwise: it's a **regular pip install**

### Step 3: Check Available Version on PyPI

```bash
# Prefer uv if available
uv pip index versions shipkit 2>/dev/null || pip index versions shipkit
```

Compare current vs available. If already on latest, tell user and stop.

### Step 4: Confirm Upgrade

Show user:
```
Current: shipkit 0.1.2
Available: shipkit 0.1.5

New in 0.1.5:
- [Fetch from CHANGELOG if possible, or just show version bump]

Would you like to upgrade?
```

### Step 5: Upgrade

Use the method matching the installation:

**uv tool install (recommended):**
```bash
uv tool upgrade shipkit
```

**uv pip (project venv):**
```bash
uv pip install --upgrade shipkit
```

**pip fallback:**
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
