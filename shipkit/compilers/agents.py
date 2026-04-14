"""Agent configuration generation for custom shipkit-branded sessions.

Generates tool-specific agent configs that provide a branded "shipkit" experience
with pre-loaded skills, guidelines, and team context.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shipkit.compilers.base import CompileContext


def generate_kiro_agent(ctx: CompileContext) -> dict:
    """Generate Kiro agent configuration as JSON.

    Returns a dict conforming to:
    https://raw.githubusercontent.com/aws/amazon-q-developer-cli/refs/heads/main/schemas/agent-v1.json
    """
    # Build resources array - Kiro auto-loads files/skills referenced here
    resources = [
        # Core guidelines
        "file://.kiro/steering/core/*.md",
        # User personal guidelines
        "file://~/.kiro/steering/*.md",
        # Core skills
        "skill://.kiro/skills/core/**/SKILL.md",
        # User personal skills
        "skill://~/.kiro/skills/**/SKILL.md",
        # Plugin guidelines
        "file://~/.config/shipkit/plugins/*/guidelines/*.md",
        # Plugin skills
        "skill://~/.config/shipkit/plugins/*/skills/**/SKILL.md",
    ]

    return {
        "$schema": "https://raw.githubusercontent.com/aws/amazon-q-developer-cli/refs/heads/main/schemas/agent-v1.json",
        "name": "shipkit",
        "description": "Team productivity assistant with shared skills and guidelines",
        "prompt": _generate_system_prompt("Kiro"),
        "model": "claude-sonnet-4-6",
        "tools": ["*"],
        "allowedTools": [
            "read", "write", "shell", "glob", "subagent", "grep",
            "web_search", "web_fetch", "ls", "imageRead"
        ],
        "resources": resources,
        "hooks": {
            "agentSpawn": [
                {
                    "command": "echo 'Shipkit agent initialized'",
                    "description": "Agent initialization"
                }
            ]
        }
    }


def generate_claude_agent(ctx: CompileContext) -> str:
    """Generate Claude Code agent configuration as Markdown with YAML frontmatter."""

    # Skills to auto-load (just reference the discovery mechanism)
    # Claude Code will discover skills from .claude/skills/ and ~/.claude/skills/

    frontmatter = """---
name: shipkit
description: Team productivity assistant with shared skills and guidelines
model: sonnet
tools: "*"
permissionMode: acceptEdits
memory: user
initialPrompt: "I'm ready to help! Use /skill-name to invoke team skills, or ask me anything."
maxTurns: 50
color: blue
---"""

    body = _generate_system_prompt("Claude Code")

    return f"{frontmatter}\n\n{body}"


def generate_opencode_agent(ctx: CompileContext) -> str:
    """Generate OpenCode agent configuration as Markdown with YAML frontmatter."""

    frontmatter = """---
name: shipkit
description: Team productivity assistant with shared skills and guidelines
mode: primary
model: anthropic/claude-sonnet-4-20250514
temperature: 0.7
steps: 50
permission:
  edit: allow
  bash: allow
  webfetch: allow
  read: allow
  grep: allow
  glob: allow
  list: allow
color: "#4A90E2"
---"""

    body = _generate_system_prompt("OpenCode")

    return f"{frontmatter}\n\n{body}"


def generate_gemini_context_header(ctx: CompileContext) -> str:
    """Generate Gemini CLI context header to prepend to GEMINI.md.

    Since Gemini CLI doesn't have custom agents, we inject branding via GEMINI.md.
    """

    return f"""# Shipkit Agent Configuration

**Identity:** You are "Shipkit", a team productivity assistant.

{_generate_system_prompt("Gemini CLI")}

---

"""


def _generate_system_prompt(tool_name: str) -> str:
    """Generate the core system prompt for shipkit agents."""

    return f"""You are **Shipkit**, a productivity assistant for software development teams.

## Your Role

You help teams by:
- **Executing skills**: Team-shared workflows packaged as reusable commands (e.g., /commit, /pr, /review)
- **Following guidelines**: Team conventions, coding standards, and best practices
- **Enabling collaboration**: Skills and guidelines work across Claude Code, Kiro, Gemini CLI, and OpenCode

## How Skills Work

Skills are discovered at runtime from multiple locations:
1. **Core skills** (shipped with shipkit) - foundational workflows for all teams
2. **User personal skills** - your custom automations
3. **Plugin skills** - community and marketplace extensions
4. **Team skills** (in repo) - shared workflows committed to git

{_tool_specific_instructions(tool_name)}

## Guidelines Discovery

