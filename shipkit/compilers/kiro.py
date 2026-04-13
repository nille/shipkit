"""Kiro compiler for shipkit.

Generates:
- \.kiro/steering/<name>.md (merged guidelines rules)
- .kiro/skills/<name>/SKILL.md (skills copied from content layers)
- .kiro/agents/<name>.json (subagent configs)

Content layering (lowest → highest precedence):
  package core → user global → project → repo-native
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import stat

import yaml

from shipkit.compilers.base import Compiler, CompileContext, CompileResult, PACKAGE_HOOKS_DIR, register_compiler


@register_compiler("kiro")
class KiroCompiler(Compiler):

    @property
    def name(self) -> str:
        return "Kiro"

    def compile(self, ctx: CompileContext, dry_run: bool = False) -> CompileResult:
        written = []
        skipped = []
        warnings = []

        # Skills are discovered at runtime via skill-discovery.md guideline
        # Only compile: guidelines (with discovery instructions), subagents, MCP, hooks
        for step in [self._compile_guidelines, self._compile_subagents, self._compile_mcp, self._compile_hooks]:
            w, s, warn = step(ctx, dry_run)
            written.extend(w)
            skipped.extend(s)
            warnings.extend(warn)

        return CompileResult(files_written=written, files_skipped=skipped, warnings=warnings)

    def _compile_guidelines(self, ctx: CompileContext, dry_run: bool) -> tuple[list, list, list]:
        written, skipped, warnings = [], [], []

        # Kiro uses "steering" not "guidelines" (their native terminology)
        steering_dir = ctx.repo_path / ".kiro" / "steering"

        # Generate tool-specific discovery instructions
        from shipkit.compilers.discovery_template import generate_discovery_instructions
        discovery_instructions = generate_discovery_instructions(
            tool_name="Kiro",
            tool_project_path=".kiro/skills",
            tool_user_path="~/.kiro/skills"
        )

        # Write discovery as a guideline file
        if not dry_run:
            steering_dir.mkdir(parents=True, exist_ok=True)
            discovery_file = steering_dir / "skill-discovery.md"
            discovery_file.write_text(f"<!-- shipkit:managed -->\n{discovery_instructions}")
            written.append("\.kiro/steering/skill-discovery.md")

        # Collect ALL layers of each guidelines rule by filename
        from shipkit.skill_parser import parse_guidelines, cascade_guidelines

        guidelines_by_name: dict[str, list[Path]] = {}
        for layer_dir in ctx.guidelines_layers:
            if not layer_dir.exists():
                continue
            for md_file in sorted(layer_dir.glob("*.md")):
                # Skip skill-discovery.md (we generate it dynamically)
                if md_file.name == "skill-discovery.md":
                    continue
                if md_file.name not in guidelines_by_name:
                    guidelines_by_name[md_file.name] = []
                guidelines_by_name[md_file.name].append(md_file)

        if not guidelines_by_name:
            skipped.append("\.kiro/steering/ (no guidelines rules found)")
            return written, skipped, warnings

        # Cascade and write each guidelines rule
        for filename, guidelines_paths in sorted(guidelines_by_name.items()):
            target = steering_dir / filename

            # Preserve repo-native guidelines files
            if target.exists() and not self._is_managed(target):
                skipped.append(f"\.kiro/steering/{filename} (repo-native, preserved)")
                continue

            # Parse all layers
            guidelines_defs = [parse_guidelines(p) for p in guidelines_paths]

            # Cascade layers (respects extends field)
            cascaded_content = cascade_guidelines(guidelines_defs)

            if dry_run:
                written.append(f"\.kiro/steering/{filename} (dry-run)")
            else:
                steering_dir.mkdir(parents=True, exist_ok=True)
                # Add a managed marker comment at the top
                managed_content = f"<!-- shipkit:managed -->\n{cascaded_content}"
                target.write_text(managed_content)
                written.append(f"\.kiro/steering/{filename}")

        return written, skipped, warnings

    def _compile_skills(self, ctx: CompileContext, dry_run: bool) -> tuple[list, list, list]:
        written, skipped, warnings = [], [], []

        skills_dir = ctx.repo_path / ".kiro" / "skills"

        # Collect ALL layers of each skill
        skills_by_name: dict[str, list[Path]] = {}
        for layer_dir in ctx.skills_layers:
            if not layer_dir.exists():
                continue
            for skill_dir in sorted(layer_dir.iterdir()):
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
            target_dir = skills_dir / skill_name

            # Parse all layers
            skill_defs = [parse_skill(p) for p in skill_paths]

            # Cascade layers (respects extends field)
            cascaded_content = cascade_skills(skill_defs)

            if dry_run:
                written.append(f".kiro/skills/{skill_name}/SKILL.md (dry-run)")
            else:
                target_dir.mkdir(parents=True, exist_ok=True)
                (target_dir / "SKILL.md").write_text(cascaded_content)

                # Merge references from all layers
                for skill_path in skill_paths:
                    refs_dir = skill_path.parent / "references"
                    if refs_dir.exists():
                        target_refs = target_dir / "references"
                        target_refs.mkdir(exist_ok=True)
                        for ref_file in refs_dir.rglob("*"):
                            if ref_file.is_file():
                                rel_path = ref_file.relative_to(refs_dir)
                                target_ref = target_refs / rel_path
                                target_ref.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(ref_file, target_ref)

                written.append(f".kiro/skills/{skill_name}/SKILL.md")

        return written, skipped, warnings

    # Map shipkit tool names to Kiro agent tool names
    TOOL_NAME_MAP = {
        "file_read": "fs_read",
        "file_write": "fs_write",
        "glob": "glob",
        "grep": "grep",
        "bash": "execute_bash",
    }

    # Map model shorthand to Kiro model identifiers
    MODEL_MAP = {
        "sonnet": "claude-sonnet-4.6-1m",
        "haiku": "claude-haiku-4.5",
        "opus": "claude-opus-4-6",
    }

    def _compile_subagents(self, ctx: CompileContext, dry_run: bool) -> tuple[list, list, list]:
        """Compile subagent YAML definitions into .kiro/agents/*.json."""
        written, skipped, warnings = [], [], []

        agents: dict[str, dict] = {}
        for layer_dir in ctx.subagents_layers:
            if not layer_dir.exists():
                continue
            for yaml_file in sorted(layer_dir.glob("*.yaml")):
                try:
                    data = yaml.safe_load(yaml_file.read_text())
                    if isinstance(data, dict) and "name" in data:
                        agents[data["name"]] = data
                except (yaml.YAMLError, OSError):
                    warnings.append(f"Failed to parse subagent: {yaml_file}")

        if not agents:
            return written, skipped, warnings

        agents_dir = ctx.repo_path / ".kiro" / "agents"

        for agent_def in agents.values():
            name = agent_def["name"]
            target = agents_dir / f"{name}.json"

            # Don't overwrite repo-native agents
            if target.exists() and not self._is_managed_json(target):
                skipped.append(f".kiro/agents/{name}.json (repo-native, preserved)")
                continue

            # Convert to Kiro agent JSON format
            tools = [self.TOOL_NAME_MAP.get(t, t) for t in agent_def.get("tools", [])]
            model = self.MODEL_MAP.get(agent_def.get("model", "sonnet"), agent_def.get("model", ""))

            # Resolve prompt path placeholders
            prompt = agent_def.get("prompt", "")
            prompt = prompt.replace("{skills}", ".kiro/skills")
            prompt = prompt.replace("{guidelines}", "\.kiro/steering")
            prompt = prompt.replace("{state}", str(ctx.home_path / ".state"))

            kiro_agent = {
                "_shipkit_managed": True,
                "name": name,
                "description": agent_def.get("description", "").strip(),
                "prompt": prompt.strip(),
                "tools": tools,
                "allowedTools": tools,
                "model": model,
            }

            # Resolve resource paths
            resources = agent_def.get("resources", [])
            if resources:
                resolved = []
                for res in resources:
                    res = res.replace("{guidelines}", "\.kiro/steering")
                    res = res.replace("{skills}", ".kiro/skills")
                    if res.endswith(".md"):
                        resolved.append(f"file://{res}")
                    else:
                        resolved.append(f"file://{res}")
                kiro_agent["resources"] = resolved

            if dry_run:
                written.append(f".kiro/agents/{name}.json (dry-run)")
            else:
                agents_dir.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(kiro_agent, indent=2) + "\n")
                written.append(f".kiro/agents/{name}.json")

        return written, skipped, warnings

    @staticmethod
    def _is_managed_json(path: Path) -> bool:
        """Check if a JSON file was generated by shipkit."""
        try:
            data = json.loads(path.read_text())
            return isinstance(data, dict) and data.get("_shipkit_managed") is True
        except (OSError, json.JSONDecodeError):
            return False

    def _compile_mcp(self, ctx: CompileContext, dry_run: bool) -> tuple[list, list, list]:
        """Compile MCP config into .kiro/config/mcp.json.

        Kiro uses a config directory for MCP servers rather than a top-level .mcp.json.
        """
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
            skipped.append(".kiro/config/mcp.json (no MCP servers configured)")
            return written, skipped, warnings

        # Repo-native entries take precedence
        config_dir = ctx.repo_path / ".kiro" / "config"
        mcp_path = config_dir / "mcp.json"
        existing_servers = {}
        if mcp_path.exists():
            existing = json.loads(mcp_path.read_text())
            existing_servers = existing.get("mcpServers", {})

        for name, config in merged_servers.items():
            if name not in existing_servers:
                existing_servers[name] = config

        output = {"mcpServers": existing_servers}

        if dry_run:
            written.append(".kiro/config/mcp.json (dry-run)")
        else:
            config_dir.mkdir(parents=True, exist_ok=True)
            mcp_path.write_text(json.dumps(output, indent=2) + "\n")
            written.append(".kiro/config/mcp.json")

        return written, skipped, warnings

    # Map shipkit hook events to Kiro lifecycle prefixes
    HOOK_EVENT_MAP = {
        "session_start": "spawn",
        "session_end": "stop",
        "user_prompt_submit": "prompt",
    }

    def _compile_hooks(self, ctx: CompileContext, dry_run: bool) -> tuple[list, list, list]:
        """Compile hooks into .kiro/hooks/ as shell wrapper scripts."""
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

        hooks_dir = ctx.repo_path / ".kiro" / "hooks"

        for hook_def in hooks_by_name.values():
            event = hook_def.get("event", "")
            lifecycle = self.HOOK_EVENT_MAP.get(event)
            if not lifecycle:
                warnings.append(f"Unknown hook event '{event}' in {hook_def['name']}, skipped for Kiro")
                continue

            # Resolve command
            command = hook_def.get("command", "")
            command = command.replace("{shipkit_hooks_dir}", str(PACKAGE_HOOKS_DIR))

            # Generate a shell wrapper script
            script_name = f"{lifecycle}-{hook_def['name']}.sh"
            target = hooks_dir / script_name

            # Don't overwrite repo-native hooks
            if target.exists() and not self._is_managed(target):
                skipped.append(f".kiro/hooks/{script_name} (repo-native, preserved)")
                continue

            script_content = f"""#!/bin/bash
# shipkit:managed — generated by shipkit sync
# Hook: {hook_def['name']}
# Event: {event} → Kiro lifecycle: {lifecycle}
{command} "$@"
"""

            if dry_run:
                written.append(f".kiro/hooks/{script_name} (dry-run)")
            else:
                hooks_dir.mkdir(parents=True, exist_ok=True)
                target.write_text(script_content)
                target.chmod(target.stat().st_mode | stat.S_IEXEC)
                written.append(f".kiro/hooks/{script_name}")

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
    def _is_managed(path: Path) -> bool:
        """Check if a file was generated by shipkit (has managed marker)."""
        try:
            first_line = path.read_text().split("\n", 1)[0]
            return "shipkit:managed" in first_line
        except (OSError, UnicodeDecodeError):
            return False
