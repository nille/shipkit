#!/usr/bin/env python3
"""Context injection hook for shipkit.

Runs at session start (SessionStart / spawn). Injects contextual information
into the agent's conversation:

1. Pending retro suggestions (high-severity → INSTRUCTION, others → soft nudge)
2. Learned user preferences from shipkit home
3. Recent session summaries for continuity

Output directives (Claude Code hook protocol):
- INSTRUCTION: — agent must act on this before first response
- CONTEXT: — background info, used when relevant
- Plain text — treated as CONTEXT

Input: JSON on stdin with session_id, cwd, hook_event_name.
Output: Text blocks with directive prefixes on stdout.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from hooks.lib.config import resolve_home_path, is_hook_session, resolve_project_name
from hooks.lib.session_context import (
    format_session_context,
    format_pending_retro_nudge,
    format_learned_preferences,
)
from hooks.lib.logging_util import debug_log


HOOK_NAME = "context-inject"


def main():
    if is_hook_session():
        sys.exit(0)

    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        event = {}

    cwd = event.get("cwd", "")
    project = resolve_project_name(cwd)

    home_path = resolve_home_path()
    if home_path is None:
        sys.exit(0)

    output_parts = []

    # 1. Pending retro suggestions
    retro_nudge = format_pending_retro_nudge()
    if retro_nudge:
        output_parts.append(f"INSTRUCTION: {retro_nudge}")

    # 2. Learned user preferences
    preferences = format_learned_preferences()
    if preferences:
        output_parts.append(f"CONTEXT: User preferences:\n{preferences}")

    # 3. Skill-rules index (learned rules per skill)
    skill_rules = _format_skill_rules_index(home_path)
    if skill_rules:
        output_parts.append(f"CONTEXT: {skill_rules}")

    # 4. Recent session summaries
    sessions = format_session_context(project_name=project)
    if sessions:
        output_parts.append(f"CONTEXT: {sessions}")

    if output_parts:
        print("\n\n".join(output_parts))
        debug_log(HOOK_NAME, f"Injected {len(output_parts)} context blocks")


def _format_skill_rules_index(home_path: Path) -> str:
    """List skills that have learned rules files."""
    skills_dir = home_path / "skills"
    if not skills_dir.exists():
        return ""

    lines = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        learned_file = skill_dir / "learned.md"
        if learned_file.exists():
            lines.append(f"  - /{skill_dir.name}: {learned_file}")

    if not lines:
        return ""

    return "Skills with learned rules (read before using these skills):\n" + "\n".join(lines)


if __name__ == "__main__":
    main()