Guidelines (team conventions) are discovered from:
1. Core guidelines (shipped with shipkit)
2. Personal guidelines (your preferences)
3. Plugin guidelines (from marketplace)
4. Team guidelines (in repo, shared via git)

All layers are merged with higher layers taking precedence. You'll receive complete
discovery instructions showing exactly where to find skills and guidelines, and how
to cascade/merge them when multiple layers define the same item.

## Your Behavior

- **Be helpful and direct** - Focus on getting work done
- **Load skills on-demand** - Read skill definitions when invoked
- **Respect layer precedence** - Team overrides > Personal > Plugins > Core
- **Explain your reasoning** - When making non-obvious decisions
- **Ask when uncertain** - Don't assume requirements

## Team Identity

You are part of this team's workflow. When team members share skills via git or
marketplace, you help distribute that knowledge across the team - even when team
members use different AI coding tools.
"""


def _tool_specific_instructions(tool_name: str) -> str:
    """Generate tool-specific usage instructions."""

    if tool_name == "Claude Code":
        return """### Invoking Skills (Claude Code)

Skills are invoked with slash commands:
```
/commit              # Smart git commits
/pr                  # Generate pull requests
/review <pr>         # Code review
/skill-name          # Any custom skill
```

Use the Agent tool to spawn subagents when needed. Skills and guidelines are
discovered from `.claude/skills/` and `.claude/guidelines/` directories."""

    elif tool_name == "Kiro":
        return """### Invoking Skills (Kiro CLI)

Skills are referenced in the resources array and auto-loaded. The user can invoke
them naturally in conversation.

Skills and guidelines are discovered from `.kiro/skills/` and `.kiro/steering/`
directories. Note: Kiro uses "steering" instead of "guidelines"."""

    elif tool_name == "OpenCode":
        return """### Invoking Skills (OpenCode)

Skills can be invoked with slash commands or naturally in conversation:
```
/commit              # Smart git commits
/pr                  # Generate pull requests
```

Skills and guidelines are discovered from `.opencode/skills/` and
`.opencode/guidelines/` directories. Primary agents (like shipkit) can invoke
subagents using @mentions."""

    elif tool_name == "Gemini CLI":
        return """### Invoking Skills (Gemini CLI)

Skills are referenced in GEMINI.md context files and available for invocation.
The user can reference them naturally in conversation.

Skills and guidelines are discovered from `.gemini/skills/` and `.gemini/guidelines/`
directories through hierarchical GEMINI.md loading."""

    return ""


def write_kiro_agent(ctx: CompileContext, dry_run: bool = False) -> Path | None:
    """Write Kiro agent configuration to .kiro/agents/shipkit.json."""

    agent_config = generate_kiro_agent(ctx)
    agent_file = ctx.repo_path / ".kiro" / "agents" / "shipkit.json"

    if dry_run:
        return agent_file

    agent_file.parent.mkdir(parents=True, exist_ok=True)
    agent_file.write_text(json.dumps(agent_config, indent=2) + "\n")

    return agent_file


def write_claude_agent(ctx: CompileContext, dry_run: bool = False) -> Path | None:
    """Write Claude Code agent configuration to .claude/agents/shipkit.md."""

    agent_config = generate_claude_agent(ctx)
    agent_file = ctx.repo_path / ".claude" / "agents" / "shipkit.md"

    if dry_run:
        return agent_file

    agent_file.parent.mkdir(parents=True, exist_ok=True)
    agent_file.write_text(agent_config)

    return agent_file


def write_opencode_agent(ctx: CompileContext, dry_run: bool = False) -> Path | None:
    """Write OpenCode agent configuration to .opencode/agents/shipkit.md."""

    agent_config = generate_opencode_agent(ctx)
    agent_file = ctx.repo_path / ".opencode" / "agents" / "shipkit.md"

    if dry_run:
        return agent_file

    agent_file.parent.mkdir(parents=True, exist_ok=True)
    agent_file.write_text(agent_config)

    return agent_file


def enhance_gemini_md(ctx: CompileContext, existing_content: str, dry_run: bool = False) -> tuple[str, Path]:
    """Prepend shipkit branding to GEMINI.md content.

    Returns (enhanced_content, file_path).
    """

    header = generate_gemini_context_header(ctx)

    # If existing content doesn't already have shipkit header, prepend it
    if "# Shipkit Agent Configuration" not in existing_content:
        enhanced = header + existing_content
    else:
        enhanced = existing_content

    gemini_file = ctx.repo_path / "GEMINI.md"

    return enhanced, gemini_file
