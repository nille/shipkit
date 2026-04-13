# Shipkit

Run shipkit commands using natural language. Use when user wants to manage their shipkit configuration, register projects, sync configuration, check status, or manage templates.

## Overview

Maps natural language requests to shipkit CLI commands. Shipkit manages skills, steering rules, and MCP server configurations that compile into tool-native config files (CLAUDE.md, .mcp.json, etc.).

## Intent Mapping

| User says | Command |
|-----------|---------|
| "register this project", "init shipkit", "set up shipkit here" | `shipkit init` |
| "register as python project", "init with python template" | `shipkit init --template python` |
| "sync", "sync config", "update config", "compile config" | `shipkit sync` |
| "sync for kiro", "compile for kiro" | `shipkit sync --tool kiro` |
| "what would sync change", "preview sync" | `shipkit sync --dry-run` |
| "shipkit status", "show project info" | `shipkit status` |
| "list projects", "show all projects" | `shipkit projects list` |
| "health check", "check shipkit", "is shipkit working" | `shipkit doctor` |
| "what templates are available", "list templates" | `shipkit template list` |

## Workflow

### 1. Identify Intent

Match the user's request to a shipkit operation from the table above.

**Constraints:**
- If the intent is ambiguous, ask the user to clarify before running anything
- If the user mentions a template name, pass it via `--template`
- If the user mentions a specific CLI tool target, pass it via `--tool`

### 2. Run the Command

Execute the matched shipkit command via shell.

**Constraints:**
- Always show the user which command you're about to run
- Run the command and present the output
- If the command fails, read the error and suggest a fix

### 3. Follow-up Actions

After running the command, suggest logical next steps:

| After | Suggest |
|-------|---------|
| `shipkit init` | "Run `shipkit sync` to generate tool-native config" |
| `shipkit sync` | "Config is up to date. Your skills are available as slash commands." |
| `shipkit doctor` (with issues) | Specific fix for each issue found |

## Examples

### "Set up shipkit in this repo"

```
> Running: shipkit init
Project 'my-project' registered.
  Marker: .shipkit
  Run 'shipkit sync' to generate tool-native config.

> Running: shipkit sync
Written:
  + CLAUDE.md
  + .mcp.json
  + .claude/commands/commit.md
  + .claude/commands/pr.md

Config synced. Your skills are now available as slash commands.
```

### "What's my shipkit status?"

```
> Running: shipkit status
Shipkit home: ~/.config/shipkit
Project: my-api
  Repo: /Users/alice/Code/my-api
  Template: python
  Project steering: 2 files
  Project skills: 1
  Knowledge: 3 files
```
