#!/usr/bin/env python3
"""Retro-analyzer hook for shipkit.

Runs after each session (SessionEnd / stop). Extracts the conversation,
analyzes it for patterns, and writes suggestions to <home>/.state/retro/pending/.

Uses debounced execution — rapid repeated invocations (e.g., multiple
assistant responses) coalesce into a single analysis after a quiet period.

Input: JSON on stdin with session_id, transcript_path, cwd, hook_event_name.
Output: JSON suggestion file in .state/retro/pending/ directory.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add the hooks directory to path for library imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hooks.lib.config import resolve_home_path, is_hook_session, resolve_project_name
from hooks.lib.transcript import extract_turns, build_summary, generate_title, count_user_turns
from hooks.lib.logging_util import log_entry, debug_log


HOOK_NAME = "retro-analyze"
MIN_TURNS = 4  # Minimum total turns (2 exchanges)


def main():
    # Don't run inside hook-spawned subagents
    if is_hook_session():
        sys.exit(0)

    # Read event JSON from stdin
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

    # Resolve shipkit home
    vault_path = resolve_home_path()
    if vault_path is None:
        debug_log(HOOK_NAME, "Shipkit not initialized, skipping")
        sys.exit(0)

    # Extract conversation
    turns = extract_turns(transcript_path)
    user_turns = count_user_turns(turns)

    # Skip trivial conversations
    if len(turns) < MIN_TURNS or user_turns < 2:
        debug_log(HOOK_NAME, f"Skipping trivial session {session_id} ({len(turns)} turns, {user_turns} user)")
        sys.exit(0)

    # Ensure retro directories exist
    pending_dir = vault_path / ".state" / "retro" / "pending"
    pending_dir.mkdir(parents=True, exist_ok=True)

    # Check if we already analyzed this session
    pending_file = pending_dir / f"{session_id}.json"
    if pending_file.exists():
        debug_log(HOOK_NAME, f"Already analyzed session {session_id}")
        sys.exit(0)

    # Build the transcript summary
    summary = build_summary(turns)
    title = generate_title(turns)
    project = resolve_project_name(cwd)

    # Write the pending session for interactive review
    # Analysis happens in-conversation (visible to user), not in background
    pending_data = {
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cwd": cwd,
        "project": project,
        "title": title,
        "turn_count": len(turns),
        "user_turn_count": user_turns,
        "status": "pending_review",
        "transcript_summary": summary,
        "transcript_path": str(transcript_path),
    }

    pending_file.write_text(json.dumps(pending_data, indent=2) + "\n")
    log_entry(HOOK_NAME, f"Saved session {session_id} for interactive review ({len(turns)} turns): {title}")

    # Output for hook system
    print(json.dumps({
        "status": "ok",
        "message": f"Session saved for retro analysis ({len(turns)} turns)",
    }))


if __name__ == "__main__":
    main()
