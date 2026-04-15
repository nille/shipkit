"""Claude Code compiler for shipkit.

Generates:
- CLAUDE.md (merged guidelines rules + skill catalog)
- .claude/agents/shipkit.md (agent config with hooks + agent-scoped MCP servers)

Content layering (lowest → highest precedence):
  package core → user global → project → repo-native
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml

from shipkit.compilers.base import Compiler, CompileContext, CompileResult, PACKAGE_HOOKS_DIR, register_compiler

SENTINEL_BEGIN = "<!-- SHIPKIT:BEGIN — managed by shipkit, do not edit above SHIPKIT:END -->"
SENTINEL_END = "<!-- SHIPKIT:END -->"


@register_compiler("claude")
class ClaudeCodeCompiler(Compiler):

    @property
    def name(self) -> str:
        return "Claude Code"

    def compile(self, ctx: CompileContext, dry_run: bool = False) -> CompileResult:
        written = []
        skipped = []
        warnings = []

        # Skills are discovered at runtime via skill-discovery.md guideline
        # Compile: guidelines (with discovery instructions), hooks, agent config (with MCP)
        for step in [self._compile_claude_md, self._compile_hooks, self._compile_agent]:
            w, s, warn = step(ctx, dry_run)
            written.extend(w)
            skipped.extend(s)
            warnings.extend(warn)

        return CompileResult(files_written=written, files_skipped=skipped, warnings=warnings)

    def _compile_claude_md(self, ctx: CompileContext, dry_run: bool) -> tuple[list, list, list]:
        written, skipped, warnings = [], [], []

        # Generate tool-specific discovery instructions for both skills AND guidelines
        from shipkit.compilers.discovery_template import generate_discovery_instructions
        from shipkit.compilers.guideline_discovery_template import generate_guideline_discovery_instructions

        skill_discovery = generate_discovery_instructions(
            tool_name="Claude Code",
            tool_project_path=".claude/skills",
            tool_user_path="~/.claude/skills"
        )

        guideline_discovery = generate_guideline_discovery_instructions(
            tool_name="Claude Code",
            tool_project_path=".claude/guidelines",
            tool_user_path="~/.claude/guidelines"
        )

        # CLAUDE.md now contains ONLY discovery instructions (minimal bootstrap)
        # Agent will discover and read both skills and guidelines at runtime
        managed_content = f"{skill_discovery}\n\n---\n\n{guideline_discovery}"

        # Assemble full CLAUDE.md preserving user content
        claude_md_path = ctx.repo_path / "CLAUDE.md"
        user_content = ""
        if claude_md_path.exists():
            existing = claude_md_path.read_text()
            if SENTINEL_END in existing:
                _, _, user_content = existing.partition(SENTINEL_END)
                user_content = user_content.strip()
            elif SENTINEL_BEGIN not in existing:
                user_content = existing.strip()
                warnings.append("Existing CLAUDE.md was not shipkit-managed; preserved as user content below sentinel.")

        full_content = f"{SENTINEL_BEGIN}\n\n{managed_content}\n\n{SENTINEL_END}\n"
        if user_content:
            full_content += f"\n{user_content}\n"

        if dry_run:
            written.append("CLAUDE.md (dry-run)")
        else:
            claude_md_path.write_text(full_content)
            written.append("CLAUDE.md")

        return written, skipped, warnings

    def _collect_mcp_servers(self, ctx: CompileContext) -> dict:
        """Collect MCP servers from all layers for embedding in agent frontmatter.

        Returns a dict of {server_name: server_config} merged from all layers.
        """
        merged_servers = {}
        for mcp_path in ctx.mcp_layers:
            if not mcp_path.exists():
                continue
            data = json.loads(mcp_path.read_text())
            servers = data.get("mcpServers", data)
            if isinstance(servers, dict):
                merged_servers.update(servers)

        return merged_servers

    # Map shipkit hook events to Claude Code hook events
    HOOK_EVENT_MAP = {
        "session_start": "SessionStart",
        "session_end": "SessionEnd",
        "user_prompt_submit": "UserPromptSubmit",
        "stop": "Stop",
        "pre_tool_use": "PreToolUse",
        "post_tool_use": "PostToolUse",
    }

    def _compile_hooks(self, ctx: CompileContext, dry_run: bool) -> tuple[list, list, list]:
        """Compile hooks into agent definition (agent-scoped, not global).

        Hooks are added to .claude/agents/shipkit.md, not .claude/settings.json.
        This means hooks only run when using the shipkit agent, not in all Claude sessions.
        """
        # Hooks are now added to agent definition in _compile_agent()
        # This method is kept for backwards compatibility but does nothing
        return [], [], []

    def _compile_agent(self, ctx: CompileContext, dry_run: bool) -> tuple[list, list, list]:
        """Generate custom shipkit agent configuration with hooks and MCP servers."""
        from shipkit.compilers.agents import write_claude_agent_with_hooks

        written, skipped, warnings = [], [], []

        # Collect hook definitions
        hooks_by_name: dict[str, dict] = {}
        for hooks_dir in ctx.hooks_layers:
            if not hooks_dir.exists():
                continue
            for hook_file in sorted(hooks_dir.glob("*.yaml")):
                hook_def = self._parse_hook_yaml(hook_file)
                if hook_def:
                    hooks_by_name[hook_def["name"]] = hook_def

        # Collect MCP servers for agent-scoped embedding
        mcp_servers = self._collect_mcp_servers(ctx)

        agent_file = write_claude_agent_with_hooks(
            ctx, hooks_by_name, self.HOOK_EVENT_MAP, mcp_servers=mcp_servers, dry_run=dry_run,
        )
        if agent_file:
            if dry_run:
                written.append(".claude/agents/shipkit.md (dry-run)")
            else:
                written.append(".claude/agents/shipkit.md")

        return written, skipped, warnings

    @staticmethod
    def _parse_hook_yaml(path: Path) -> dict | None:
        """Parse a shipkit hook YAML definition."""
        try:
            data = yaml.safe_load(path.read_text())
            if isinstance(data, dict) and "name" in data and "event" in data:
                return data
        except Exception:
            pass
        return None

