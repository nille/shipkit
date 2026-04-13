"""Gemini CLI compiler for shipkit.

Generates:
- GEMINI.md (merged guidelines rules + skill catalog)
- .gemini/settings.json (hooks + MCP servers)
- .gemini/commands/<skill>.toml (skills as custom commands)

Content layering (lowest → highest precedence):
  package core → user global → project → repo-native

Based on Gemini CLI docs: https://geminicli.com/
Hook events: SessionStart, SessionEnd, BeforeAgent, AfterAgent, BeforeModel, AfterModel, etc.
"""

from __future__ import annotations

import json
from pathlib import Path

from shipkit.compilers.base import Compiler, CompileContext, CompileResult, PACKAGE_HOOKS_DIR, register_compiler

SENTINEL_BEGIN = "<!-- SHIPKIT:BEGIN — managed by shipkit, do not edit above SHIPKIT:END -->"
SENTINEL_END = "<!-- SHIPKIT:END -->"


@register_compiler("gemini")
class GeminiCliCompiler(Compiler):

    @property
    def name(self) -> str:
        return "Gemini CLI"

    def compile(self, ctx: CompileContext, dry_run: bool = False) -> CompileResult:
        written = []
        skipped = []
        warnings = []

        for step in [self._compile_gemini_md, self._compile_settings_json, self._compile_commands]:
            w, s, warn = step(ctx, dry_run)
            written.extend(w)
            skipped.extend(s)
            warnings.extend(warn)

        return CompileResult(files_written=written, files_skipped=skipped, warnings=warnings)

    def _compile_gemini_md(self, ctx: CompileContext, dry_run: bool) -> tuple[list, list, list]:
        """Generate GEMINI.md with guidelines rules and skill catalog."""
        written, skipped, warnings = [], [], []

        # Collect ALL layers of each guidelines rule by filename
        from shipkit.skill_parser import parse_guidelines, cascade_guidelines

        guidelines_by_name: dict[str, list[Path]] = {}
        for guidelines_dir in ctx.guidelines_layers:
            if not guidelines_dir.exists():
                continue
            for md_file in sorted(guidelines_dir.glob("*.md")):
                if md_file.name not in guidelines_by_name:
                    guidelines_by_name[md_file.name] = []
                guidelines_by_name[md_file.name].append(md_file)

        # Cascade each guidelines rule
        sections = []
        for filename in sorted(guidelines_by_name.keys()):
            guidelines_paths = guidelines_by_name[filename]
            guidelines_defs = [parse_guidelines(p) for p in guidelines_paths]
            cascaded = cascade_guidelines(guidelines_defs)
            sections.append(cascaded)

        # Collect skill catalog from all layers, deduplicating by name
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

        # Assemble full GEMINI.md preserving user content
        gemini_md_path = ctx.repo_path / "GEMINI.md"
        user_content = ""
        if gemini_md_path.exists():
            existing = gemini_md_path.read_text()
            if SENTINEL_END in existing:
                _, _, user_content = existing.partition(SENTINEL_END)
                user_content = user_content.strip()
            elif SENTINEL_BEGIN not in existing:
                user_content = existing.strip()
                warnings.append("Existing GEMINI.md was not shipkit-managed; preserved as user content below sentinel.")

        full_content = f"{SENTINEL_BEGIN}\n\n{managed_content}\n\n{SENTINEL_END}\n"
        if user_content:
            full_content += f"\n{user_content}\n"

        if dry_run:
            written.append("GEMINI.md (dry-run)")
        else:
            gemini_md_path.write_text(full_content)
            written.append("GEMINI.md")

        return written, skipped, warnings

    # Map shipkit hook events to Gemini CLI hook events
    HOOK_EVENT_MAP = {
        "session_start": "SessionStart",
        "session_end": "SessionEnd",
        "user_prompt_submit": "BeforeAgent",  # Closest match
        "stop": "SessionEnd",  # Gemini doesn't have separate stop event
        "pre_tool_use": "BeforeTool",
        "post_tool_use": "AfterTool",
    }

    def _compile_settings_json(self, ctx: CompileContext, dry_run: bool) -> tuple[list, list, list]:
        """Generate .gemini/settings.json with hooks and MCP servers."""
        written, skipped, warnings = [], [], []

        # Collect hook definitions from all layers
        hooks_by_name: dict[str, dict] = {}
        for hooks_dir in ctx.hooks_layers:
            if not hooks_dir.exists():
                continue
            for hook_file in sorted(hooks_dir.glob("*.yaml")):
                hook_def = self._parse_hook_yaml(hook_file)
                if hook_def:
                    hooks_by_name[hook_def["name"]] = hook_def

        # Build Gemini CLI hooks config grouped by event
        gemini_hooks: dict[str, list] = {}
        for hook_def in hooks_by_name.values():
            event = hook_def.get("event", "")
            gemini_event = self.HOOK_EVENT_MAP.get(event)
            if not gemini_event:
                warnings.append(f"Unknown hook event '{event}' in {hook_def['name']}, skipped")
                continue

            # Resolve the command path
            command = hook_def.get("command", "")
            command = command.replace("{shipkit_hooks_dir}", str(PACKAGE_HOOKS_DIR))

            hook_entry = {
                "matcher": "*",  # Match all patterns
                "hooks": [{
                    "type": "command",
                    "command": command,
                    "timeout": hook_def.get("timeout", 120),
                }]
            }

            if gemini_event not in gemini_hooks:
                gemini_hooks[gemini_event] = []
            gemini_hooks[gemini_event].append(hook_entry)

        # Merge MCP configs from all layers
        merged_mcp_servers = {}
        for mcp_path in ctx.mcp_layers:
            if not mcp_path.exists():
                continue
            data = json.loads(mcp_path.read_text())
            servers = data.get("mcpServers", data)
            if isinstance(servers, dict):
                merged_mcp_servers.update(servers)

        # Read existing settings.json and merge
        settings_dir = ctx.repo_path / ".gemini"
        settings_path = settings_dir / "settings.json"

        existing_settings = {}
        if settings_path.exists():
            try:
                existing_settings = json.loads(settings_path.read_text())
            except json.JSONDecodeError:
                warnings.append("Could not parse existing .gemini/settings.json")

        # Merge hooks (existing take precedence for same event)
        if gemini_hooks:
            existing_hooks = existing_settings.get("hooks", {})
            for event_name, hook_list in gemini_hooks.items():
                if event_name not in existing_hooks:
                    existing_hooks[event_name] = hook_list
            existing_settings["hooks"] = existing_hooks

        # Merge MCP servers (existing take precedence)
        if merged_mcp_servers:
            existing_mcp = existing_settings.get("mcpServers", {})
            for name, config in merged_mcp_servers.items():
                if name not in existing_mcp:
                    existing_mcp[name] = config
            existing_settings["mcpServers"] = existing_mcp

        # Only write if we have something to add
        if not gemini_hooks and not merged_mcp_servers and not existing_settings:
            skipped.append(".gemini/settings.json (no hooks or MCP servers configured)")
            return written, skipped, warnings

        if dry_run:
            written.append(".gemini/settings.json (dry-run)")
        else:
            settings_dir.mkdir(parents=True, exist_ok=True)
            settings_path.write_text(json.dumps(existing_settings, indent=2) + "\n")
            written.append(".gemini/settings.json")

        return written, skipped, warnings

    @staticmethod
    def _parse_hook_yaml(path: Path) -> dict | None:
        """Parse a shipkit hook YAML definition."""
        import yaml
        try:
            data = yaml.safe_load(path.read_text())
            if isinstance(data, dict) and "name" in data and "event" in data:
                return data
        except Exception:
            pass
        return None

    def _compile_commands(self, ctx: CompileContext, dry_run: bool) -> tuple[list, list, list]:
        """Generate .gemini/commands/<skill>.toml for each skill."""
        written, skipped, warnings = [], [], []

        commands_dir = ctx.repo_path / ".gemini" / "commands"

        # Collect ALL layers of each skill
        skills_by_name: dict[str, list[Path]] = {}
        for skills_dir in ctx.skills_layers:
            if not skills_dir.exists():
                continue
            for skill_dir in sorted(skills_dir.iterdir()):
                if not skill_dir.is_dir():
                    continue
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    if skill_dir.name not in skills_by_name:
                        skills_by_name[skill_dir.name] = []
                    skills_by_name[skill_dir.name].append(skill_md)

        # Cascade and write each skill
        from shipkit.skill_parser import parse_skill, cascade_skills

        for skill_name, skill_paths in sorted(skills_by_name.items()):
            # Parse all layers
            skill_defs = [parse_skill(p) for p in skill_paths]

            # Cascade layers (respects extends field)
            cascaded_content = cascade_skills(skill_defs)

            # Use description from highest layer
            description = skill_defs[-1].description

            # Generate TOML command file
            # Gemini CLI uses TOML format for custom commands
            toml_content = f'''# {skill_name} skill
# Generated by shipkit - do not edit directly

[command]
name = "{skill_name}"
description = "{description}"

[command.prompt]
content = """
{cascaded_content}
"""
'''

            target = commands_dir / f"{skill_name}.toml"

            if dry_run:
                written.append(f".gemini/commands/{skill_name}.toml (dry-run)")
            else:
                commands_dir.mkdir(parents=True, exist_ok=True)
                target.write_text(toml_content)
                written.append(f".gemini/commands/{skill_name}.toml")

        return written, skipped, warnings

    @staticmethod
    def _extract_description(skill_content: str) -> str:
        """Extract first line description from SKILL.md."""
        first_line = skill_content.strip().split("\n")[0]
        return first_line.lstrip("#").strip()
