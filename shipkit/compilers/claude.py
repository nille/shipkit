"""Claude Code compiler for shipkit.

Generates:
- CLAUDE.md (merged guidelines rules + skill catalog)
- .mcp.json (merged MCP server config)
- .claude/commands/<skill>.md (skills as custom slash commands)

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
        # Only compile: guidelines (with discovery instructions), MCP, hooks
        for step in [self._compile_claude_md, self._compile_mcp_json, self._compile_hooks]:
            w, s, warn = step(ctx, dry_run)
            written.extend(w)
            skipped.extend(s)
            warnings.extend(warn)

        return CompileResult(files_written=written, files_skipped=skipped, warnings=warnings)

    def _compile_claude_md(self, ctx: CompileContext, dry_run: bool) -> tuple[list, list, list]:
        written, skipped, warnings = [], [], []

        # Generate tool-specific discovery instructions
        from shipkit.compilers.discovery_template import generate_discovery_instructions
        discovery_instructions = generate_discovery_instructions(
            tool_name="Claude Code",
            tool_project_path=".claude/skills",
            tool_user_path="~/.claude/skills"
        )

        # Collect ALL layers of each guidelines rule by filename
        from shipkit.skill_parser import parse_guideline, cascade_guidelines

        guidelines_by_name: dict[str, list[Path]] = {}
        for guidelines_dir in ctx.guidelines_layers:
            if not guidelines_dir.exists():
                continue
            for md_file in sorted(guidelines_dir.glob("*.md")):
                # Skip skill-discovery.md (we generate it dynamically above)
                if md_file.name == "skill-discovery.md":
                    continue
                if md_file.name not in guidelines_by_name:
                    guidelines_by_name[md_file.name] = []
                guidelines_by_name[md_file.name].append(md_file)

        # Start with discovery instructions
        sections = [discovery_instructions]

        # Then cascade each guideline
        for filename in sorted(guidelines_by_name.keys()):
            guidelines_paths = guidelines_by_name[filename]
            guidelines_defs = [parse_guideline(p) for p in guidelines_paths]
            cascaded = cascade_guidelines(guidelines_defs)
            sections.append(cascaded)

        # Collect skill catalog from all layers, deduplicating by name
        # Higher layers override lower layers
        skills_by_name: dict[str, str] = {}
        for skills_dir in ctx.skills_layers:
            if not skills_dir.exists():
                continue
            for skill_dir in sorted(skills_dir.iterdir()):
                if not skill_dir.is_dir():
                    continue
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    first_line = skill_md.read_text().strip().split("\n")[0]
                    desc = first_line.lstrip("#").strip()
                    skills_by_name[skill_dir.name] = desc

        # Build managed section
        managed_parts = []
        if sections:
            managed_parts.append("\n\n---\n\n".join(sections))
        if skills_by_name:
            managed_parts.append("\n## Available Skills\n")
            for skill_name, desc in sorted(skills_by_name.items()):
                managed_parts.append(f"- **/{skill_name}** — {desc}")

        managed_content = "\n".join(managed_parts)

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

    def _compile_mcp_json(self, ctx: CompileContext, dry_run: bool) -> tuple[list, list, list]:
        written, skipped, warnings = [], [], []

        # Merge MCP configs from all layers (package → user → project)
        merged_servers = {}
        for mcp_path in ctx.mcp_layers:
            if not mcp_path.exists():
                continue
            data = json.loads(mcp_path.read_text())
            servers = data.get("mcpServers", data)
            if isinstance(servers, dict):
                merged_servers.update(servers)

        if not merged_servers:
            skipped.append(".mcp.json (no MCP servers configured)")
            return written, skipped, warnings

        # Repo-native entries take precedence (never overwritten)
        repo_mcp_path = ctx.repo_path / ".mcp.json"
        existing_servers = {}
        if repo_mcp_path.exists():
            existing = json.loads(repo_mcp_path.read_text())
            existing_servers = existing.get("mcpServers", {})

        for name, config in merged_servers.items():
            if name not in existing_servers:
                existing_servers[name] = config

        output = {"mcpServers": existing_servers}

        if dry_run:
            written.append(".mcp.json (dry-run)")
        else:
            repo_mcp_path.write_text(json.dumps(output, indent=2) + "\n")
            written.append(".mcp.json")

        return written, skipped, warnings

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
        written, skipped, warnings = [], [], []

        # Collect hook definitions from all layers, deduplicating by name
        hooks_by_name: dict[str, dict] = {}
        for hooks_dir in ctx.hooks_layers:
            if not hooks_dir.exists():
                continue
            for hook_file in sorted(hooks_dir.glob("*.yaml")):
                hook_def = self._parse_hook_yaml(hook_file)
                if hook_def:
                    hooks_by_name[hook_def["name"]] = hook_def

        if not hooks_by_name:
            return written, skipped, warnings

        # Build Claude Code hooks config grouped by event
        claude_hooks: dict[str, list] = {}
        for hook_def in hooks_by_name.values():
            event = hook_def.get("event", "")
            claude_event = self.HOOK_EVENT_MAP.get(event)
            if not claude_event:
                warnings.append(f"Unknown hook event '{event}' in {hook_def['name']}, skipped")
                continue

            # Resolve the command path — replace {shipkit_hooks_dir} with actual path
            command = hook_def.get("command", "")
            command = command.replace("{shipkit_hooks_dir}", str(PACKAGE_HOOKS_DIR))

            hook_entry = {
                "hooks": [{
                    "type": "command",
                    "command": command,
                    "timeout": hook_def.get("timeout", 120),
                }]
            }

            if claude_event not in claude_hooks:
                claude_hooks[claude_event] = []
            claude_hooks[claude_event].append(hook_entry)

        if not claude_hooks:
            return written, skipped, warnings

        # Read existing settings.json and merge hooks
        settings_dir = ctx.repo_path / ".claude"
        settings_path = settings_dir / "settings.json"

        existing_settings = {}
        if settings_path.exists():
            try:
                existing_settings = json.loads(settings_path.read_text())
            except json.JSONDecodeError:
                warnings.append("Could not parse existing .claude/settings.json, hooks not written")
                return written, skipped, warnings

        # Merge: existing hooks take precedence for same event
        existing_hooks = existing_settings.get("hooks", {})
        for event_name, hook_list in claude_hooks.items():
            if event_name not in existing_hooks:
                existing_hooks[event_name] = hook_list

        existing_settings["hooks"] = existing_hooks

        if dry_run:
            written.append(".claude/settings.json (dry-run)")
        else:
            settings_dir.mkdir(parents=True, exist_ok=True)
            settings_path.write_text(json.dumps(existing_settings, indent=2) + "\n")
            written.append(".claude/settings.json")

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

