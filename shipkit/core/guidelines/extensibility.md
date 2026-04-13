# Extensibility

How shipkit separates core content from user customizations.

## Content Layering

Shipkit compiles content from three layers (lowest to highest precedence):

1. **Package core** (`shipkit/core/`) — shipped with shipkit, updated via `git pull` or package upgrade
2. **User global** (`<home>/guidelines/`, `<home>/skills/`) — personal additions and overrides
3. **Project** (`<home>/projects/<name>/`) — project-specific overrides

Higher layers override lower layers. A guidelines rule in the user layer with the same filename as a package rule replaces it entirely. A skill with the same directory name replaces it.

## User Content Principle

The shipkit home directory (`~/.config/shipkit/`) is exclusively for user content. Core guidelines rules and skills live in the shipkit package and are never copied there. This means:

- **Updates are conflict-free** — upgrading shipkit updates core content automatically
- **User content is always additive** — user files add to or override package defaults
- **No merge conflicts** — the home directory never contains upstream files that could diverge

## Adding Personal Content

To add a personal guidelines rule:
1. Create a `.md` file in `<home>/guidelines/`
2. Run `shipkit sync` — it will be included in the compiled output

To add a personal skill:
1. Create a directory in `<home>/skills/<skill-name>/`
2. Add a `SKILL.md` file following the standard skill format
3. Run `shipkit sync` — it will appear as a slash command

## Project-Specific Overrides

Each registered project can have its own guidelines and skills in `<home>/projects/<name>/`:
- `guidelines/` — project-specific rules (e.g., "this project uses PostgreSQL")
- `skills/` — project-specific skills
- `knowledge/` — research, ADRs, decision logs
- `mcp.json` — project-specific MCP server overrides

## CLI Tool Targets

Shipkit compiles to different tool-native formats:
- **Claude Code** — CLAUDE.md + .mcp.json + .claude/commands/
- **Kiro** — .kiro/agents/ + .kiro/guidelines/ + .kiro/skills/
- **Others** — via compiler adapters

The shipkit content is tool-agnostic. The compiler handles the translation.
