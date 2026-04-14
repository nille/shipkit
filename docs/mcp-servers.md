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
      "args": ["@playwright/mcp@latest", "--extension"]
    }
  }
}
```

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

### Option 2: Manual Configuration
Add to `~/.claude/mcp.json` (user-wide) or `.mcp.json` (project-specific).

### Option 3: Project-Specific
Add to your project's `.mcp.json` and commit to git for team sharing.

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
