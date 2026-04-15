---
name: install
description: Install Shipkit safely into existing Claude Code setup. Scans current config, reports status, then guides through installation. Use when user says "install", "setup", "configure shipkit", or is getting started.
---

# Shipkit Installer

Guide users through safe Shipkit installation with a scan-first approach: diagnose current state, report status, then fix issues interactively.

## Workflow

### Phase 1: Diagnose

Run these checks and collect results:

1. **Claude Code installed** - `which claude` (required)
2. **Git installed** - `which git` (required for /commit, /pr, etc.)
3. **Git user configured** - `git config user.name && git config user.email`
   - **IMPORTANT:** Only CHECK if configured, do NOT modify
   - If missing: Report in Phase 2 as "❌ Git user not configured"
   - If present: Report in Phase 2 as "✅ Git user configured (Name <email>)"
   - **Never change git config without explicit user request**
4. **Claude home exists** - `test -d ~/.claude`
5. **Existing settings.json** - `test -f ~/.claude/settings.json`
6. **Existing hooks** - Parse ~/.claude/settings.json, count hooks
7. **Existing agents** - `ls ~/.claude/agents/` and check for "shipkit.md"
8. **Existing skills** - Count `ls ~/.claude/skills/` (user personal skills)
9. **Existing guidelines** - Count `ls ~/.claude/guidelines/*.md`
10. **Shipkit already installed** - Check if `~/.config/shipkit/` exists
11. **Python version** - `python3 --version` (must be >= 3.10)
12. **Model configuration (Bedrock users)** - If using Bedrock (`CLAUDE_CODE_USE_BEDROCK=1`), validate model IDs:
    - Check `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`
    - Valid formats: `us.anthropic.claude-opus-4-6-v1` OR `global.anthropic.claude-opus-4-20250514-v1:0[1m]`
    - Invalid: `global.anthropic.claude-opus-4-6-v1:0[1m]` (missing date for global endpoint)

### Phase 2: Report Status

Display a status dashboard:

```
## Shipkit Installation Scan

### Prerequisites
✅ Claude Code installed (/usr/local/bin/claude)
✅ Git installed (2.40.1)
✅ Git user configured (Nicklas af Ekenstam <nick@example.com>)
✅ Python 3.14.3 (>= 3.10 ✓)

**Note:** If git user is not configured or user wants to change it, ask:
```
Would you like to configure git user?
  Current: Nicklas af Ekenstam <ekenstam@amazon.com>
  
  Keep current, or change?
  (Leave blank to keep, or enter: Name <email>)
```

Only change if user explicitly provides new values.

### Current Claude Code Setup
✅ ~/.claude/ exists
✅ settings.json found
⚠️ 3 existing hooks found (will merge, not replace)
❌ Agent "shipkit" already exists (will backup first)
✅ 5 personal skills found (will preserve)
✅ 2 personal guidelines found (will preserve)

### Bedrock Model Configuration (if applicable)
✅ Using Bedrock (CLAUDE_CODE_USE_BEDROCK=1)
⚠️ Invalid Opus model ID detected
    Current: global.anthropic.claude-opus-4-6-v1:0[1m]
    Valid options:
      - us.anthropic.claude-opus-4-6-v1 (US regional)
      - global.anthropic.claude-opus-4-20250514-v1:0[1m] (global with date)
    Will offer to fix during install

### Shipkit Status
❌ Not yet installed

---

Ready to install? I'll:
1. Backup your current settings.json
2. Fix invalid Bedrock model IDs (if needed)
3. Merge Shipkit hooks (preserve your existing hooks)
4. Install shipkit agent to ~/.claude/agents/shipkit.md
5. Create ~/.config/shipkit/config.yaml

Your existing skills, guidelines, and hooks will be preserved.
```

Status icons:
- ✅ Ready
- ⚠️ Warning (will handle safely)
- ❌ Missing (will install)

### Phase 3: Gather Preferences

Before installing, ask about layer preferences:

```
Which skill sets would you like to install?

  [x] Core - Battle-tested essentials (21 skills)
      /commit, /pr, /review, /test, /research, /release, etc.
      Recommended for everyone.

  [ ] Experimental - Cutting-edge features (may change)
      New AI techniques, alpha features, unstable APIs.
      Only if you want to live on the edge.

  [ ] Advanced - Specialized/domain-specific tools
      Performance profiling, K8s debugging, SQL optimization.
      Only if you need these specific domains.

Select which to enable (space to toggle, enter to confirm):
> Core only (recommended)
```

Save preference to memory for config.yaml creation.

#### 3.2 MCP Servers

MCP servers are configured per-project during `/init`, not during global install.
Each project gets its own MCP servers based on its tech stack.

When a user first runs `sk` in a project, shipkit will automatically offer to run
`/init` to set up project-specific MCP servers and preferences.

### Phase 4: Install

Work through installation in order:

#### 4.1 Backup Existing Config

If ~/.claude/settings.json exists:

```bash
cp ~/.claude/settings.json ~/.claude/settings.json.backup-$(date +%Y%m%d-%H%M%S)
```

