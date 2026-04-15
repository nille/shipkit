# Shipkit

[![CI](https://github.com/nille/shipkit/actions/workflows/ci.yml/badge.svg)](https://github.com/nille/shipkit/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Stop configuring Claude Code. Start shipping.**

Production-grade Claude Code setup with 21 battle-tested skills, self-learning capabilities, and team workflows—built by a developer with 20+ years in the trenches. Zero FOMO, maximum productivity.

## Why Shipkit?

**Tired of Twitter threads telling you what you're missing?** Every day there's a new Claude Code tip, a new config hack, a must-have setup tweak. You're either constantly reconfiguring or watching your productivity fall behind.

**Shipkit solves this once and for all.** You get a production-grade Claude Code setup built by someone who's been shipping AI agent tooling since day one. 21 skills, hooks, MCP servers, and a self-learning system that adapts to your workflow—all tested in real production environments.

**For solo developers:** You're instantly ahead of 95% of Claude Code users. No more setup FOMO, no more copying configs from Reddit threads. Just the best setup, ready to go.

**For teams:** Everyone gets the same powerful baseline. Share custom skills via git. Build team conventions that actually stick.

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

**2. Dual learning systems**
- **Pattern Learner:** Detects repeated workflows (command sequences, file patterns) → Creates automation skills
- **Retro:** Learns your preferences and conventions → Updates behavioral guidelines
- **Together:** Skills automate WHAT you do, guidelines shape HOW you work

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

**You're not missing out—you're ahead.** These skills took months to build and refine in real production workflows.

### Extend without limits:

- **21 built-in skills** for commits, PRs, reviews, testing, debugging, research, releases, marketplace contributions, config backup
- **Add your own** in `~/.claude/skills/` — the `/skill-builder` helps you create them
- **Share with the community** — use `/contribute-skill` to submit your skills to the marketplace
- **Install community plugins** with `shipkit plugin install <plugin-name>`
- **Team-shared content** — commit skills/guidelines to your repo and share via git

### Teams get shared workflows:

Build custom skills once, share them via git. Everyone on your team gets the same capabilities automatically.

**Example:** Your team builds a custom `/deploy` skill for your production pipeline:

```
Alice creates /deploy skill in team repo
   │
   ├─ Commits to .claude/skills/deploy/
   │
   ↓
Everyone else pulls and runs shipkit sync
   │
   ├──→ Bob:     /deploy works ✅
   ├──→ Carol:   /deploy works ✅
   └──→ David:   /deploy works ✅
```

**Team workflows, git-based distribution.** Commit skills and guidelines to your repo. Everyone on the team gets them through git pull + shipkit sync.

## Built by someone who's been there from day one

Shipkit isn't a weekend project or a viral Twitter thread. It's 20+ years of software engineering experience applied to AI agents since the early days. Every skill, every hook, every design decision comes from real production use—not theory, not hype, not FOMO bait.

You're getting the setup I wish existed when I started. Battle-tested, opinionated, and always improving.

## How It Works

Shipkit is a layered content system for Claude Code. Skills and guidelines flow through multiple layers, with team-specific content always winning.

### Layer Architecture

```
📦 Package Layers (pip-installed)
│
├─ Core (always included)          ← 21 battle-tested skills
├─ Experimental (opt-in)           ← Cutting-edge, may change
└─ Advanced (opt-in)               ← Domain-specific, niche tools
         ↓
🌐 Marketplace (on-demand)
   └─ Community plugins             ← github.com/nille/shipkit-marketplace
         ↓
👤 User Personal (~/.claude/)
   ├─ skills/                       ← Your custom skills
   └─ guidelines/                   ← Your preferences
         ↓
👥 Team (.claude/ in repo)
   ├─ skills/                       ← Team workflows (git-committed)
   └─ guidelines/                   ← Team conventions (git-committed)
         ↓
   🎯 Compiled Output
   └─ CLAUDE.md + .claude/agents/shipkit.md
```

**Precedence:** Team overrides User, User overrides Marketplace, Marketplace overrides Package.

**Layer Selection:** Run `shipkit install` to choose which package layers (Core, Experimental, Advanced) to enable.

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | >= 3.10 | Runtime for shipkit itself |
| Git | any | Required by `/commit`, `/pr`, `/release` |
| Claude Code | latest | Get it at [claude.ai/code](https://claude.ai/code) |

**Optional but recommended:**

| Tool | Used by |
|------|---------|
| [GitHub CLI (`gh`)](https://cli.github.com) | `/pr`, `/review` — creating and reviewing pull requests |
| [Node.js](https://nodejs.org) | MCP servers (Playwright, Context7, GitHub) |

## Quick Start

```bash
# 1. Install shipkit (uv recommended, pip also works)
uv tool install shipkit  # or: pip install shipkit

# 2. Run the interactive installer
shipkit install

# The installer will:
# - Scan your existing Claude Code setup
# - Safely merge Shipkit (preserves your config)
# - Let you choose which skill sets to enable:
#   [x] Core - Battle-tested essentials (recommended)
#   [ ] Experimental - Cutting-edge features
#   [ ] Advanced - Specialized tools
# - Install hooks to ~/.claude/settings.json
# - Create shipkit agent
# - Offer to install shell alias

# 3. Use shipkit in any git repo
cd ~/Code/my-project
shipkit sync              # Generates .claude/ config for this project
shipkit run               # Launches: claude --agent shipkit

# Or use the 'sk' alias (if you installed it):
sk "add tests for auth module"
sk "review my changes"
sk "create a PR"

# Browse available skills:
/skills                   # In any shipkit session
```

After sync, your AI coding CLI has access to all skills as slash commands, guidelines in its system context, and MCP servers configured.


## Skills

21 skills ship with the package, available as slash commands.

**Shipkit follows the [Agent Skills open standard](https://agentskills.io/)** — skills use the same `SKILL.md` format as Claude Code, Cursor, and other compatible tools. This means skills from the broader Agent Skills ecosystem work in shipkit.

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

**Guidelines are markdown files** that get compiled into `CLAUDE.md` for Claude Code.

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
cat > ~/.claude/guidelines/my-conventions.md << 'EOF'
# My Conventions

- Always use TypeScript strict mode
- Prefer functional components
- Use ruff for Python formatting
EOF
```

**Extend existing rule:**
```bash
cat > ~/.claude/guidelines/dev-principles.md << 'EOF'
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
cat > ~/.claude/guidelines/dev-principles.md << 'EOF'
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

Intelligent automation that runs at session boundaries. Shipkit ships with 8 production hooks:

### 🔒 Safety & Quality

| Hook | Event | Purpose |
|------|-------|---------|
| **`pre-commit-safety`** | Pre-tool-use | **Hybrid regex + LLM scanner** - Prevents secrets, debug code, merge conflicts from being committed. Context-aware: distinguishes test fixtures from real secrets. |

### 🧠 Two Complementary Learning Systems

Shipkit learns from your work in two ways:

**Pattern Learner → Automate Tasks (Skills)**
- Detects repeated **command sequences** and **file edit patterns**
- After 3+ occurrences: "Create /restart-service skill?"
- **Output:** New skills that automate workflows
- **Example:** You run the same 5 debug commands → Becomes `/debug-auth` skill

**Retro → Learn Behaviors (Guidelines)**
- Detects **preferences**, **mistakes**, **conventions**
- You say "retro" → Interactive analysis → Approve suggestions
- **Output:** Updated guidelines that shape all future work
- **Example:** You always validate at API boundaries → Guideline reminder

**TL;DR:** Pattern Learner automates WHAT you do (tasks → skills). Retro learns HOW you work (behaviors → guidelines).

| Hook | Event | Purpose |
|------|-------|---------|
| **`pattern-learner`** | Session end | Detects repeated workflows, suggests skill automation |
| `retro-analyze` | Session end | Saves session metadata for interactive retrospectives |
| `retro-auto` | Session start | Auto-promotes learnable rules from retro suggestions |
| **`session-goals`** | Session start/end | Prompts for goals at start, tracks accomplishments at end |

### 📊 Context & Coordination

| Hook | Event | Purpose |
|------|-------|---------|
| `context-inject` | Session start | Injects cross-session context and learned preferences |
| `session-save` | Session end | Saves session metadata for cross-session memory |
| `update-check` | Session start | Daily check for shipkit updates (non-blocking) |

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

Shipkit ships with Playwright and Context7 MCP server defaults. Customize in `~/.claude/mcp.json` or project-level in `.mcp.json`:

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

By default, shipkit searches `github.com/nille/shipkit-marketplace` for plugins. Add custom registries in shipkit config:

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

Layer 2 (User Global):    ~/.claude/skills/commit/SKILL.md
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
cat > ~/.claude/guidelines/my-conventions.md << 'EOF'
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

Create a directory in `~/.claude/skills/<name>/` with a `SKILL.md`:

```
~/.claude/skills/deploy/
├── SKILL.md          # Skill definition (required)
└── references/       # Supporting docs (optional)
    └── runbook.md
```

## Versioning Your Personal Content

Your personal skills and guidelines in `~/.claude/` represent valuable accumulated knowledge. You should version them.

### What to version:

```bash
cd ~/.claude
git init

# Version your custom content
git add skills/           # Your custom skills
git add guidelines/       # Your preferences (including auto-learned.md)
git add mcp.json          # MCP server configs (if customized)

# Shipkit metadata (optional)
cd ~/.config/shipkit
git init
git add config.yaml       # Layer preferences
```

### Using dotfiles managers:

If you use [chezmoi](https://www.chezmoi.io/), [yadm](https://yadm.io/), or similar:

```bash
# Add Claude Code content to your dotfiles
chezmoi add ~/.claude/skills/
chezmoi add ~/.claude/guidelines/
chezmoi add ~/.config/shipkit/config.yaml
```

### Sync across machines:

```bash
# Push your ~/.claude/ content
cd ~/.claude
git remote add origin git@github.com:yourname/my-claude-config.git
git push -u origin main

# On another machine
cd ~/.claude
git init
git remote add origin git@github.com:yourname/my-claude-config.git
git pull origin main
```

Your learned preferences from pattern-learner and retro hooks are especially valuable - they represent accumulated wisdom from hundreds of sessions.

**Quick backup:** Use the `/sync-config` skill to commit and push your config in one command:

```
> /sync-config
✓ Config committed and pushed to remote
```

## CLI Reference

```bash
# Installation
shipkit install                                    # Interactive LLM-powered installer
                                                   # (scans existing setup, safely merges)

# Daily usage
shipkit sync [--dry-run]                           # Compile layers to Claude Code config
shipkit run [PROMPT] [--no-agent]                  # Sync + launch claude --agent shipkit
shipkit status                                     # Show layers, paths, current directory
shipkit alias [NAME] [--install]                   # Generate shell alias (default: sk)

# Plugins
shipkit plugin install <name|url>                  # Install from marketplace or git URL
shipkit plugin list                                # Show installed plugins
shipkit plugin uninstall <name>                    # Remove a plugin

# Maintenance
shipkit doctor [--lint] [--check NAME]             # Health check + content validation
```

**Key differences:**
- `install` not `init` - LLM handles complex merging
- No `--tool` flag - Claude Code only
- No project registry - works in any git repo
- `run` launches branded shipkit agent

## Architecture

### Directory Structure

```
~/.claude/                             Claude Code native (user content)
├── skills/                            Your custom skills
│   └── <name>/SKILL.md
├── guidelines/                        Your preferences
│   └── auto-learned.md                From pattern-learner and retro hooks
├── agents/shipkit.md                  Generated by shipkit sync
├── settings.json                      Hooks installed here
└── mcp.json                           MCP server configs (optional)

~/.config/shipkit/                     Shipkit metadata and core content
├── config.yaml                        Layer preferences (core, experimental, advanced)
├── core/                              Core content (copied during install)
│   ├── skills/                        21 battle-tested skills
│   ├── guidelines/                    8 core guidelines
│   └── hooks/                         8 production hooks
├── experimental/                      Experimental content (if enabled)
│   ├── skills/
│   └── guidelines/
├── advanced/                          Advanced content (if enabled)
│   ├── skills/
│   └── guidelines/
├── plugins/                           Installed marketplace plugins
│   └── <name>/
│       ├── plugin.yaml
│       ├── skills/
│       ├── guidelines/
│       └── hooks/
└── .state/                            Machine state (not user-facing)
    ├── patterns/                      Pattern learner storage
    ├── sessions/                      Session goals tracking
    ├── retro/pending/                 Suggestions awaiting review
    └── marketplace-cache/             Cached plugin index

.claude/                               Team content (git-committed)
├── skills/                            Team workflows
├── guidelines/                        Team conventions
└── agents/shipkit.md                  Generated by shipkit sync
```

### Package Structure

```
shipkit (pip-installed)
├── cli.py                             Commands: install, sync, run, status, plugin, alias
├── config.py                          ShipkitConfig (layer preferences)
├── sync.py                            Orchestrates compilation
├── compilers/
│   ├── base.py                        CompileContext (layered discovery)
│   ├── claude.py                      Claude Code compiler
│   └── agents.py                      Agent config generation
├── core/                              Core layer (always included)
│   ├── skills/                        21 battle-tested skills
│   ├── guidelines/                    8 core guidelines
│   └── hooks/                         8 production hooks
├── experimental/                      Experimental layer (opt-in)
│   ├── skills/
│   └── guidelines/
├── advanced/                          Advanced layer (opt-in)
│   ├── skills/
│   └── guidelines/
└── tests/                             141 tests
```

### Layer Precedence

When compiling:
1. Core (always)
2. Experimental (if enabled in config)
3. Advanced (if enabled in config)
4. Marketplace plugins
5. User personal (~/.claude/)
6. Team (.claude/ in repo) - **highest priority**

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
