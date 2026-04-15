"""Agent configuration generation for custom shipkit-branded Claude Code sessions.

Generates Claude Code agent config that provides a branded "shipkit" experience
with pre-loaded skills, guidelines, and team context.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shipkit.compilers.base import CompileContext


def generate_claude_agent(ctx: CompileContext) -> str:
    """Generate Claude Code agent configuration as Markdown with YAML frontmatter."""

    # Skills to auto-load (just reference the discovery mechanism)
    # Claude Code will discover skills from .claude/skills/ and ~/.claude/skills/

    from shipkit import __version__

    # Build frontmatter with simple initialPrompt
    # ASCII art breaks YAML parsing, so keep prompt simple
    frontmatter = f"""---
name: shipkit
description: Production-grade Claude Code assistant with battle-tested skills and self-learning capabilities
model: sonnet
tools: "*"
permissionMode: acceptEdits
memory: user
initialPrompt: "Shipkit v{__version__} ready! Use /skill-name to invoke skills, or ask me anything."
maxTurns: 50
color: pink
---"""

    body = _generate_system_prompt()

    return f"{frontmatter}\n\n{body}"


def _generate_system_prompt() -> str:
    """Generate the core system prompt for shipkit agent."""

    return """You are **Shipkit**, a production-grade productivity assistant for Claude Code.

## Your Role

You provide a battle-tested Claude Code experience with:
- **21+ pre-built skills**: Smart workflows for commits, PRs, reviews, testing, research, releases
- **Self-learning system**: Pattern detection that suggests automation based on YOUR workflows
- **Pre-commit safety**: Prevents secrets and debug code from being committed
- **Guidelines**: Best practices and conventions that shape all your work

**You're not just an assistant—you're a continuously improving development environment.**

## How Skills Work

Skills are powerful workflows you can invoke with slash commands:
```
/commit              # Smart git commits with conventional format
/pr                  # Generate PRs from commit history
/review <pr>         # Structured code reviews
/test                # Generate tests matching your conventions
/research "query"    # Multi-source research with citations
/release minor       # Version bumps with changelog
```

Skills are discovered from multiple layers (highest precedence first):
1. **Project skills** - In `.claude/skills/` (team-shared via git)
2. **Personal skills** - In `~/.claude/skills/` (your customizations)
3. **Plugin skills** - From marketplace
4. **Core skills** - Shipped with shipkit (battle-tested)

### Discovery Process

When user invokes `/skill-name`:
1. Use Glob to search all layer locations
2. If found in multiple layers, merge according to `extends:` frontmatter
3. Read the SKILL.md and execute its workflow
4. Follow the skill's instructions exactly

Complete discovery instructions are provided in CLAUDE.md.

## Guidelines

Guidelines shape HOW you work across all conversations:
- Core guidelines (shipped with shipkit)
- Personal guidelines (your preferences)
- Auto-learned guidelines (from retro analysis and pattern detection)
- Project guidelines (team conventions)

These are always loaded—you'll receive complete context showing active guidelines.

## Your Behavior

- **Ship quality code** - Focus on correctness, security, and best practices
- **Be direct** - No fluff, just get work done
- **Learn continuously** - Pattern learner and retro systems improve over time
- **Respect user preferences** - Layer precedence means personal choices always win
- **Execute skills properly** - Always read SKILL.md before executing
- **Ask when uncertain** - Don't guess requirements

## Self-Learning

Two systems learn from your work:
1. **Pattern Learner** - Detects repeated workflows → Suggests creating skills
2. **Retro** - Analyzes sessions → Updates guidelines with learned behaviors

This means your shipkit setup continuously adapts to YOUR workflow, not generic templates.

## Key Principle

You're here to make Claude Code exceptional for software development—fast workflows, safe practices, continuous learning. Everything else is secondary.
"""


def generate_claude_agent_with_hooks(
    ctx: CompileContext,
    hooks_by_name: dict[str, dict],
    hook_event_map: dict[str, str],
    mcp_servers: dict[str, dict] | None = None,
) -> str:
    """Generate Claude Code agent configuration with agent-scoped hooks and MCP servers."""
    from shipkit import __version__
    from shipkit.config import SHIPKIT_HOME

    # Build frontmatter with hooks
    hook_config = {}
    for hook_def in hooks_by_name.values():
        event = hook_def.get("event", "")
        claude_event = hook_event_map.get(event)
        if not claude_event:
            continue

        command = hook_def.get("command", "")
        if "{shipkit_hooks_dir}" in command:
            user_hooks_dir = SHIPKIT_HOME / "core" / "hooks"
            command = command.replace("{shipkit_hooks_dir}", str(user_hooks_dir))

        if claude_event not in hook_config:
            hook_config[claude_event] = []

        hook_config[claude_event].append({
            "type": "command",
            "command": command,
            "timeout": hook_def.get("timeout", 120),
        })

    # Build YAML frontmatter with hooks and MCP servers
    import yaml
    frontmatter_data = {
        "name": "shipkit",
        "description": f"Shipkit v{__version__} — Production-grade Claude Code assistant with battle-tested skills and self-learning capabilities",
        "model": "sonnet",
        "tools": "*",
        "permissionMode": "acceptEdits",
        "memory": "user",
        "initialPrompt": f"Shipkit v{__version__} ready! Use /skill-name to invoke skills, or ask me anything.",
        "maxTurns": 50,
        "color": "orange",
    }

    # Add hooks if any
    if hook_config:
        frontmatter_data["hooks"] = hook_config

    # Add agent-scoped MCP servers (inline definitions)
    # Format: list of {name: {type: stdio, command: ..., args: [...]}}
    if mcp_servers:
        mcp_list = []
        for server_name, server_config in mcp_servers.items():
            # Build inline MCP definition matching Claude Code's expected format
            inline_def = {"type": "stdio"}
            if "command" in server_config:
                inline_def["command"] = server_config["command"]
            if "args" in server_config:
                inline_def["args"] = server_config["args"]
            if "env" in server_config:
                inline_def["env"] = server_config["env"]
            mcp_list.append({server_name: inline_def})
        frontmatter_data["mcpServers"] = mcp_list

    frontmatter = "---\n" + yaml.dump(frontmatter_data, default_flow_style=False, sort_keys=False) + "---"

    body = _generate_system_prompt()
    agent_config = f"{frontmatter}\n\n{body}"

    return agent_config


def write_claude_agent_with_hooks(
    ctx: CompileContext,
    hooks_by_name: dict[str, dict],
    hook_event_map: dict[str, str],
    mcp_servers: dict[str, dict] | None = None,
    dry_run: bool = False,
) -> Path | None:
    """Write Claude Code agent configuration with agent-scoped hooks and MCP servers."""
    agent_config = generate_claude_agent_with_hooks(ctx, hooks_by_name, hook_event_map, mcp_servers)
    agent_file = ctx.repo_path / ".claude" / "agents" / "shipkit.md"

    if dry_run:
        return agent_file

    agent_file.parent.mkdir(parents=True, exist_ok=True)
    agent_file.write_text(agent_config)

    return agent_file


def write_claude_agent(ctx: CompileContext, dry_run: bool = False) -> Path | None:
    """Write Claude Code agent configuration to .claude/agents/shipkit.md."""
    # Backwards compatibility wrapper
    return write_claude_agent_with_hooks(ctx, {}, {}, dry_run=dry_run)
