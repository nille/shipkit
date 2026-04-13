# Setup

Guide users through first-time shipkit configuration. Use when user says "setup", "setup shipkit", "configure shipkit", "get started", or on first use of shipkit.

## Overview

Scan-first approach: diagnose current state, report status, then fix issues interactively. Works for fresh installs and existing setups that need repair.

## Workflow

### Phase 1: Diagnose

Run these checks and collect results:

1. **Python** — `python3 --version` (must be 3.10+)
2. **Shipkit installed** — `shipkit --version` (should succeed)
3. **Shipkit home** — `shipkit doctor` (check if home directory exists and is valid)
4. **CLI tool installed** — detect which AI CLI tools are available:
   - Claude Code: `claude --version`
   - Kiro: `kiro-cli --version`
   - Gemini CLI: `gemini --version`
5. **Git** — `git --version` (required for commit/pr skills)
6. **GitHub CLI** — `gh --version` (optional, required for pr/review skills)
7. **Current project** — check if the current directory is a registered shipkit project

### Phase 2: Report Status

Display a status dashboard:

```
## Shipkit Setup Status

### Prerequisites
+ Python 3.12.0
+ Git 2.43.0
+ GitHub CLI 2.40.0

### AI CLI Tools
+ Claude Code v1.0 (primary)
  Kiro not installed (optional)

### Shipkit
+ Home: ~/.config/shipkit
+ Config: claude (default)
  Current directory: not registered

### Skills Available
  18 package skills (commit, pr, review, test, debug, ...)
  0 user skills
  0 plugins installed
```

**Constraints:**
- Use `+` for ready, `!` for issues, blank for info
- Show what's working before showing what's missing
- Don't overwhelm — group related items

### Phase 3: Fix Issues

Work through issues in dependency order.

#### 3.1 Missing CLI Tool

If no AI CLI tool is installed:

```
No AI CLI tool detected. Shipkit works with:

1. Claude Code (recommended) — https://docs.anthropic.com/en/docs/claude-code
   Install: npm install -g @anthropic-ai/claude-code

2. Kiro — https://kiro.dev
   Install via toolbox or package manager

Which would you like to set up?
```

Wait for user choice, then help install.

#### 3.2 Missing GitHub CLI

If gh is not installed (optional but recommended):

```
GitHub CLI (gh) enables the /pr and /review skills.
Install: brew install gh (macOS) or see https://cli.github.com

Want to install it now, or skip for later?
```

#### 3.3 Register Current Project

If the current directory is not a registered project:

```
This directory isn't registered as a shipkit project.

Register it now? This will:
  - Create a .shipkit marker file
  - Generate CLAUDE.md with guidelines rules and skill catalog
  - Set up slash commands in .claude/commands/

1. Yes, register with default template
2. Yes, with a specific template (python, typescript, ...)
3. No, skip for now
```

If yes, run `shipkit init` followed by `shipkit sync`.

#### 3.4 Configure Defaults

If this is the first time and no config exists:

```
Quick configuration (press Enter to accept defaults):

1. Primary CLI tool: claude (detected)
   Change? (claude/kiro/other)
```

Only ask about settings that need user input. If detection works, confirm and move on.

### Phase 4: Verify

Re-run Phase 1 diagnostics and show updated status.

If all items pass:

```
## Setup Complete

Your shipkit is ready. Try these:

  /commit     — smart git commits from diffs
  /pr         — create PRs with auto-generated descriptions
  /test       — generate tests for your code
  /review     — code review local changes
  /retro      — review session learnings

Run /shipkit for all available commands.
```

## Examples

### Fresh Install

```
User: "setup shipkit"
Agent: [runs diagnostics]

       "## Shipkit Setup Status

       ### Prerequisites
       + Python 3.12.0
       + Git 2.43.0
       ! GitHub CLI not installed

       ### AI CLI Tools
       + Claude Code v1.0

       ### Shipkit
       + Home: ~/.config/shipkit
         Current directory: not registered

       GitHub CLI enables /pr and /review skills.
       Install? (y/n/skip)"

User: "skip for now"
Agent: "OK. Register this directory as a project?
       1. Default template
       2. Python template
       3. Skip"

User: "1"
Agent: [runs shipkit init && shipkit sync]

       "## Setup Complete

       Project 'my-project' registered and synced.
       18 skills available as slash commands.

       Try: /commit, /pr, /test, /review"
```

### Existing Setup

```
User: "check my setup"
Agent: [runs diagnostics]

       "## Shipkit Setup Status

       + Python 3.12.0
       + Git 2.43.0
       + GitHub CLI 2.40.0
       + Claude Code v1.0
       + Shipkit home valid
       + Project: my-api (synced)
       + 18 package skills + 2 user skills

       Everything looks good. No issues found."
```
