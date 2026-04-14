# Shipkit

[![CI](https://github.com/nille/shipkit/actions/workflows/ci.yml/badge.svg)](https://github.com/nille/shipkit/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

CLI-agnostic AI dev productivity kit. Skills, guidelines, hooks, and MCP server configs that compile into tool-native configuration for Claude Code, Kiro, Gemini CLI, OpenCode, and other AI coding tools.

## Why Shipkit?

Most AI coding tools come with their own conventions: custom slash commands, tool-specific configs, proprietary skill systems. When you invest time customizing one tool, that work is locked in. Switch tools? Start from scratch.

**Shipkit flips this.** Write your workflows, preferences, and automation once. Compile to any AI coding CLI. Your investment moves with you.

### Three superpowers that compound over time:

**1. Self-learning system**  
Shipkit watches how you work and auto-improves. After each session, metadata is saved for review. Next session, you're nudged to analyze it — the agent identifies patterns, mistakes, and missing capabilities in-conversation where you can see everything. Approve suggestions and they become permanent guidelines or skill improvements. The more you use it, the better it gets at understanding *your* workflow.

```
Session N ends → metadata saved
Session N+1 starts → "You have 1 unanalyzed session. Say 'retro' to review"
You → "retro"
Agent → reads transcript, analyzes in-conversation (you see everything)
Agent → proposes: "Should I add this to guidelines?"
You → approve → guidelines/auto-learned.md updated
```

**Fully transparent** - you see the analysis happen and can guide it.

**2. CLI-agnostic architecture**  
Switching from Claude Code to Kiro? Trying out Gemini CLI or OpenCode? Your skills, guidelines, and learned preferences compile to whatever tool you're using. Same content, different output formats. No lock-in, no migration scripts, no starting over.

```bash
shipkit sync --tool claude    # Generates CLAUDE.md + .claude/commands/
shipkit sync --tool kiro      # Generates .kiro/skills/ + .kiro/guidelines/
shipkit sync --tool gemini    # Generates GEMINI.md + .gemini/commands/
shipkit sync --tool opencode  # Generates .opencode/plugins/ + opencode.json
```

**3. Content layering that never breaks**  
Updates to core skills don't overwrite your customizations. Content flows through layers — package core, user global, plugins, repo — with higher layers always winning. Your preferences are sacred. Updates bring new capabilities without touching your setup.

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

- **21 built-in skills** for commits, PRs, reviews, testing, debugging, research, releases, marketplace contributions, config backup
- **Add your own** in `~/.config/shipkit/skills/` — the `/skill-builder` helps you create them
- **Share with the community** — use `/contribute-skill` to submit your skills to the marketplace
- **Install community plugins** with `shipkit plugin install <plugin-name>`
- **Team-shared content** — commit skills/guidelines to your repo and share via git

### Teams can collaborate across different tools:

Your team doesn't need to standardize on one AI coding tool. Each developer uses their preferred tool, but everyone shares the same skills and workflows.

**Example:** Your team builds a custom `/deploy` skill for your production pipeline:

```
Alice (Claude Code) creates /deploy skill
   │
   ├─ Shares to marketplace (shipkit official or private): /contribute-skill deploy
   │
   ↓
Marketplace stores as tool-agnostic SKILL.md
   │
   ├──→ Bob (Kiro):        shipkit plugin install deploy → /deploy works ✅
   ├──→ Carol (Gemini):    shipkit plugin install deploy → /deploy works ✅
   └──→ David (OpenCode):  shipkit plugin install deploy → /deploy works ✅
```

**One skill, four tools, zero conversion.** The skill is stored in tool-agnostic markdown. Each developer's `shipkit sync` compiles it to their tool's native format. Team workflows stay consistent regardless of individual tool preferences.

## How It Works

Shipkit is a content compiler. You write [skills](#skills) and [guidelines](#guidelines) once, and `shipkit sync` generates the right files for whichever AI coding tool you use.

Content flows through three source layers, then compiles to your repo:

```
1. Package core     ← Built-in (ships with shipkit)
2. User global      ← Personal (~/.config/shipkit/)
3. Plugins          ← Marketplace (shipkit plugin install)
        ↓
   Compile & Merge
        ↓
4. Repo             ← Output (.claude/, .kiro/, etc.)
```

**How merging works:**
- Layers 1-3 are **sources** (read by shipkit)
- Layer 4 (repo) is **output** (written by shipkit)
- When writing to repo, shipkit preserves existing customizations
- You can commit repo content to share with your team via git

Higher source layers win on conflict. Repo content is protected from being overwritten.

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

# On first init, you'll be prompted:
# 🚀 Quick access: Install a shell alias?
#   Creates: alias sk='noglob shipkit run'
#   Install 'sk' alias? [Y/n]

# After install, use the short alias anywhere:
sk "add tests for the auth module"
sk "review my changes"
sk "create a PR"

# Or use the full command:
shipkit run
# → Auto-detects tool and launches: claude --agent shipkit
# → Or: kiro-cli chat --agent shipkit
# → Or: opencode --agent shipkit

# Compile configs without launching:
shipkit sync
shipkit alias sk --install
# Now just type 'sk' from any directory
```

After sync, your AI coding CLI has access to all skills as slash commands, guidelines in its system context, and MCP servers configured.

```bash
# Use language-specific templates
shipkit init --template python
shipkit init --template typescript

# Target a different CLI tool
shipkit sync --tool opencode
```

## Skills

21 skills ship with the package, available as slash commands.

**Shipkit follows the [Agent Skills open standard](https://agentskills.io/)** — skills use the same `SKILL.md` format as Claude Code, Cursor, Gemini CLI, OpenCode, and [20+ other tools](https://agentskills.io/home). This means skills from the broader Agent Skills ecosystem work in shipkit, and shipkit skills work in other compatible tools.

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
| `/sync-config` | Commit and push personal config to git remote for backup |
| `/migrate-tool` | Switch between AI coding tools — moves personal skills/guidelines |
| `/retro` | Session review, self-improvement, triage pending learnings |
| `/shipkit` | Natural language interface to shipkit CLI commands |
| `/update` | Self-update and re-sync all projects |

## Guidelines

Guidelines are behavioral guidelines compiled into the agent's system context. They shape how the agent works across all conversations — execution style, verification standards, development principles, and safety defaults.

**Think of guidelines as "house rules" for the agent.** They're always loaded, unlike skills which are activated on-demand.

### Core Guidelines

8 guidelines ship with the package:

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

### How Guidelines Work

**Guidelines are markdown files** that get compiled into `CLAUDE.md`, `GEMINI.md`, `.kiro/guidelines/`, etc.

Like skills, they **cascade across layers** - you can extend core rules with your own preferences:

```
Core:    dev-principles.md → "Ship small, test at boundaries"
User:    dev-principles.md → "Additionally, always use TypeScript strict mode"
Project: dev-principles.md → "For this API, follow REST conventions"
```

**Result:** Agent sees all three layers merged together.

### Adding Your Own Guidelines

**Global rule (all projects):**
```bash
cat > ~/.config/shipkit/guidelines/my-conventions.md << 'EOF'
# My Conventions

- Always use TypeScript strict mode
- Prefer functional components
- Use ruff for Python formatting
EOF
```

**Extend existing rule:**
```bash
cat > ~/.config/shipkit/guidelines/dev-principles.md << 'EOF'
---
extends: true  # Default - adds to core dev-principles
---

# Additional Principles

- Always write API tests before implementation
- Never commit commented-out code
EOF
```

**Replace existing rule:**
```bash
cat > ~/.config/shipkit/guidelines/dev-principles.md << 'EOF'
---
extends: false  # Ignore core, use only this
---

# Custom Dev Principles

My completely different development philosophy.
EOF
```

**Team-shared rule (commit to repo):**
```bash
# Create in your repo and commit via git
mkdir -p .shipkit/guidelines
cat > .shipkit/guidelines/api-rules.md << 'EOF'
# API Rules

- This project uses PostgreSQL — never suggest MySQL
- API responses follow JSON:API spec
- Rate limiting is handled by nginx
EOF

git add .shipkit/
# Team gets this via git pull
```

### When to Use Guidelines vs Skills

| Use Guidelines For | Use Skills For |
|------------------------|----------------|
| General behavior and principles | Specific workflows and tasks |
| Always-active guidance | On-demand capabilities |
| Cross-cutting concerns | Domain-specific operations |
| Development philosophy | Executable procedures |

**Example:**
- **Guidelines:** "Always write tests" (general principle, always applies)
- **Skill:** `/test` (specific action to generate tests)

### Precedence and Cascading

Guidelines follow the same precedence as skills:

1. **Package core** (lowest) - Built-in guidelines
2. **User global** - Your personal preferences  
3. **Plugins** (highest) - From installed plugins

**For team-shared guidelines:** Commit them to your repo (`.shipkit/guidelines/`) instead of using shipkit layers. Shipkit will read and merge repo content intelligently.

When the same filename exists in multiple layers:
- **`extends: true` (default):** All layers merged with markers
- **`extends: false`:** Only that layer, lower layers ignored

## Hooks

Background automation that runs at session boundaries:

| Hook | Event | Purpose |
|------|-------|---------|
| `context-inject` | Session start | Notifies about pending sessions, injects learned preferences |
| `update-check` | Session start | Checks PyPI for newer shipkit version (daily cache) |
| `session-save` | Session end | Saves session metadata for cross-session context |
| `retro-analyze` | Session end | Saves session metadata for interactive review |

### Self-Learning Loop

**Fully interactive and visible** - analysis happens in-conversation using your CLI tool:

1. **Session ends** → `retro-analyze` hook saves metadata to `.state/retro/pending/`
2. **Next session starts** → `context-inject` hook notifies: "You have 1 unanalyzed session"
3. **User says "retro"** → `/retro` skill is invoked
4. **Agent analyzes** in-conversation:
   - Reads pending session transcript
   - Identifies patterns, mistakes, improvements
   - **You see the analysis happen**
5. **Agent proposes** changes to guidelines/skills
6. **You approve/reject/modify**
7. **Agent updates** `guidelines/auto-learned.md` or skill files

**Why visible beats background:**
- Transparent - you see what's being learned
- Collaborative - you guide the analysis
- Trustworthy - no hidden background magic
- Universal - works with any LLM provider your tool supports (Bedrock, Ollama, models.dev, etc.)
- No separate API keys needed

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

See `seed/mcp.sample.json` for more examples.

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

Plugins can provide skills, guidelines, hooks, and subagents. They slot into the content layering as the third layer (after package core and user global).

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

## Skill Cascading and Composition

Skills can be extended and overridden across layers. When the same skill exists in multiple layers, shipkit merges them intelligently.

### How Cascading Works

By default, **skills cascade** - higher layers extend lower layers rather than replacing them:

```
Layer 1 (Package Core):    shipkit/core/skills/commit/SKILL.md
                          "Create conventional commits with semantic format"

Layer 2 (User Global):    ~/.config/shipkit/skills/commit/SKILL.md
                          "Additionally, always include ticket references"
                          
Layer 3 (Repo):           .shipkit/skills/commit/SKILL.md
                          "For this API, also update CHANGELOG.md"
```

**Result after `shipkit sync`:**
```markdown
<!-- Layer: package core -->
Create conventional commits with semantic format
...

---
<!-- Layer: user global -->
Additionally, always include ticket references
...

---
<!-- Layer: repo -->
For this API, also update CHANGELOG.md
...
```

The agent sees **all three layers** merged together, each marked with its source.

### Precedence Rules

When layers conflict, **higher layers take precedence:**

1. **Package core** (lowest) - Built-in skills shipped with shipkit
2. **User global** - Your personal preferences in `~/.config/shipkit/`
3. **Plugins** (highest) - Installed via `shipkit plugin install`

### Complete Override

To completely replace lower layers instead of extending, use `extends: false` in frontmatter:

```yaml
---
name: commit
description: Custom commit workflow
extends: false  # Ignore all lower layers
---

# My Complete Custom Workflow

This completely replaces the core commit skill.
No cascading with lower layers.
```

**Result:** Only this layer's content is used, lower layers are ignored.

### Use Cases

**Cascade (extends: true, default):**
- Add project-specific rules to core skills
- Layer team conventions on top of personal preferences
- Keep core behavior, add extras

**Override (extends: false):**
- Completely different workflow for this project
- Replace broken or incompatible core skill
- Start fresh without inherited behavior

### References Merging

`references/` directories from all layers are merged. If the same filename exists in multiple layers, higher layers win.

### Agent Skills Standard Compatibility

Shipkit's `extends` field is a **custom extension** - tools that don't understand it will simply ignore the frontmatter field and load the skill body. Skills remain compatible with the [Agent Skills open standard](https://agentskills.io/specification).

## Adding Personal Content

### Guidelines

```bash
# Global rule (applies to all projects)
cat > ~/.config/shipkit/guidelines/my-conventions.md << 'EOF'
# My Conventions

- Always use TypeScript strict mode
- Prefer functional components
- Use ruff for Python formatting
EOF

# Team-shared rule (commit to repo)
mkdir -p .shipkit/guidelines
cat > .shipkit/guidelines/api-rules.md << 'EOF'
# API Rules

- This project uses PostgreSQL — never suggest MySQL
- API responses follow JSON:API spec
EOF

git add .shipkit/
git commit -m "Add API guidelines for team"
# Team gets this via git pull

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
# Create from current project's guidelines + skills
shipkit template create my-stack

# Use when registering new projects
shipkit init --template my-stack

# List available
shipkit template list
```

## Versioning Your Personal Content

Your personal shipkit content (`~/.config/shipkit/`) represents significant investment: custom skills, guidelines, learned preferences, templates. You should version it.

### What to version:

```bash
cd ~/.config/shipkit
git init

# Version these directories
git add skills/          # Your custom skills
git add guidelines/        # Your behavioral rules (including auto-learned.md)
git add mcp.json         # MCP server configs
git add config.yaml      # Global settings
git add templates/       # Custom project templates
```

### What NOT to version:

```bash
# Add to .gitignore
echo ".state/" >> .gitignore       # Machine state (sessions, retro pending)
echo "plugins/" >> .gitignore      # Installed from git, not yours
echo "projects/" >> .gitignore     # Project paths are machine-specific
```

### Sync across machines:

```bash
# Initial setup - push to private repo
cd ~/.config/shipkit
git remote add origin git@github.com:yourname/my-shipkit-config.git
git push -u origin main

# On another machine - clone instead of init
rm -rf ~/.config/shipkit  # if exists
git clone git@github.com:yourname/my-shipkit-config.git ~/.config/shipkit
```

### Using dotfiles managers:

If you use [chezmoi](https://www.chezmoi.io/), [yadm](https://yadm.io/), or similar:

```bash
# Add shipkit config to your dotfiles
chezmoi add ~/.config/shipkit/skills/
chezmoi add ~/.config/shipkit/guidelines/
chezmoi add ~/.config/shipkit/config.yaml
```

### Share within your team:

Fork your personal config as a team starter:

```bash
# Team member clones your setup as a base
git clone git@github.com:yourname/my-shipkit-config.git ~/.config/shipkit
cd ~/.config/shipkit

# Add their own customizations
# Push to their own fork
git remote set-url origin git@github.com:teammate/their-shipkit-config.git
```

Your learned preferences (guidelines/auto-learned.md) are especially valuable to version - they represent the accumulated wisdom from all your sessions.

**Quick backup:** Use the `/sync-config` skill to commit and push your config in one command:

```
> /sync-config
✓ Config committed and pushed to remote
```

## CLI Reference

```
shipkit init [--template TYPE] [--name NAME]     Register current repo as a project
shipkit sync [--tool NAME] [--dry-run] [--all]   Compile to tool-native config (generates agents)
shipkit status                                   Show project info and sync status
shipkit run [PROMPT] [--tool TOOL] [--no-agent]  Sync + launch with custom shipkit agent
shipkit alias [NAME] [--install] [--project P]   Generate shell alias (global or project-specific)
shipkit migrate --to TOOL [--dry-run]            Migrate personal content between tools

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
| **Claude Code** | `CLAUDE.md`, `.mcp.json`, `.claude/settings.json`, **`.claude/agents/shipkit.md`** |
| **Kiro** | `.kiro/steering/`, `.kiro/agents/` (subagents + **shipkit.json**), `.kiro/config/mcp.json`, `.kiro/hooks/` |
| **Gemini CLI** | `GEMINI.md` (with shipkit branding), `.gemini/settings.json` |
| **OpenCode** | `AGENTS.md`, `opencode.json`, **`.opencode/agents/shipkit.md`**, `.opencode/plugins/shipkit-hooks.ts` |

Set your preferred tool globally, per-project (metadata only), or at sync time:

```yaml
# ~/.config/shipkit/config.yaml
cli_tool: claude  # or kiro, gemini, opencode

# ~/.config/shipkit/projects/<name>/project.yaml (tool preference only)
cli_tool: opencode
```

```bash
# Or override at sync time
shipkit sync --tool opencode
```

### Switching Tools

Want to switch from one AI coding tool to another? Shipkit makes it seamless.

**Auto-detection:** Shipkit notices when you're using a different tool and offers to migrate:

```
I notice you're using kiro but shipkit is configured for claude.
Want to migrate? Say 'migrate tool' or run /migrate-tool
```

**Interactive migration:**
```bash
/migrate-tool    # Guides you through switching tools interactively
```

**Direct migration:**
```bash
# Preview what will be migrated
shipkit migrate --to kiro --dry-run

# Migrate personal skills and guidelines
shipkit migrate --to kiro
```

**What gets migrated:**
- Personal skills: `~/.claude/skills/` → `~/.kiro/skills/`
- Personal guidelines: `~/.claude/guidelines/` → `~/.kiro/steering/`
- Config preference: `config.yaml` updated to new tool

**What stays the same:**
- Core content in `~/.config/shipkit/core/` (shared across all tools)
- Plugins in `~/.config/shipkit/plugins/` (shared across all tools)
- Project content in repos (team-shared via git)

**Note:** Kiro uses "steering" instead of "guidelines" - shipkit handles this automatically.

After migration, run `shipkit sync` to generate tool-native config files for the new tool.

## Architecture

```
~/.config/shipkit/                     SHIPKIT_HOME (configurable via env var)
├── config.yaml                        Global settings (cli_tool)
├── guidelines/                          Personal guidelines
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
│       ├── guidelines/                  Plugin guidelines
│       └── hooks/                     Plugin hooks
├── projects/
│   └── <name>/
│       └── project.yaml               Project metadata (repo path, template, cli_tool)
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
│       ├── guidelines/                  8 guidelines
│       ├── skills/                    21 skills
│       ├── hooks/                     5 hooks + shared lib
│       ├── subagents/                 3 subagent definitions
│       └── mcp.json                   Default MCP servers
├── seed/                              Copied to ~/.config/shipkit/ on first init
│   ├── mcp.sample.json
│   └── templates/                     default, python, typescript
└── tests/                             140 tests
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
