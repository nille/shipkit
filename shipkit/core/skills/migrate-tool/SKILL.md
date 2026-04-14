# Migrate Tool

**Trigger:** User says "migrate tool", "switch tool", "change from claude to kiro", "migrate to gemini", or similar

**Purpose:** Help users migrate their personal skills and guidelines when switching between AI coding tools (Claude Code, Kiro, Gemini CLI, OpenCode).

## Prerequisites Check

Before starting, verify:
- `~/.config/shipkit/` exists and is initialized
- User knows which tool they want to switch to
- Current tool has content worth migrating

## Process

### 1. Detect Current Tool

Check the current tool preference:
```bash
# Read from config
current_tool=$(grep 'cli_tool:' ~/.config/shipkit/config.yaml | awk '{print $2}')
echo "Current tool: $current_tool"
```

### 2. Ask Target Tool

**If user already specified target (e.g., "migrate to kiro"):**
- Extract target from their message

**If not specified, ask:**
```
Which tool are you migrating to?

  1. claude    - Claude Code
  2. kiro      - Kiro CLI  
  3. gemini    - Gemini CLI
  4. opencode  - OpenCode

Current: {current_tool}
Target: 
```

Wait for user to specify (e.g., "kiro", "2", "claude code").

### 3. Preview Migration

Show what will be migrated using dry-run:

```bash
shipkit migrate --to <target_tool> --dry-run
```

This shows:
- Source → destination paths
- How many skills/guidelines will be moved
- Whether target directories already exist (merge scenario)

### 4. Explain What Happens

Tell the user:

```
This will:
  ✓ Move your personal skills: ~/.{current}/ → ~/.{target}/
  ✓ Move your personal guidelines: ~/.{current}/ → ~/.{target}/
  ✓ Update ~/.config/shipkit/config.yaml to prefer {target}
  ✓ Keep shipkit core content (works with all tools)
  ✓ Keep project-level content (stays in .{current}/ dirs in repos)

What stays the same:
  - ~/.config/shipkit/core/ (shared across all tools)
  - ~/.config/shipkit/plugins/ (shared)
  - Project content in repos (team-shared via git)

Important notes:
  - Kiro uses "steering" instead of "guidelines"
  - After migration, run: shipkit sync
  - Your {current} tool will still work with project content
```

### 5. Confirm Migration

```
Ready to migrate from {current} to {target}? (y/n)
```

If **no:**
```
Migration cancelled. Your config remains on {current}.
```

Exit.

If **yes**, proceed.

### 6. Execute Migration

```bash
shipkit migrate --to <target_tool>
```

The CLI will:
- Show migration progress
- Handle merging if target directories exist
- Update config.yaml
- Print confirmation

### 7. Run Sync

After successful migration:
```bash
cd <current_repo_if_in_one> && shipkit sync
```

This regenerates tool-native config files for the new tool.

### 8. Summary

Tell the user:

```
✓ Migration complete: {current} → {target}

Next steps:
  1. Install {target} if not already: <install_command>
  2. Your personal skills are now at: ~/.{target}/skills/
  3. Your personal guidelines are now at: ~/.{target}/{guidelines_or_steering}/
  4. Run 'shipkit sync' in any project to update config files

Rollback (if needed):
  shipkit migrate --to {current}
```

## Tool-Specific Notes

### Claude Code
- Skills: `~/.claude/skills/`
- Guidelines: `~/.claude/guidelines/`
- Config: `CLAUDE.md`
- Install: `npm install -g @anthropic-ai/claude-code`

### Kiro
- Skills: `~/.kiro/skills/`
- **Steering** (not guidelines): `~/.kiro/steering/`
- Config: `.kiro/steering/` files
- Install: `pip install kiro-cli`

### Gemini CLI
- Skills: `~/.gemini/skills/`
- Guidelines: `~/.gemini/guidelines/`
- Config: `GEMINI.md`
- Install: See https://github.com/google/gemini-cli

### OpenCode
- Skills: `~/.opencode/skills/`
- Guidelines: `~/.opencode/guidelines/`
- Config: `AGENTS.md`
- Install: `pip install opencode`

## Edge Cases

### Already on Target Tool

If `current_tool == target_tool`:
```
You're already configured for {target}. Nothing to migrate.

Current tool preference: {target}
```

Exit early.

### No Content to Migrate

If source directories are empty:
```
No personal content found in ~/.{current}/ to migrate.

The migration would only update config.yaml: cli_tool → {target}

Proceed anyway? (y/n)
```

If yes, update config only. If no, exit.

### Target Already Has Content

If `~/.{target}/skills/` or `~/.{target}/guidelines/` already exist with content:

```
! Target directories already exist:
  ~/.{target}/skills/ ({count} items)
  ~/.{target}/guidelines/ ({count} items)

Migration will MERGE content:
  - Existing items in target: kept
  - New items from source: moved
  - Conflicts (same name): source skipped

Continue? (y/n)
```

### Tool Not Installed

After migration, if user tries to run the new tool but it's not found:

```
! {target} is not installed. Install it first:

  {install_command}

Then run: shipkit sync
```

## Example Interaction

```
User: I want to switch from claude to kiro