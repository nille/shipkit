"""Session context formatting for spawn/start hooks.

Reads recent session records from shipkit home and formats them
for injection into the agent's context at session start.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .config import resolve_home_path


def find_sessions(
    project_name: str | None = None,
    max_count: int = 20,
) -> list[dict]:
    """Find recent session records from the vault, newest first.

    Returns list of dicts with: session_id, timestamp, title, summary,
    project, turn_count, path.
    """
    vault = resolve_home_path()
    if vault is None:
        return []

    sessions_dir = vault / ".state" / "sessions"
    if not sessions_dir.exists():
        return []

    results = []
    # Collect all session JSON files
    session_files = sorted(sessions_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

    for sf in session_files[:max_count]:
        try:
            data = json.loads(sf.read_text())
            if project_name and data.get("project") != project_name:
                continue
            data["path"] = str(sf)
            results.append(data)
        except (json.JSONDecodeError, OSError):
            continue

    return results


def format_session_context(
    project_name: str | None = None,
    max_summaries: int = 3,
    max_older: int = 7,
    max_chars: int = 2000,
) -> str:
    """Format recent sessions as context for injection.

    Returns a text block with recent session summaries and older session titles.
    """
    sessions = find_sessions(project_name=project_name, max_count=max_summaries + max_older)

    if not sessions:
        return ""

    parts = []
    total_chars = 0

    # Recent sessions with full summaries
    for i, session in enumerate(sessions[:max_summaries]):
        title = session.get("title", "Untitled")
        summary = session.get("summary", "")
        timestamp = session.get("timestamp", "")
        date_str = timestamp[:10] if timestamp else "?"

        entry = f"- [{date_str}] {title}"
        if summary:
            entry += f"\n  {summary}"

        if total_chars + len(entry) > max_chars:
            break
        parts.append(entry)
        total_chars += len(entry)

    # Older sessions with just titles
    older = sessions[max_summaries:max_summaries + max_older]
    if older:
        older_lines = []
        for session in older:
            title = session.get("title", "Untitled")
            timestamp = session.get("timestamp", "")
            date_str = timestamp[:10] if timestamp else "?"
            line = f"  - [{date_str}] {title}"
            if total_chars + len(line) > max_chars:
                break
            older_lines.append(line)
            total_chars += len(line)
        if older_lines:
            parts.append("Older sessions:")
            parts.extend(older_lines)

    if not parts:
        return ""

    return "Recent sessions:\n" + "\n".join(parts)


def format_pending_retro_nudge(max_items: int = 3) -> str:
    """Format high-severity pending retro items as an instruction nudge.

    Returns empty string if no high-severity items pending.
    """
    vault = resolve_home_path()
    if vault is None:
        return ""

    pending_dir = vault / ".state" / "retro" / "pending"
    if not pending_dir.exists():
        return ""

    high_items = []
    for pf in sorted(pending_dir.glob("*.json")):
        try:
            data = json.loads(pf.read_text())
            suggestions = data.get("suggestions", [])
            for s in suggestions:
                if s.get("severity") == "high":
                    high_items.append(s.get("title", "Untitled"))
        except (json.JSONDecodeError, OSError):
            continue

    if not high_items:
        # Check count of any pending items for a softer nudge
        pending_count = len(list(pending_dir.glob("*.json")))
        if pending_count > 0:
            return f"You have {pending_count} pending retro items. Run /retro to review them when you have a moment."
        return ""

    items_text = "\n".join(f"  - {item}" for item in high_items[:max_items])
    return (
        f"There are {len(high_items)} high-severity retro items from previous sessions:\n"
        f"{items_text}\n"
        f"Consider running /retro to address these."
    )


def format_learned_preferences() -> str:
    """Format learned user preferences for context injection."""
    vault = resolve_home_path()
    if vault is None:
        return ""

    prefs_file = vault / "guidelines" / "auto-learned.md"
    if not prefs_file.exists():
        return ""

    content = prefs_file.read_text().strip()
    if not content:
        return ""

    # Strip frontmatter if present
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2].strip()

    return content
