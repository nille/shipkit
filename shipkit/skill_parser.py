"""Skill and steering parsing utilities for Agent Skills standard compliance.

Implements the Agent Skills open standard: https://agentskills.io/specification

Supports:
- Frontmatter parsing (name, description, license, compatibility, metadata, allowed-tools)
- Skill cascading/composition via 'extends' field
- Steering rule cascading with same mechanism
- Layer merging with precedence rules
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class SkillDefinition:
    """Parsed skill definition following Agent Skills standard."""

    name: str
    description: str
    body: str
    license: str = ""
    compatibility: str = ""
    metadata: dict = None
    allowed_tools: str = ""
    extends: bool = True  # Shipkit extension: cascade with lower layers
    source_path: Path | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


def parse_skill(skill_md_path: Path) -> SkillDefinition:
    """Parse a SKILL.md file following Agent Skills standard.

    Returns a SkillDefinition with frontmatter fields and body content.
    """
    content = skill_md_path.read_text()

    # Extract frontmatter
    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)

    if not frontmatter_match:
        # No frontmatter - treat entire file as body with extracted name
        # Fallback to first line as description
        lines = content.strip().split('\n')
        first_line = lines[0] if lines else ""
        description = first_line.lstrip('#').strip()

        return SkillDefinition(
            name=skill_md_path.parent.name,
            description=description or "No description",
            body=content,
            source_path=skill_md_path,
        )

    frontmatter_text, body = frontmatter_match.groups()
    frontmatter = yaml.safe_load(frontmatter_text) or {}

    # Extract standard fields
    name = frontmatter.get('name', skill_md_path.parent.name)
    description = frontmatter.get('description', '')
    license_field = frontmatter.get('license', '')
    compatibility = frontmatter.get('compatibility', '')
    metadata = frontmatter.get('metadata', {})
    allowed_tools = frontmatter.get('allowed-tools', '')

    # Shipkit extension: check for 'extends' in frontmatter or metadata
    extends = frontmatter.get('extends', metadata.get('extends', True))
    if isinstance(extends, str):
        extends = extends.lower() in ('true', 'yes', '1')

    return SkillDefinition(
        name=name,
        description=description,
        body=body.strip(),
        license=license_field,
        compatibility=compatibility,
        metadata=metadata,
        allowed_tools=allowed_tools,
        extends=extends,
        source_path=skill_md_path,
    )


def cascade_skills(skill_definitions: list[SkillDefinition]) -> str:
    """Cascade multiple skill definitions from lowest to highest precedence.

    If a higher layer has extends=false, only that layer is returned.
    Otherwise, all layers with extends=true are concatenated.

    Args:
        skill_definitions: List in precedence order (lowest first)

    Returns:
        Merged skill content with layer markers
    """
    if not skill_definitions:
        return ""

    # Check if highest layer has extends=false
    if not skill_definitions[-1].extends:
        # Complete override - only use highest layer
        return skill_definitions[-1].body

    # Cascade: include all layers that have extends=true
    parts = []
    for i, skill_def in enumerate(skill_definitions):
        if not skill_def.extends and i < len(skill_definitions) - 1:
            # This layer wants to reset, skip all lower layers
            parts.clear()

        if skill_def.source_path:
            layer_name = _layer_name(skill_def.source_path)
            parts.append(f"<!-- Layer: {layer_name} -->")

        parts.append(skill_def.body)

        if i < len(skill_definitions) - 1:
            parts.append("\n---\n")

    return "\n\n".join(parts)


def _layer_name(path: Path) -> str:
    """Extract human-readable layer name from path."""
    path_str = str(path)
    if '/content/skills/' in path_str:
        return "package core"
    elif '/.config/shipkit/skills/' in path_str:
        return "user global"
    elif '/plugins/' in path_str:
        plugin_name = path_str.split('/plugins/')[1].split('/')[0]
        return f"plugin:{plugin_name}"
    elif '/projects/' in path_str:
        project_name = path_str.split('/projects/')[1].split('/')[0]
        return f"project:{project_name}"
    else:
        return "unknown"


@dataclass
class SteeringDefinition:
    """Parsed steering rule definition."""

    filename: str
    body: str
    extends: bool = True  # Cascade with lower layers by default
    source_path: Path | None = None


def parse_steering(steering_md_path: Path) -> SteeringDefinition:
    """Parse a steering .md file with optional frontmatter.

    Steering rules follow the same format as skills but are simpler:
    - Optional frontmatter with 'extends' field
    - Body content (markdown)
    
    If no frontmatter, defaults to extends: true (additive).
    """
    content = steering_md_path.read_text()
    filename = steering_md_path.name

    # Extract frontmatter if present
    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)

    if not frontmatter_match:
        # No frontmatter - entire file is body, defaults to extends: true
        return SteeringDefinition(
            filename=filename,
            body=content.strip(),
            extends=True,
            source_path=steering_md_path,
        )

    frontmatter_text, body = frontmatter_match.groups()
    frontmatter = yaml.safe_load(frontmatter_text) or {}

    # Check for 'extends' field
    extends = frontmatter.get('extends', True)
    if isinstance(extends, str):
        extends = extends.lower() in ('true', 'yes', '1')

    return SteeringDefinition(
        filename=filename,
        body=body.strip(),
        extends=extends,
        source_path=steering_md_path,
    )


def cascade_steering(steering_definitions: list[SteeringDefinition]) -> str:
    """Cascade multiple steering definitions from lowest to highest precedence.

    If a higher layer has extends=false, only that layer is returned.
    Otherwise, all layers with extends=true are concatenated.

    Args:
        steering_definitions: List in precedence order (lowest first)

    Returns:
        Merged steering content with layer markers
    """
    if not steering_definitions:
        return ""

    # Check if highest layer has extends=false
    if not steering_definitions[-1].extends:
        # Complete override - only use highest layer
        return steering_definitions[-1].body

    # Cascade: include all layers that have extends=true
    parts = []
    for i, steering_def in enumerate(steering_definitions):
        if not steering_def.extends and i < len(steering_definitions) - 1:
            # This layer wants to reset, skip all lower layers
            parts.clear()

        if steering_def.source_path:
            layer_name = _layer_name(steering_def.source_path)
            parts.append(f"<!-- Layer: {layer_name} -->")

        parts.append(steering_def.body)

        if i < len(steering_definitions) - 1:
            parts.append("\n---\n")

    return "\n\n".join(parts)