Explain: "✓ Backed up settings.json to ~/.claude/settings.json.backup-YYYYMMDD-HHMMSS"

If ~/.claude/agents/shipkit.md exists:

```bash
mv ~/.claude/agents/shipkit.md ~/.claude/agents/shipkit.md.backup-$(date +%Y%m%d-%H%M%S)
```

Explain: "✓ Backed up existing shipkit agent"

#### 4.2 Create Shipkit Config

Create ~/.config/shipkit/config.yaml based on user's layer preferences:

```yaml
layers:
  core: true
  experimental: false  # or true based on user choice
  advanced: false      # or true based on user choice

marketplace:
  auto_check: true
  last_check: ""

plugin_registries:
  - github.com/nille/shipkit-marketplace
```

**IMPORTANT:** Do NOT include `cli_tool` field (obsolete, removed in recent refactor).

**If Bedrock user with invalid model IDs detected:**
Also fix model IDs in settings.json env section:
- `global.anthropic.claude-opus-4-6-v1:0[1m]` → `global.anthropic.claude-opus-4-20250514-v1:0[1m]` (add date)
- Or suggest using `us.` regional endpoint instead

Explain: "✓ Created ~/.config/shipkit/config.yaml"
If fixed models: "✓ Fixed invalid Bedrock model IDs"

#### 4.3 Merge Hooks

Read existing ~/.claude/settings.json, merge shipkit hooks:

**IMPORTANT:** Merge, don't replace! If user has existing hooks for the same event, preserve both.

Example merge strategy:
```json
{
  "hooks": {
    "SessionStart": [
      ...existing user hooks...,
      ...shipkit hooks...
    ]
  }
}
```

**Note:** Hooks are merged by reading hook YAML definitions and merging into settings.json manually.
Do NOT use `shipkit sync` for hooks - it syncs project files, not global hooks.

Explain which hooks were added and confirm existing hooks were preserved.

#### 4.4 Verify Installation

Run verification checks:

```bash
shipkit status
```

Expected output should show:
- Shipkit metadata: ~/.config/shipkit/
- Enabled layers
- Claude Code home: ~/.claude/
- Installation successful

#### 4.5 Test in Current Directory

If we're in a git repo, offer to run sync:

```bash
cd <current-directory>
shipkit sync
```

Show what files were generated (.claude/agents/shipkit.md, CLAUDE.md, etc.)

### Phase 5: Next Steps

Display success message with guidance:

```
Shipkit installed successfully!

Installed:
  + Layer preferences saved to ~/.config/shipkit/config.yaml
  + Hooks merged into ~/.claude/settings.json
  + Shipkit agent created at ~/.claude/agents/shipkit.md

Next steps:
  1. cd to a git repository
  2. Run: sk                     # Launch shipkit (auto-syncs + offers /init)
     Or: shipkit run             # Same thing, longer name

  First launch in a project will offer to run /init to set up
  project-specific MCP servers based on your tech stack.

Quick access:
  Run: shipkit alias sk --install
  Then use: sk "add tests for auth module"

Try your new skills:
  /commit                       # Smart git commits
  /pr                           # Generate pull requests
  /review <pr>                  # Code reviews
  /init                         # Set up MCP servers for a project

Documentation:
  - Skills: Use /skills in any session to see all available
  - Help: shipkit --help

Your existing Claude Code setup has been preserved. All your personal skills,
guidelines, and hooks are still active.
```

## Key Principles

- **Scan first, act later** - Always diagnose before changing anything
- **Always backup** - Before modifying settings.json or overwriting agents
- **Merge, never replace** - Preserve user's existing hooks, skills, guidelines
- **Explain everything** - Tell user what you're doing and why
- **Verify it worked** - Run shipkit status to confirm
- **Be conservative** - Ask when uncertain, default to safer option
- **Handle errors gracefully** - If something fails, explain clearly and suggest fixes

## Error Handling

Common issues and how to resolve:

**Claude Code not installed:**
```
❌ Claude Code not found
Install it first: curl -fsSL https://claude.ai/install.sh | bash
```

**Shipkit already installed:**
```
✓ Shipkit is already installed!
Run: shipkit status      # See current config
Run: shipkit install     # Re-run installer (will update)
```

**Settings.json parse error:**
```
⚠️ Could not parse ~/.claude/settings.json (invalid JSON)
I can fix this - would you like me to:
  1. Backup and recreate (recommended)
  2. Show me the file so I can manually fix
  3. Skip hooks installation
```

**Permission denied:**
```
❌ Cannot write to ~/.claude/settings.json
Check permissions: ls -la ~/.claude/settings.json
Try: chmod 644 ~/.claude/settings.json
```

## Testing After Installation

Suggest the user test in their current directory if it's a git repo:

```bash
# Test shipkit works
shipkit status           # Should show config
shipkit sync            # Should generate .claude/ files
claude --agent shipkit  # Should launch with shipkit branding

# Try a core skill
/commit                 # Should work
```

If any test fails, help debug the issue before claiming success.
