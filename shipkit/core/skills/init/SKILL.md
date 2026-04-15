---
name: init
description: Initialize shipkit for the current project. Detects tech stack, recommends and configures MCP servers, and runs sync. Use when user says "init", "initialize", "set up this project", or on first use in a new project.
---

# Initialize Project

Set up shipkit for the current project directory. Detects the project's tech stack and walks the user through selecting MCP servers relevant to this project.

## When To Use

- First time using shipkit in a project
- When the shipkit agent suggests running `/init` (auto-detected new project)
- When user wants to add or change MCP servers for a project
- When user says "init", "initialize", "set up this project"

## Workflow

### Step 1: Verify Prerequisites

Confirm we're in a git repo and shipkit is installed globally:

```bash
git rev-parse --show-toplevel
shipkit --version
```

If not a git repo, tell the user to run `git init` first.
If shipkit isn't installed, point them to `shipkit install`.

### Step 2: Check Existing State

Check what's already configured for this project:

```bash
# Check if already initialized
test -f .claude/agents/shipkit.md && echo "Agent exists" || echo "No agent"
test -f .claude/mcp.json && echo "MCP config exists" || echo "No MCP config"
test -f CLAUDE.md && echo "CLAUDE.md exists" || echo "No CLAUDE.md"
```

If `.claude/mcp.json` already exists, read it and show current MCP servers.
Ask: "Update existing config or start fresh?"

### Step 3: Detect Tech Stack

Scan the project root for tech stack indicators:

**Check for these files (use Glob, not find):**

| File | Indicates |
|------|-----------|
| `package.json` | Node.js — read it to detect frameworks (React, Vue, Next.js, Express, etc.) |
| `tsconfig.json` | TypeScript |
| `pyproject.toml` | Python — read it to detect frameworks (Flask, Django, FastAPI, etc.) |
| `requirements.txt` | Python |
| `Cargo.toml` | Rust |
| `go.mod` | Go |
| `Gemfile` | Ruby |
| `pom.xml` | Java (Maven) |
| `build.gradle` | Java/Kotlin (Gradle) |
| `*.sln` or `*.csproj` | .NET/C# |
| `docker-compose.yml` | Docker/containers |
| `prisma/schema.prisma` | Database (Prisma ORM) |
| `*.sql` files | Database |

**Check git remote:**

```bash
git remote get-url origin 2>/dev/null
```

If it's a `github.com` URL, note this for GitHub MCP recommendation.

**Present findings:**

```
Detected tech stack:
  - Python (pyproject.toml, FastAPI)
  - PostgreSQL (sqlalchemy in dependencies)
  - GitHub remote (github.com/team/api-service)
  - Docker (docker-compose.yml)
```

### Step 4: Recommend MCP Servers

Based on the detected tech stack, recommend relevant MCP servers. Present as a selection list with recommendations pre-checked.

**Recommendation rules:**

| Condition | Recommend | Why |
|-----------|-----------|-----|
| GitHub remote detected | GitHub MCP | Enhances /pr and /review skills |
| Any project | Brave Search | Powers /research skill |
| `package.json` with test deps (jest, vitest, playwright) | Playwright MCP | Browser testing automation |
| Database deps (sqlalchemy, prisma, pg, mysql2, diesel) | Postgres or SQLite MCP | Direct DB queries |
| Any project | Filesystem MCP | Enhanced file operations |

**Do NOT recommend by default** (only if user asks):
- Slack (privacy concerns)
- Linear (requires paid account)

**Present selection:**

```
Recommended MCP servers for this project:

  [x] GitHub - View/create PRs and issues
      Uses your GITHUB_TOKEN

  [x] Brave Search - Web search for /research skill
      Free API key: https://brave.com/search/api/

  [ ] Filesystem - Enhanced file operations
      No API key needed

  [ ] Playwright - Browser automation for testing
      Requires: Node.js

Select servers to install, or skip MCP setup:
```

Pre-check servers that match the detected stack. Let user toggle.

### Step 5: Configure Selected MCPs

For each selected MCP server:

#### 5.1 Check Prerequisites

- **Node.js required?** Check `which node`. If missing and needed, warn the user.
- **API key required?** Check if the relevant env var exists.

#### 5.2 Guide API Key Setup

For each MCP that needs an API key:

```
GitHub MCP needs GITHUB_TOKEN.

Checking... Found $GITHUB_TOKEN in environment.
Use this token? (y/n)
```

If not found:

```
GitHub MCP needs GITHUB_TOKEN.

Options:
  1. Create a new token: https://github.com/settings/tokens
     Scopes needed: repo, read:org
  2. Skip GitHub MCP (add later with /init)

Enter token, or skip:
```

**IMPORTANT:** Never store raw API key values in `.claude/mcp.json`. Use environment variable references (`${GITHUB_TOKEN}`) so tokens aren't committed to git.

#### 5.3 Write Project MCP Config

Write `.claude/mcp.json` with the selected servers:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "${BRAVE_API_KEY}"
      }
    }
  }
}
```

**IMPORTANT:** This file goes in `.claude/mcp.json` (project-level, git-committed).
It is NOT `~/.claude/mcp.json` (global) and NOT `~/.config/shipkit/mcp.json` (user-level).

Project MCP config is the highest precedence layer — it overrides user-level defaults.

### Step 6: Sync Project

Run sync to compile the MCP config into the agent:

```bash
shipkit sync
```

This generates/updates `.claude/agents/shipkit.md` with the MCP servers embedded in the agent frontmatter.

### Step 7: Summary

Present what was configured:

```
Project initialized!

  Tech stack: Python (FastAPI), PostgreSQL, Docker
  MCP servers configured: 2
    + GitHub (using $GITHUB_TOKEN)
    + Brave Search (using $BRAVE_API_KEY)

  Files created/updated:
    + .claude/mcp.json (project MCP config)
    + .claude/agents/shipkit.md (agent with embedded MCPs)
    + CLAUDE.md (skill/guideline discovery)

  MCP servers are agent-scoped — they only activate when using
  the shipkit agent, not in regular Claude Code sessions.

  To add more MCP servers later, run /init again.
```

## MCP Server Reference

Quick reference for common MCP server configurations:

### GitHub
```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}" }
}
```
Requires: Node.js, GITHUB_TOKEN

### Brave Search
```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-brave-search"],
  "env": { "BRAVE_API_KEY": "${BRAVE_API_KEY}" }
}
```
Requires: Node.js, BRAVE_API_KEY (free at https://brave.com/search/api/)

### Filesystem
```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"]
}
```
Requires: Node.js

### Playwright
```json
{
  "command": "npx",
  "args": ["-y", "@playwright/mcp@latest"]
}
```
Requires: Node.js

### PostgreSQL
```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-postgres", "${DATABASE_URL}"]
}
```
Requires: Node.js, DATABASE_URL

### SQLite
```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-sqlite", "--db-path", "./db.sqlite"]
}
```
Requires: Node.js

## Key Principles

- **Detect, don't guess** — Scan the actual project before recommending
- **Env vars, not raw tokens** — Never commit secrets to `.claude/mcp.json`
- **Project-level config** — Write to `.claude/mcp.json`, not global config
- **Idempotent** — Running /init again updates existing config safely
- **Respect existing setup** — If MCPs already configured, show and offer to update
