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

### Changed
- Quick Start now recommends `uv tool install shipkit` over pip

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
