#!/usr/bin/env python3
"""Session goals tracker hook for shipkit.

Runs at session start and end to help with focus and accountability.

session_start: Prompts "What are you working on today?"
session_end: Shows summary of goals vs accomplishments

Stores goals in ~/.config/shipkit/.state/sessions/<session-id>.json
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Hook lib is in the same package
sys.path.insert(0, str(Path(__file__).parent))

from lib.config import is_hook_session, resolve_home_path
from lib.llm_client import call_claude, is_llm_available


def handle_session_start(session_id: str, sessions_dir: Path) -> None:
    """Handle session start - prompt for goals."""

    # Check for previous unfinished session
    latest_session = find_latest_session(sessions_dir, exclude=session_id)

    output = ['INSTRUCTION: Session starting. Ask the user:\n\n"']

    if latest_session and not latest_session.get("completed"):
        output.append("🔄 Picking up where you left off?\n\n")
        output.append(f"Last session goal: {latest_session.get('goal', 'Unknown')}\n")
        if latest_session.get("status") == "in_progress":
            output.append("(You didn't mark it complete)\n\n")
        output.append("Continue with that, or starting something new?\n\n")

    output.append("What are you working on this session? (This helps me stay focused)\n\n")
    output.append("Example: 'Fix auth bug' or 'Add pagination to API' or 'just exploring'")
    output.append('"\n')

    print("".join(output), flush=True)


def handle_session_end(session_id: str, sessions_dir: Path) -> None:
    """Handle session end - summarize accomplishments vs goals."""

    # Load session data
    session_file = sessions_dir / f"{session_id}.json"
    if not session_file.exists():
        # No goals set, skip
        return

    session_data = json.loads(session_file.read_text())
    goal = session_data.get("goal", "")

    if not goal or goal.lower() in ("just exploring", "nothing specific", "n/a"):
        # No specific goal, skip summary
        return

    # Use LLM to analyze if goal was accomplished
    # (Would need transcript analysis - for now just prompt user)

    output = ['INSTRUCTION: Session ending. Tell the user:\n\n"']
    output.append("📊 Session summary:\n\n")
    output.append(f"Goal: {goal}\n\n")
    output.append("Did you accomplish this?\n")
    output.append("  • ✅ Yes - mark as done\n")
    output.append("  • 🔄 Partial - made progress\n")
    output.append("  • ❌ No - didn't get to it\n")
    output.append("  • 🌀 Changed direction - worked on something else\n\n")
    output.append("(Helps track focus and identify time sinks)")
    output.append('"\n')

    print("".join(output), flush=True)


def find_latest_session(sessions_dir: Path, exclude: str | None = None) -> dict | None:
    """Find the most recent session data."""
    if not sessions_dir.exists():
        return None

    sessions = []
    for session_file in sessions_dir.glob("*.json"):
        if exclude and session_file.stem == exclude:
            continue
        try:
            data = json.loads(session_file.read_text())
            sessions.append(data)
        except Exception:
            continue

    if not sessions:
        return None

    # Sort by timestamp, return latest
    sessions.sort(key=lambda s: s.get("start_time", ""), reverse=True)
    return sessions[0]


def save_session_goal(session_id: str, goal: str, sessions_dir: Path) -> None:
    """Save session goal to storage."""
    sessions_dir.mkdir(parents=True, exist_ok=True)

    session_file = sessions_dir / f"{session_id}.json"
    session_data = {
        "session_id": session_id,
        "goal": goal,
        "start_time": datetime.now().isoformat(),
        "status": "in_progress",
        "completed": False,
    }

    session_file.write_text(json.dumps(session_data, indent=2))


def main():
    """Main hook entry point."""
    # Skip if we're in a hook-spawned session
    if is_hook_session():
        sys.exit(0)

    # Disable in CI
    if os.environ.get("CI"):
        sys.exit(0)

    try:
        # Read event from stdin
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    event_type = event.get("event", "")
    session_id = event.get("sessionId", "unknown")

    home_path = resolve_home_path()
    if not home_path:
        sys.exit(0)

    sessions_dir = home_path / ".state" / "sessions"

    if event_type == "session_start":
        handle_session_start(session_id, sessions_dir)
    elif event_type == "session_end":
        handle_session_end(session_id, sessions_dir)

    sys.exit(0)


if __name__ == "__main__":
    main()
