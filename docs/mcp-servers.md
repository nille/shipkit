# MCP Server Guide

MCP (Model Context Protocol) servers extend Claude's capabilities by connecting to external services and tools.

## Recommended MCP Servers for Shipkit

### Essential (Free, Low Friction)

#### Brave Search
**Powers:** `/research` skill with live web search  
**API Key:** Free at https://brave.com/search/api/  
**Setup:**
```json
{
  "mcpServers": {
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

Add to ~/.claude/settings.json:
```json
{
  "env": {
    "BRAVE_API_KEY": "your-key-here"
  }
}
```

#### Filesystem
**Powers:** Enhanced file operations, workspace awareness  
**API Key:** None  
**Setup:**
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/your/workspace"]
    }
  }
}
```

#### GitHub
**Powers:** `/pr`, `/review` skills with live PR/issue data  
**API Key:** Your existing `GITHUB_TOKEN`  
**Setup:**
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

### Development Tools

#### Playwright
**Powers:** Browser automation, testing  
**Requires:** Node.js  
**Best for:** Web development  
**Setup:**
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-playwright"]
    }
  }
}
```

**Note:** There are two Playwright MCP packages:
- `@anthropic-ai/mcp-server-playwright` (Anthropic official, recommended)
- `@playwright/mcp` (needs `--extension` flag for Chrome bridge)

**Chrome MCP Bridge (Advanced):**
Playwright MCP can connect to your real Chrome browser using the [Chrome MCP Bridge extension](https://chromewebstore.google.com/detail/playwright-mcp-bridge/mmlmfjhmonkocbjadbfplnigmagldckm).

**Benefits:**
- Use your logged-in browser sessions (no test authentication)
- Access real cookies, localStorage, session state
- Test with actual user context

**Setup:**
1. Install [Chrome extension](https://chromewebstore.google.com/detail/playwright-mcp-bridge/mmlmfjhmonkocbjadbfplnigmagldckm)
2. Add Playwright MCP with `--extension` flag (see config above)
3. Open Chrome, ensure extension shows green icon (connected)
4. Use `/browser-test` skill (Advanced layer) to leverage this

**Use cases:**
- Test authenticated flows without login automation
- Debug issues in your actual browser context
- Record user actions and generate test code

#### SQLite
**Powers:** Local database queries  
**API Key:** None  
**Best for:** Projects using SQLite  
**Setup:**
```json
{
  "mcpServers": {
    "sqlite": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sqlite", "--db-path", "/path/to/database.db"]
    }
  }
}
```

### Team/Productivity

#### Linear
**Powers:** Issue tracking integration  
**API Key:** LINEAR_API_KEY  
**Best for:** Teams using Linear  
**Setup:**
```json
{
  "mcpServers": {
    "linear": {
      "command": "npx",
      "args": ["-y", "@linear/mcp-server"],
      "env": {
        "LINEAR_API_KEY": "${LINEAR_API_KEY}"
      }
    }
  }
}
```

#### Slack
**Powers:** Team communication, notifications  
**API Key:** SLACK_BOT_TOKEN  
**Best for:** Team coordination  
**Setup:**
```json
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": ["-y", "@anthropics/mcp-server-slack"],
      "env": {
        "SLACK_BOT_TOKEN": "${SLACK_BOT_TOKEN}"
      }
    }
  }
}
```

## Installation Methods

### Option 1: During `shipkit install`
The installer will offer to set up popular MCPs interactively.
MCPs are saved to `~/.config/shipkit/mcp.json` and compiled into the shipkit agent during `shipkit sync`.

### Option 2: Manual Configuration
Add to `~/.config/shipkit/mcp.json`, then run `shipkit sync` to compile into the agent.

### Option 3: Project-Specific
Add to your project's `.mcp.json` and commit to git for team sharing.

## How MCP Scoping Works

Shipkit MCP servers are **agent-scoped** — they are compiled into `.claude/agents/shipkit.md`
as inline `mcpServers` definitions. This means:

- MCPs only activate when using the shipkit agent (`claude --agent shipkit`)
- They do NOT pollute your global Claude Code sessions
- Each MCP server starts when the agent starts and disconnects when it finishes
- API keys are still configured in `~/.claude/settings.json` under `env`

The MCP config flows through layers (lowest to highest precedence):
1. Package core (`~/.config/shipkit/core/mcp.json`)
2. Plugins (`~/.config/shipkit/plugins/*/mcp.json`)
3. User preferences (`~/.config/shipkit/mcp.json`)

## Testing MCP Servers

After installation, verify MCPs work:

```bash
# Test a server responds
echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}' | npx -y @modelcontextprotocol/server-github
```

Should return JSON response with server capabilities.

## Popular Combinations

### Research-Heavy Work
- Brave Search (web search)
- GitHub (code search)

### Full-Stack Development
- GitHub (PRs, issues)
- Playwright (browser testing)
- Postgres/SQLite (database queries)

### Team Lead
- GitHub (PR management)
- Linear (issue tracking)
- Slack (team communication)

### Solo Developer (Minimal)
- Brave Search (for /research)
- GitHub (for /pr)

## More MCPs

Browse the full catalog: https://github.com/modelcontextprotocol/servers

## Troubleshooting

**"Command not found: npx"**
→ Install Node.js: https://nodejs.org

**"MCP server timeout"**
→ Check API key is set correctly in ~/.claude/settings.json

**"Permission denied"**
→ Check file paths (database, filesystem MCPs)

**"Rate limited"**
→ Check API key quota (Brave Search, GitHub, etc.)
