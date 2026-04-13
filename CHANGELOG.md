# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- `shipkit alias` command: generate a shell alias to launch a project from any directory
  - `--install` flag to auto-append to ~/.zshrc or ~/.bashrc
  - `--project` flag to target a specific registered project
  - Uses `noglob` wrapper to prevent shell glob expansion of arguments
- GitHub Actions CI workflow: tests + lint on push/PR across Python 3.10–3.13
- End-to-end smoke tests covering full init → sync → verify pipeline
- CLI tests via Click's CliRunner for all commands
- CHANGELOG.md
- "Why Shipkit?" section in README highlighting three core superpowers:
  - Self-learning system that auto-improves from usage patterns
  - CLI-agnostic architecture (write once, compile to any tool)
  - Content layering that preserves customizations across updates
- Practical examples of shipping faster with built-in skills
- Extension guide (custom skills, plugins, project overrides)
- Badges to README: CI status, Python version, license
- Plugin marketplace system with registry support:
  - `plugin_registries` config in `~/.config/shipkit/config.yaml`
  - Default registry: `github.com/nille/shipkit-marketplace`
  - Install plugins by short name: `shipkit plugin install review-plus`
  - Users can add custom registries to config
  - Full URLs and local paths still supported
- `/contribute-skill` - automates submitting local skills to marketplace
  - Forks shipkit-marketplace repo
  - Creates plugin structure (plugin.yaml, README.md)
  - Submits PR automatically
  - Lowers barrier to community contributions

### Added (continued)
- Gemini CLI compiler for Google's Gemini CLI tool:
  - Generates GEMINI.md with steering rules and skill catalog
  - Generates .gemini/settings.json with hooks and MCP servers
  - Generates .gemini/commands/*.toml for each skill (TOML format)
  - Full hook support (SessionStart, SessionEnd, BeforeTool, AfterTool, etc.)
  - Self-learning loop compatible (retro-analyze, retro-auto hooks)
  - MCP server support
- OpenCode compiler for Anomaly's OpenCode tool:
  - Generates .opencode/plugins/shipkit-hooks.ts (TypeScript plugin wrapping Python hooks)
  - Generates .opencode/plugins/shipkit-tools.ts (custom tools from skills)
  - Generates opencode.json with plugin registration and MCP servers
  - Full hook support (session.created, session.idle, tool.execute.before/after)
  - Self-learning loop compatible (retro hooks work)
  - Plugin-based architecture (JS/TS wrappers around Python hooks)
- Documentation section on versioning personal content:
  - How to version ~/.config/shipkit/ with git
  - What to include (skills, steering, config) vs exclude (.state, plugins, projects)
  - Syncing across machines
  - Using dotfiles managers (chezmoi, yadm)
  - Sharing within teams
- `/sync-config` skill - automates backing up personal content:
  - Commits changes to skills, steering, config, templates
  - Pushes to git remote
  - Initializes git repo if needed
  - Guides user through remote setup if not configured
- Auto-create .gitignore in ~/.config/shipkit/:
  - Copied from seed/gitignore.sample during init
  - Excludes .state/, plugins/, projects/
  - Includes helpful comments on what to version

### Added (continued)
- Skill cascading and composition system:
  - Skills now cascade across layers by default (extends: true)
  - Higher layers extend lower layers rather than replacing them
  - Support for complete override (extends: false)
  - New skill_parser module for Agent Skills standard compliance
  - Layer markers in merged output show skill composition
  - References from all layers are merged
  - All 4 compilers updated to support cascading
- Agent Skills open standard compliance:
  - Follows https://agentskills.io/specification format
  - Compatible with 20+ tools (Claude Code, Cursor, Gemini CLI, etc.)
  - Custom 'extends' field for shipkit cascading (backward compatible)
  - Skills work across Agent Skills ecosystem

### Changed
- Quick Start now recommends `uv tool install shipkit` over pip
- Updated .gitignore to include .gemini/, .opencode/, GEMINI.md, opencode.json
- Skills now cascade by default instead of complete replacement
  - Package core → User global → Plugins → Project (each extends previous)
  - Breaking change: Skills are now composable, not replacements
  - To get old behavior: add 'extends: false' to your custom skills
- Steering rules now cascade by default (same extends mechanism)
  - Same filename in multiple layers = cascade with layer markers
  - Breaking change: Steering rules are now composable
  - Previously: all steering files concatenated (duplicates possible)
  - Now: Cascaded by filename with override support

## [0.1.0] - 2026-04-13

### Added
- Python CLI (`shipkit`) with commands: init, sync, status, doctor, run, projects, template, plugin
- Claude Code compiler: CLAUDE.md, .mcp.json, .claude/commands/, .claude/settings.json
- Kiro compiler: .kiro/steering/, .kiro/skills/, .kiro/agents/, .kiro/config/mcp.json, .kiro/hooks/
- 19 skills: commit, pr, review, research, test, debug, release, explain, refactor, scaffold, docs, deps, adr, ci, skill-builder, retro, shipkit, update, setup
- 8 steering rules: agent-behavior, safety-defaults, skill-loading-rules, sustainability, verification-rules, dev-principles, extensibility, subagent-catalog
- 5 hooks: context-inject, retro-analyze, retro-auto, session-save, update-check
- 3 subagent definitions: retro-analyzer, session-summarizer, retro-auto
- Plugin system (install/uninstall/list/update from local path or git)
- Content linter with 8 checks (json, skills, steering, hooks, subagents, plugins, pii, links)
- Content layering: package → plugins → user global → project → repo-native
- Project templates: default, python, typescript
- MIT license
