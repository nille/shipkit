---
name: update-shipkit
description: Update shipkit to the latest version from PyPI. Handles pip upgrade and core content refresh. Use when update notification appears or user wants latest features.
---

# Update Shipkit Skill

Automated shipkit upgrade workflow.

## When To Use

- When you see: "💡 There's a new shipkit version available"
- When user says: "update shipkit", "upgrade shipkit", "get latest shipkit"
- Periodically to stay current with new features

## Workflow

### Step 1: Check Current Version

```bash
shipkit --version
```

### Step 2: Check Available Version on PyPI

```bash
pip index versions shipkit
```

Compare current vs available.

### Step 3: Confirm Upgrade

Show user:
```
Current: shipkit 0.1.2
Available: shipkit 0.1.5

New in 0.1.5:
- [Fetch from CHANGELOG if possible, or just show version bump]

Would you like to upgrade?
```

### Step 4: Upgrade

```bash
pip install --upgrade shipkit
```

### Step 5: Refresh Core Content

After pip upgrade, refresh core content in ~/.config/shipkit/:

```bash
shipkit upgrade
```

This copies latest core/experimental/advanced from pip package to user space.

### Step 6: Verify

```bash
shipkit --version
```

Should show new version.

### Step 7: Next Steps

Tell user:
```
✅ Shipkit upgraded: 0.1.2 → 0.1.5

Changes take effect:
- New skills: Available immediately (already symlinked)
- New hooks: Take effect on next Claude restart
- Updated agent: Run 'shipkit sync' in your projects

Restart Claude Code to activate new hooks.
```

## Error Handling

**"No newer version available"**
→ "Already on latest version (0.1.5)"

**"pip upgrade failed"**
→ Show error, suggest: pip install --upgrade --force-reinstall shipkit

**"shipkit upgrade failed"**
→ Show error, may need manual cleanup

## Key Principles

- Always show what's changing (version numbers)
- Run shipkit upgrade after pip (refreshes core)
- Remind to restart Claude (hooks)
- Test that upgrade worked (verify version)
