#!/usr/bin/env python3
"""Session memory hook for shipkit.

Runs after each session (SessionEnd / stop). Saves a session record to
<home>/.state/sessions/<session_id>.json with metadata (title, project, turn count,
timestamp). This provides cross-session memory — the context injection hook
reads these records on the next session start.

Input: JSON on stdin with session_id, transcript_path, cwd, hook_event_name.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from hooks.lib.config import resolve_home_path, is_hook_session, resolve_project_name
from hooks.lib.transcript import extract_turns, generate_title, build_summary, count_user_turns
from hooks.lib.logging_util import log_entry, debug_log


HOOK_NAME = "session-save"
MIN_TURNS = 4


def main():
    if is_hook_session():
        sys.exit(0)

    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    session_id = event.get("session_id", "")
    transcript_path_str = event.get("transcript_path", "")
    cwd = event.get("cwd", "")

    if not session_id or not transcript_path_str:
        sys.exit(0)

    transcript_path = Path(transcript_path_str).expanduser()

    vault_path = resolve_home_path()
    if vault_path is None:
        sys.exit(0)

    # Extract conversation
    turns = extract_turns(transcript_path)
    if len(turns) < MIN_TURNS:
        debug_log(HOOK_NAME, f"Skipping trivial session {session_id}")
        sys.exit(0)

    # Create sessions directory
    sessions_dir = vault_path / ".state" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    session_file = sessions_dir / f"{session_id}.json"

    # Update existing or create new
    if session_file.exists():
        try:
            existing = json.loads(session_file.read_text())
            # Update turn count and summary if session continued
            existing["turn_count"] = len(turns)
            existing["user_turn_count"] = count_user_turns(turns)
            existing["updated_at"] = datetime.now(timezone.utc).isoformat()
            session_file.write_text(json.dumps(existing, indent=2) + "\n")
            debug_log(HOOK_NAME, f"Updated session {session_id} ({len(turns)} turns)")
            sys.exit(0)
        except (json.JSONDecodeError, OSError):
            pass  # Overwrite corrupted file

    title = generate_title(turns)
    project = resolve_project_name(cwd)

    # Build a brief summary from user turns (what was discussed)
    user_messages = [t["content"] for t in turns if t["role"] in ("user", "human")]
    summary_parts = []
    for msg in user_messages[:5]:
        first_line = msg.strip().split("\n")[0]
        if len(first_line) > 100:
            first_line = first_line[:97] + "..."
        summary_parts.append(first_line)
    summary = "; ".join(summary_parts)
    if len(summary) > 300:
        summary = summary[:297] + "..."

    session_data = {
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": project,
        "cwd": cwd,
        "title": title,
        "summary": summary,
        "turn_count": len(turns),
        "user_turn_count": count_user_turns(turns),
    }

    session_file.write_text(json.dumps(session_data, indent=2) + "\n")
    log_entry(HOOK_NAME, f"Saved session {session_id}: {title}")

    print(json.dumps({"status": "ok", "message": f"Session recorded: {title}"}))


if __name__ == "__main__":
    main()
