"""OpenCode compiler for shipkit.

Generates:
- .opencode/plugins/shipkit-hooks.ts (TypeScript plugin wrapping Python hooks)
- opencode.json (plugin registration + MCP servers)
- .opencode/plugins/shipkit-tools.ts (custom tools from skills)

Content layering (lowest → highest precedence):
  package core → user global → project → repo-native

Based on OpenCode docs: https://opencode.ai/docs/plugins/
Event system: session.created, session.idle, tool.execute.before, tool.execute.after
"""

from __future__ import annotations

import json
from pathlib import Path

from shipkit.compilers.base import Compiler, CompileContext, CompileResult, PACKAGE_HOOKS_DIR, register_compiler

import yaml


@register_compiler("opencode")
class OpenCodeCompiler(Compiler):

    @property
    def name(self) -> str:
        return "OpenCode"

    def compile(self, ctx: CompileContext, dry_run: bool = False) -> CompileResult:
        written = []
        skipped = []
        warnings = []

        # Skills are discovered at runtime via AGENTS.md
        # Compile: AGENTS.md (with discovery + guidelines), hooks plugin, opencode.json
        for step in [self._compile_agents_md, self._compile_hooks_plugin, self._compile_opencode_json]:
            w, s, warn = step(ctx, dry_run)
            written.extend(w)
            skipped.extend(s)
            warnings.extend(warn)

        return CompileResult(files_written=written, files_skipped=skipped, warnings=warnings)

    def _compile_agents_md(self, ctx: CompileContext, dry_run: bool) -> tuple[list, list, list]:
        """Generate AGENTS.md with discovery instructions only."""
        written, skipped, warnings = [], [], []

        # Generate tool-specific discovery instructions for both skills AND guidelines
        from shipkit.compilers.discovery_template import generate_discovery_instructions
        from shipkit.compilers.guideline_discovery_template import generate_guideline_discovery_instructions

        skill_discovery = generate_discovery_instructions(
            tool_name="OpenCode",
            tool_project_path=".opencode/skills",
            tool_user_path="~/.opencode/skills"
        )

        guideline_discovery = generate_guideline_discovery_instructions(
            tool_name="OpenCode",
            tool_project_path=".opencode/guidelines",
            tool_user_path="~/.opencode/guidelines"
        )

        # AGENTS.md contains ONLY discovery instructions (minimal bootstrap)
        # Agent will discover and read guidelines at runtime
        managed_content = f"{skill_discovery}\n\n---\n\n{guideline_discovery}"

        # Write to AGENTS.md (OpenCode's equivalent of CLAUDE.md)
        agents_md_path = ctx.repo_path / "AGENTS.md"

        # Preserve user content below sentinel (like Claude compiler)
        SENTINEL_BEGIN = "<!-- SHIPKIT:BEGIN — managed by shipkit, do not edit above SHIPKIT:END -->"
        SENTINEL_END = "<!-- SHIPKIT:END -->"

        user_content = ""
        if agents_md_path.exists():
            existing = agents_md_path.read_text()
            if SENTINEL_END in existing:
                _, _, user_content = existing.partition(SENTINEL_END)
                user_content = user_content.strip()
            elif SENTINEL_BEGIN not in existing:
                user_content = existing.strip()
                warnings.append("Existing AGENTS.md was not shipkit-managed; preserved as user content below sentinel.")

        full_content = f"{SENTINEL_BEGIN}\n\n{managed_content}\n\n{SENTINEL_END}\n"
        if user_content:
            full_content += f"\n{user_content}\n"

        if dry_run:
            written.append("AGENTS.md (dry-run)")
        else:
            agents_md_path.write_text(full_content)
            written.append("AGENTS.md")

        return written, skipped, warnings

    # Map shipkit hook events to OpenCode events
    HOOK_EVENT_MAP = {
        "session_start": "session.created",
        "session_end": "session.idle",
        "user_prompt_submit": "session.updated",  # Closest match
        "stop": "session.idle",
        "pre_tool_use": "tool.execute.before",
        "post_tool_use": "tool.execute.after",
    }

    def _compile_hooks_plugin(self, ctx: CompileContext, dry_run: bool) -> tuple[list, list, list]:
        """Generate .opencode/plugins/shipkit-hooks.ts that wraps Python hooks."""
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

        if not hooks_by_name:
            skipped.append(".opencode/plugins/shipkit-hooks.ts (no hooks configured)")
            return written, skipped, warnings

        # Build TypeScript plugin that wraps Python hooks
        ts_lines = [
            "// Generated by shipkit - wraps Python hooks for OpenCode",
            "// Do not edit directly - regenerate with: shipkit sync",
            "",
            "export const ShipkitHooksPlugin = async (ctx: any) => {",
            "  const { $ } = ctx;",
            "  ",
            "  return {",
        ]

        hook_handlers = []
        for hook_def in hooks_by_name.values():
            event = hook_def.get("event", "")
            opencode_event = self.HOOK_EVENT_MAP.get(event)
            if not opencode_event:
                warnings.append(f"Unknown hook event '{event}' in {hook_def['name']}, skipped")
                continue

            # Resolve the command path
            command = hook_def.get("command", "")
            command = command.replace("{shipkit_hooks_dir}", str(PACKAGE_HOOKS_DIR))
            timeout = hook_def.get("timeout", 120)

            # Generate TypeScript event handler
            handler = f'''    "{opencode_event}": async (input: any, output: any) => {{
      try {{
        const result = await $.exec('{command}', {{
          timeout: {timeout * 1000}, // ms
          stdin: JSON.stringify(input),
        }});
        if (result.exitCode !== 0) {{
          console.error(`Hook {hook_def['name']} failed:`, result.stderr);
        }}
      }} catch (error) {{
        console.error(`Hook {hook_def['name']} error:`, error);
      }}
    }},'''

            hook_handlers.append(handler)

        ts_lines.extend(hook_handlers)
        ts_lines.append("  };")
        ts_lines.append("};")
        ts_lines.append("")

        ts_content = "\n".join(ts_lines)

        plugins_dir = ctx.repo_path / ".opencode" / "plugins"
        target = plugins_dir / "shipkit-hooks.ts"

        if dry_run:
            written.append(".opencode/plugins/shipkit-hooks.ts (dry-run)")
        else:
            plugins_dir.mkdir(parents=True, exist_ok=True)
            target.write_text(ts_content)
            written.append(".opencode/plugins/shipkit-hooks.ts")

        return written, skipped, warnings

    def _compile_tools_plugin(self, ctx: CompileContext, dry_run: bool) -> tuple[list, list, list]:
        """Generate .opencode/plugins/shipkit-tools.ts with custom tools from skills."""
        written, skipped, warnings = [], [], []

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

        if not skills_by_name:
            skipped.append(".opencode/plugins/shipkit-tools.ts (no skills configured)")
            return written, skipped, warnings

        # Build TypeScript plugin with custom tools
        ts_lines = [
            "// Generated by shipkit - custom tools from skills",
            "// Do not edit directly - regenerate with: shipkit sync",
            "",
            "import { tool } from '@opencode-ai/plugin';",
            "",
            "export const ShipkitToolsPlugin = async (ctx: any) => {",
            "  return {",
            "    tool: {",
        ]

        # Cascade and write each skill
        from shipkit.skill_parser import parse_skill, cascade_skills

        tool_defs = []
        for skill_name, skill_paths in sorted(skills_by_name.items()):
            # Parse all layers
            skill_defs = [parse_skill(p) for p in skill_paths]

            # Cascade layers (respects extends field)
            cascaded_content = cascade_skills(skill_defs)

            # Use description from highest layer
            description = skill_defs[-1].description

            # Escape skill content for TypeScript string literal
            escaped_content = cascaded_content.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')

            # Generate tool definition with embedded skill content
            tool_def = f'''      {skill_name}: tool({{
        description: "{description}",
        args: {{}}, // Skills don't have typed args by default
        async execute(args: any, context: any) {{
          // Skill instructions embedded by shipkit
          const skillContent = `{escaped_content}`;

          // Return skill content so the agent can read it
          return skillContent;
        }}
      }}),'''

            tool_defs.append(tool_def)

        ts_lines.extend(tool_defs)
        ts_lines.append("    },")
        ts_lines.append("  };")
        ts_lines.append("};")
        ts_lines.append("")

        ts_content = "\n".join(ts_lines)

        plugins_dir = ctx.repo_path / ".opencode" / "plugins"
        target = plugins_dir / "shipkit-tools.ts"

        if dry_run:
            written.append(".opencode/plugins/shipkit-tools.ts (dry-run)")
        else:
            plugins_dir.mkdir(parents=True, exist_ok=True)
            target.write_text(ts_content)
            written.append(".opencode/plugins/shipkit-tools.ts")

        return written, skipped, warnings

    def _compile_opencode_json(self, ctx: CompileContext, dry_run: bool) -> tuple[list, list, list]:
        """Generate opencode.json with plugin registration and MCP servers."""
        written, skipped, warnings = [], [], []

        # Merge MCP configs from all layers
        merged_mcp_servers = {}
        for mcp_path in ctx.mcp_layers:
            if not mcp_path.exists():
                continue
            data = json.loads(mcp_path.read_text())
            servers = data.get("mcpServers", data)
            if isinstance(servers, dict):
                merged_mcp_servers.update(servers)

        # Read existing opencode.json
        opencode_json_path = ctx.repo_path / "opencode.json"
        config = {"$schema": "https://opencode.ai/config.json"}

        if opencode_json_path.exists():
            try:
                config = json.loads(opencode_json_path.read_text())
            except json.JSONDecodeError:
                warnings.append("Could not parse existing opencode.json")

        # Add shipkit plugins to plugin list
        plugins = config.get("plugin", [])
        if isinstance(plugins, list):
            # Add our plugins if not already present
            for plugin in ["./plugins/shipkit-hooks.ts", "./plugins/shipkit-tools.ts"]:
                if plugin not in plugins:
                    plugins.append(plugin)
            config["plugin"] = plugins

        # Merge MCP servers (existing take precedence)
        if merged_mcp_servers:
            existing_mcp = config.get("mcpServers", {})
            for name, server_config in merged_mcp_servers.items():
                if name not in existing_mcp:
                    existing_mcp[name] = server_config
            config["mcpServers"] = existing_mcp

        if dry_run:
            written.append("opencode.json (dry-run)")
        else:
            opencode_json_path.write_text(json.dumps(config, indent=2) + "\n")
            written.append("opencode.json")

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

    @staticmethod
    def _extract_description(skill_content: str) -> str:
        """Extract first line description from SKILL.md."""
        first_line = skill_content.strip().split("\n")[0]
        return first_line.lstrip("#").strip().replace('"', '\\"')
