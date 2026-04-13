# Shipkit

[![CI](https://github.com/nille/shipkit/actions/workflows/ci.yml/badge.svg)](https://github.com/nille/shipkit/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

CLI-agnostic AI dev productivity kit. Skills, steering rules, hooks, and MCP server configs that compile into tool-native configuration for Claude Code, Kiro, Gemini CLI, OpenCode, and other AI coding tools.

## Why Shipkit?

Most AI coding tools come with their own conventions: custom slash commands, tool-specific configs, proprietary skill systems. When you invest time customizing one tool, that work is locked in. Switch tools? Start from scratch.

**Shipkit flips this.** Write your workflows, preferences, and automation once. Compile to any AI coding CLI. Your investment moves with you.

### Three superpowers that compound over time:

**1. Self-learning system**  
Shipkit watches how you work and auto-improves. After each session, a background analyzer identifies patterns, mistakes, and missing capabilities. Next session, you're nudged to review suggestions — approve them and they become permanent steering rules or skill improvements. The more you use it, the better it gets at understanding *your* workflow.

```
Session N → background analysis → suggestions written
Session N+1 → "2 retro suggestions pending — say 'retro' to review"
You → approve → auto-learned.md updated → permanent behavior change
```

**2. CLI-agnostic architecture**  
Switching from Claude Code to Kiro? Trying out Gemini CLI or OpenCode? Your skills, steering rules, and learned preferences compile to whatever tool you're using. Same content, different output formats. No lock-in, no migration scripts, no starting over.

```bash
shipkit sync --tool claude    # Generates CLAUDE.md + .claude/commands/
shipkit sync --tool kiro      # Generates .kiro/skills/ + .kiro/steering/
shipkit sync --tool gemini    # Generates GEMINI.md + .gemini/commands/
shipkit sync --tool opencode  # Generates .opencode/plugins/ + opencode.json
```

**3. Content layering that never breaks**  
Updates to core skills don't overwrite your customizations. Content flows through five layers — package core, plugins, user global, project-specific, repo-native — with higher layers always winning. Your preferences are sacred. Updates bring new capabilities without touching your setup.

### Ship faster, every single day:

```bash
# Smart commits that explain the "why"
/commit

# Generate PRs from your commit history
/pr

# Structured code reviews (local diffs or GitHub PRs)
/review anthropics/claude-code#123

# Generate tests matching your project's conventions
/test

# Multi-source research with citations
/research "does Bedrock support fine-tuning Llama models?"

# Release with auto-generated changelogs
/release minor
```

Every skill runs in any supported tool. Write it once, use it everywhere.

### Extend without limits:

- **20 built-in skills** for commits, PRs, reviews, testing, debugging, research, releases, marketplace contributions
- **Add your own** in `~/.config/shipkit/skills/` — the `/skill-builder` helps you create them
- **Share with the community** — use `/contribute-skill` to submit your skills to the marketplace
- **Install community plugins** with `shipkit plugin install <plugin-name>`
- **Project-specific overrides** — per-repo steering rules that only apply where they matter

## How It Works

Shipkit is a content compiler. You write skills and rules once, and `shipkit sync` generates the right files for whichever AI coding tool you use.

Content flows through four layers (lowest to highest precedence):

```
Package core          ← ships with shipkit, updated via pip/git
  ↓ Plugins           ← community extensions
    ↓ User global     ← your personal additions in ~/.config/shipkit/
      ↓ Project       ← per-project overrides
        ↓ Repo-native ← existing tool config (never overwritten)
```

Each layer can add or override skills, steering rules, MCP servers, and hooks. Higher layers win on conflict. Your content is never touched by updates.

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | >= 3.10 | Runtime for shipkit itself |
| Git | any | Required by `/commit`, `/pr`, `/release` |
| An AI coding CLI | — | [Claude Code](https://claude.ai/code), [Kiro CLI](https://kiro.dev), [Gemini CLI](https://geminicli.com), or [OpenCode](https://opencode.ai) |

**Optional but recommended:**

| Tool | Used by |
|------|---------|
| [GitHub CLI (`gh`)](https://cli.github.com) | `/pr`, `/review` — creating and reviewing pull requests |
| [Node.js](https://nodejs.org) | MCP servers (Playwright, Context7, GitHub) |

## Quick Start

```bash
# Install
uv tool install shipkit
# or: pip install shipkit
# or: git clone <repo> && cd shipkit && uv sync

# Register a project (auto-creates ~/.config/shipkit/ on first use)
cd ~/Code/my-project
shipkit init

# Compile to tool-native config
shipkit sync

# Or: sync + launch your CLI tool
shipkit run

# Create a shell alias to launch from anywhere
shipkit alias sk --install
# Now just type 'sk' from any directory
```

After sync, your AI coding CLI has access to all skills as slash commands, steering rules in its system context, and MCP servers configured.

```bash
# Use language-specific templates
shipkit init --template python
shipkit init --template typescript

# Target a different CLI tool
shipkit sync --tool opencode
```

## Skills

20 skills ship with the package, available as slash commands:

### Core

| Skill | Purpose |
|-------|---------|
| `/commit` | Smart git commits — analyzes diffs, conventional format, explains why |
| `/pr` | Create PRs with auto-generated title and description from commits |
| `/review` | Structured code review for local diffs or pull requests |
| `/test` | Generate tests matching your project's framework and conventions |
| `/debug` | Systematic debugging — reproduce, isolate, fix |
| `/research` | Multi-source technical research with citations and confidence |
| `/release` | Version bump, changelog generation, tagging (SemVer/CalVer) |
| `/explain` | Code, architecture, and system behavior explanations |

### Extended

| Skill | Purpose |
|-------|---------|
| `/refactor` | Guided refactoring with safety checks and rollback |
| `/scaffold` | Project scaffolding from templates and conventions |
| `/docs` | Generate or update documentation |
| `/deps` | Dependency audit, updates, and security scanning |
| `/adr` | Create Architectural Decision Records |
| `/ci` | CI/CD pipeline setup and troubleshooting |

### Meta

| Skill | Purpose |
|-------|---------|
| `/setup` | First-time configuration wizard — diagnose, report, fix |
| `/skill-builder` | Create and improve shipkit skills |
| `/contribute-skill` | Submit local skills to marketplace — fork, PR, automate |
| `/retro` | Session review, self-improvement, triage pending learnings |
| `/shipkit` | Natural language interface to shipkit CLI commands |
| `/update` | Self-update and re-sync all projects |

## Steering Rules

Behavioral rules compiled into the agent's context on every sync. These shape how the agent works across all conversations.

| Rule | Purpose |
|------|---------|
| `agent-behavior` | Execution style, verification, ambiguity handling, hook directives |
| `safety-defaults` | Risk flagging, tool verification, plan approval gates |
| `skill-loading-rules` | Always read skill definitions before executing |
| `sustainability` | Circuit breaker, confidence tiers, cognitive budget |
| `verification-rules` | Source trust hierarchy, claim verification, depth tiers |
| `dev-principles` | Ship small, test at boundaries, prefer simple |
| `extensibility` | How content layering works, adding personal content |
| `subagent-catalog` | Available background agents and when they run |

## Hooks

Background automation that runs at session boundaries:

| Hook | Event | Purpose |
|------|-------|---------|
| `context-inject` | Session start | Injects learned preferences, retro nudges, session history |
| `update-check` | Session start | Checks PyPI for newer shipkit version (daily cache) |
| `retro-auto` | Session start | Promotes learnable rules from observations to steering/skills |
| `session-save` | Session end | Saves session metadata for cross-session context |
| `retro-analyze` | Session end | Analyzes transcript for improvement suggestions |

### Autonomous Learning Loop

Shipkit includes a self-improvement system that learns from your sessions:

1. **retro-analyze** hook runs after each session, identifying patterns and improvement opportunities
2. Findings are classified by severity (high/medium/low) and saved to `.state/retro/`
3. **retro-auto** hook runs at next session start, promoting learnable rules:
   - Cross-cutting rules → `steering/auto-learned.md`
   - Skill-specific rules → `skills/<name>/learned.md`
   - Structural changes stay in pending for manual `/retro` triage
4. **context-inject** hook surfaces pending items and learned preferences at session start

## Subagents

Three background agents handle the autonomous learning loop:

| Agent | Model | Purpose |
|-------|-------|---------|
| `retro-analyzer` | Sonnet | Analyzes transcripts, emits suggestions and observations |
| `session-summarizer` | Haiku | Generates session titles and summaries |
| `retro-auto` | Sonnet | Promotes learnable rules, consolidates auto-learned content |

These run headless via hooks — they're not invoked directly.

## MCP Servers

Shipkit ships with Playwright and Context7 MCP server defaults. Customize in `~/.config/shipkit/mcp.json`:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    }
  }
}
```

Per-project overrides go in `<home>/projects/<name>/mcp.json`. See `seed/mcp.sample.json` for more examples.

## Plugins

Extend shipkit with community plugins from the [marketplace](https://github.com/nille/shipkit-marketplace):

```bash
# Install by short name (searches marketplace)
shipkit plugin install review-plus

# Install from git URL
shipkit plugin install https://github.com/user/shipkit-plugin-auth

# Install from local path
shipkit plugin install ~/Code/my-plugin

# Manage
shipkit plugin list
shipkit plugin update review-plus
shipkit plugin uninstall review-plus
```

Plugins can provide skills, steering rules, hooks, and subagents. They slot into the content layering between user global and project layers.

### Plugin Registries

By default, shipkit searches `github.com/nille/shipkit-marketplace` for plugins. Add custom registries in `~/.config/shipkit/config.yaml`:

```yaml
cli_tool: claude
plugin_registries:
  - github.com/nille/shipkit-marketplace
  - github.com/your-org/custom-plugins
```

### Plugin Structure

A plugin is a directory with a `plugin.yaml` manifest:

```yaml
name: my-plugin
description: What this plugin does
author: your-name
version: 1.0.0
```

## Adding Personal Content

### Steering rules

```bash
# Global rule (applies to all projects)
cat > ~/.config/shipkit/steering/my-conventions.md << 'EOF'
# My Conventions

- Always use TypeScript strict mode
- Prefer functional components
- Use ruff for Python formatting
EOF

# Project-specific rule
cat > ~/.config/shipkit/projects/my-api/steering/api-rules.md << 'EOF'
# API Rules

- This project uses PostgreSQL — never suggest MySQL
- API responses follow JSON:API spec
EOF

# Recompile
shipkit sync
```

### Skills

Create a directory in `~/.config/shipkit/skills/<name>/` with a `SKILL.md`:

```
~/.config/shipkit/skills/deploy/
├── SKILL.md          # Skill definition (required)
└── references/       # Supporting docs (optional)
    └── runbook.md
```

### Project templates

```bash
# Create from current project's steering + skills
shipkit template create my-stack

# Use when registering new projects
shipkit init --template my-stack

# List available
shipkit template list
```

## CLI Reference

```
shipkit init [--template TYPE] [--name NAME]   Register current repo as a project
shipkit sync [--tool NAME] [--dry-run] [--all] Compile to tool-native config
shipkit status                                 Show project info and sync status
shipkit run [PROMPT]                           Sync + launch AI coding CLI
shipkit alias <name> [--install] [--project P] Generate shell alias for a project

shipkit projects list                          List all registered projects
shipkit doctor [--lint] [--check NAME]         Health check + content validation
shipkit template list                          List available templates
shipkit template create <name>                 Save current project as template

shipkit plugin install <source> [--name NAME]  Install plugin from git URL or path
shipkit plugin uninstall <name>                Remove a plugin
shipkit plugin list                            List installed plugins
shipkit plugin update <name>                   Update plugin from git
```

## Multi-Tool Support

Shipkit compiles to:

| Tool | Generated Files |
|------|----------------|
| **Claude Code** | `CLAUDE.md`, `.mcp.json`, `.claude/commands/`, `.claude/settings.json` |
| **Kiro** | `.kiro/steering/`, `.kiro/skills/`, `.kiro/agents/`, `.kiro/config/mcp.json`, `.kiro/hooks/` |
| **Gemini CLI** | `GEMINI.md`, `.gemini/settings.json`, `.gemini/commands/*.toml` |
| **OpenCode** | `opencode.json`, `.opencode/plugins/shipkit-hooks.ts`, `.opencode/plugins/shipkit-tools.ts` |

Set your preferred tool globally, per-project, or at sync time:

```yaml
# ~/.config/shipkit/config.yaml
cli_tool: claude  # or kiro, gemini, opencode

# ~/.config/shipkit/projects/<name>/project.yaml
cli_tool: opencode
```

```bash
# Or override at sync time
shipkit sync --tool opencode
```

## Architecture

```
~/.config/shipkit/                     SHIPKIT_HOME (configurable via env var)
├── config.yaml                        Global settings (cli_tool)
├── steering/                          Personal steering rules
│   └── auto-learned.md                Cross-cutting auto-learned preferences
├── skills/                            Personal skills
│   └── <name>/
│       ├── SKILL.md                   Skill definition
│       └── learned.md                 Auto-learned skill-specific rules
├── mcp.json                           Global MCP server additions
├── templates/                         Project templates
├── plugins/                           Installed plugins
│   └── <name>/
│       ├── plugin.yaml                Plugin manifest
│       ├── skills/                    Plugin skills
│       ├── steering/                  Plugin steering rules
│       └── hooks/                     Plugin hooks
├── projects/
│   └── <name>/
│       ├── project.yaml               Project config (repo path, template, cli_tool)
│       ├── steering/                   Project-specific rules
│       ├── skills/                     Project-specific skills
│       ├── knowledge/                  Research, ADRs, decisions
│       └── mcp.json                   Project MCP overrides
└── .state/                            Machine-managed (not user-facing)
    ├── sessions/                      Session records for cross-session context
    ├── retro/
    │   ├── observations.jsonl         Low-severity pattern tracking
    │   ├── pending/                   Suggestions awaiting review
    │   └── processed/                 Applied/discarded suggestions
    └── debounce/                      Hook execution state
```

```
shipkit (Python package)
├── shipkit/
│   ├── cli.py                         Click-based CLI
│   ├── config.py                      Config loading (ShipkitConfig, ProjectConfig, ResolvedConfig)
│   ├── datadir.py                     Home directory management (ensure_home, resolve_home)
│   ├── project.py                     Project registration and resolution
│   ├── sync.py                        Sync orchestration
│   ├── plugin.py                      Plugin install/uninstall/list
│   ├── lint.py                        Content validation (8 checks)
│   ├── compilers/
│   │   ├── base.py                    CompileContext, Compiler ABC, content layering
│   │   ├── claude.py                  Claude Code compiler
│   │   ├── kiro.py                    Kiro compiler
│   │   ├── gemini.py                  Gemini CLI compiler
│   │   └── opencode.py                OpenCode compiler
│   └── content/                       Core content (ships with package)
│       ├── steering/                  8 steering rules
│       ├── skills/                    20 skills
│       ├── hooks/                     5 hooks + shared lib
│       ├── subagents/                 3 subagent definitions
│       └── mcp.json                   Default MCP servers
├── seed/                              Copied to ~/.config/shipkit/ on first init
│   ├── mcp.sample.json
│   └── templates/                     default, python, typescript
└── tests/                             102 tests
```

## Development

```bash
# Install in dev mode
uv sync

# Run tests
pytest tests/ -v

# Run content validation
python -m shipkit.lint

# Run specific lint check
python -m shipkit.lint skills
python -m shipkit.lint --list
```

## License

MIT
