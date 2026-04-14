#!/usr/bin/env python3
"""Pattern learner hook for shipkit.

Runs at session end (SessionEnd event). Analyzes the session transcript to detect:
- Repeated command sequences
- Common file edit patterns
- Error → fix workflows
- Workflows that appear across multiple sessions

Uses LLM to determine if patterns are worth automating into skills.
Suggests skill creation when threshold met (3+ occurrences).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

# Hook lib is in the same package
sys.path.insert(0, str(Path(__file__).parent))

from lib.config import is_hook_session, resolve_home_path
from lib.transcript import parse_transcript
from lib.llm_client import call_claude, is_llm_available


@dataclass
class Pattern:
    """A detected workflow pattern."""
    pattern_id: str  # Hash of the pattern
    pattern_type: str  # "command_sequence", "file_edit", "error_fix"
    description: str  # Human-readable description
    occurrences: int  # How many times seen
    first_seen: str  # ISO timestamp
    last_seen: str  # ISO timestamp
    sessions: list[str]  # Session IDs where this pattern appeared
    automatable: bool | None  # LLM assessment: worth automating?
    suggested_skill_name: str | None  # Suggested skill name
    confidence: float  # How confident we are this is a real pattern (0-1)

    # Pattern details (type-specific)
    commands: list[str] | None = None  # For command_sequence
    files: list[str] | None = None  # For file_edit
    error_pattern: str | None = None  # For error_fix
    fix_description: str | None = None  # For error_fix


def extract_command_sequences(transcript: dict) -> list[dict]:
    """Extract sequences of bash commands from transcript.

    Returns: List of command sequences (3+ consecutive commands)
    """
    sequences = []
    current_sequence = []

    for turn in transcript.get("turns", []):
        for content in turn.get("assistant_content", []):
            if content.get("type") == "tool_use" and content.get("tool") == "Bash":
                command = content.get("parameters", {}).get("command", "")
                if command:
                    current_sequence.append(command)
            else:
                # Non-bash tool or user message breaks the sequence
                if len(current_sequence) >= 3:
                    sequences.append({
                        "commands": current_sequence.copy(),
                        "length": len(current_sequence)
                    })
                current_sequence = []

    # Catch sequence at end
    if len(current_sequence) >= 3:
        sequences.append({
            "commands": current_sequence.copy(),
            "length": len(current_sequence)
        })

    return sequences


def extract_file_edit_patterns(transcript: dict) -> list[dict]:
    """Extract patterns of files edited together.

    Returns: List of file groups that are often edited together
    """
    edit_groups = []

    for turn in transcript.get("turns", []):
        files_in_turn = []
        for content in turn.get("assistant_content", []):
            if content.get("type") == "tool_use" and content.get("tool") in ("Edit", "Write"):
                file_path = content.get("parameters", {}).get("file_path", "")
                if file_path:
                    files_in_turn.append(file_path)

        if len(files_in_turn) >= 2:
            edit_groups.append({
                "files": sorted(set(files_in_turn)),
                "count": len(files_in_turn)
            })

    return edit_groups


def hash_pattern(pattern_data: str) -> str:
    """Generate a stable hash for a pattern."""
    return hashlib.sha256(pattern_data.encode()).hexdigest()[:16]


def analyze_with_llm(potential_patterns: list[dict]) -> list[Pattern]:
    """Use LLM to analyze if patterns are worth automating.

    Args:
        potential_patterns: Raw detected patterns

    Returns:
        List of Pattern objects with LLM assessment
    """
    if not potential_patterns or not is_llm_available():
        return []

    try:
        # Build prompt for LLM
        patterns_text = []
        for i, p in enumerate(potential_patterns, 1):
            if p["type"] == "command_sequence":
                cmds = "\n    ".join(p["commands"])
                patterns_text.append(f"{i}. Command sequence:\n    {cmds}")
            elif p["type"] == "file_edit":
                files = ", ".join(p["files"])
                patterns_text.append(f"{i}. Files edited together: {files}")

        prompt = f"""Analyze these workflow patterns from a developer's coding session:

{chr(10).join(patterns_text)}

For each pattern, determine:
1. Is this worth automating into a skill?
2. What would be a good skill name?
3. How confident are you this is a real, reusable pattern (0-1)?

Consider:
- Is this a common task that repeats often?
- Would automation save meaningful time?
- Is the pattern stable (not ad-hoc debugging)?
- Would other developers benefit from this?

Respond with JSON array:
[
  {{
    "index": 1,
    "automatable": true,
    "skill_name": "restart-and-verify",
    "confidence": 0.9,
    "reason": "Common debugging workflow, repeatable"
  }},
  {{
    "index": 2,
    "automatable": false,
    "confidence": 0.3,
    "reason": "Ad-hoc refactoring, too specific"
  }},
  ...
]

Be conservative: only suggest automation for patterns that are clearly reusable."""

        response = call_claude(prompt, model="claude-haiku-4", max_tokens=2000, temperature=0.0)

        # Parse LLM response
        json_match = response
        if "```json" in response:
            json_match = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_match = response.split("```")[1].split("```")[0].strip()

        assessments = json.loads(json_match)

        # Build Pattern objects with LLM assessment
        patterns = []
        for assessment in assessments:
            idx = assessment["index"] - 1
            if 0 <= idx < len(potential_patterns):
                p = potential_patterns[idx]

                # Create pattern ID
                if p["type"] == "command_sequence":
                    pattern_data = "|".join(p["commands"])
                else:
                    pattern_data = "|".join(p.get("files", []))

                pattern = Pattern(
                    pattern_id=hash_pattern(pattern_data),
                    pattern_type=p["type"],
                    description=assessment.get("reason", ""),
                    occurrences=1,
                    first_seen=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat(),
                    sessions=[],
                    automatable=assessment.get("automatable", False),
                    suggested_skill_name=assessment.get("skill_name"),
                    confidence=assessment.get("confidence", 0.5),
                    commands=p.get("commands") if p["type"] == "command_sequence" else None,
                    files=p.get("files") if p["type"] == "file_edit" else None,
                )

                patterns.append(pattern)

        return patterns

    except Exception as e:
        print(f"# LLM pattern analysis failed: {e}", file=sys.stderr)
        return []


def load_pattern_history(patterns_dir: Path) -> dict[str, Pattern]:
    """Load previously detected patterns from storage.

    Returns: Dict of pattern_id -> Pattern
    """
    patterns = {}

    if not patterns_dir.exists():
        return patterns

    for pattern_file in patterns_dir.glob("*.json"):
        try:
            data = json.loads(pattern_file.read_text())
            pattern = Pattern(**data)
            patterns[pattern.pattern_id] = pattern
        except Exception:
            continue

    return patterns


def save_pattern(pattern: Pattern, patterns_dir: Path) -> None:
    """Save a pattern to storage."""
    patterns_dir.mkdir(parents=True, exist_ok=True)

    pattern_file = patterns_dir / f"{pattern.pattern_id}.json"
    pattern_file.write_text(json.dumps(asdict(pattern), indent=2))


def merge_pattern_occurrence(existing: Pattern, new_session: str) -> Pattern:
    """Merge a new occurrence into existing pattern."""
    existing.occurrences += 1
    existing.last_seen = datetime.now().isoformat()
    if new_session not in existing.sessions:
        existing.sessions.append(new_session)
    return existing


def should_suggest(pattern: Pattern, threshold: int = 3) -> bool:
    """Determine if we should suggest automating this pattern.

    Criteria:
    - Seen at least `threshold` times
    - LLM marked as automatable
    - High confidence (>0.7)
    """
    return (
        pattern.automatable
        and pattern.occurrences >= threshold
        and pattern.confidence >= 0.7
    )


def format_suggestion(pattern: Pattern) -> str:
    """Format a pattern automation suggestion for Claude."""
    output = ["INSTRUCTION: Pattern detected that could be automated. Tell the user:\n\n"]
    output.append(f'"💡 I noticed a repeated workflow pattern:\n\n')

    if pattern.pattern_type == "command_sequence":
        output.append("You\'ve run this sequence across multiple sessions:\n")
        for i, cmd in enumerate(pattern.commands or [], 1):
            # Truncate long commands
            cmd_display = cmd if len(cmd) < 80 else cmd[:77] + "..."
            output.append(f"  {i}. {cmd_display}\n")
    elif pattern.pattern_type == "file_edit":
        output.append("You often edit these files together:\n")
        for f in pattern.files or []:
            output.append(f"  - {f}\n")

    output.append(f"\nSeen {pattern.occurrences} times across {len(pattern.sessions)} sessions.\n\n")

    if pattern.suggested_skill_name:
        output.append(f"Would you like me to create a /{pattern.suggested_skill_name} skill that automates this?\n\n")
        output.append("Say 'yes' to create it, or 'not now' to dismiss (I won't suggest this again).\"\n")

    return "".join(output)


def main():
    """Main hook entry point."""
    # Skip if we're in a hook-spawned session
    if is_hook_session():
        sys.exit(0)

    # Disable pattern learning in CI or if explicitly disabled
    if os.environ.get("CI") or os.environ.get("SHIPKIT_NO_PATTERN_LEARNING") == "1":
        sys.exit(0)

    try:
        # Read event from stdin (session_end event)
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    # Get session info
    session_id = event.get("sessionId", "unknown")
    transcript_path = event.get("transcriptPath")

    if not transcript_path or not Path(transcript_path).exists():
        sys.exit(0)

    # Parse transcript
    try:
        transcript = parse_transcript(transcript_path)
    except Exception:
        sys.exit(0)

    # Skip very short sessions (< 5 turns, probably not interesting)
    if len(transcript.get("turns", [])) < 5:
        sys.exit(0)

    # Extract potential patterns
    command_sequences = extract_command_sequences(transcript)
    file_edit_patterns = extract_file_edit_patterns(transcript)

    if not command_sequences and not file_edit_patterns:
        # No patterns found
        sys.exit(0)

    # Build list of potential patterns for LLM
    potential_patterns = []

    for seq in command_sequences:
        potential_patterns.append({
            "type": "command_sequence",
            "commands": seq["commands"]
        })

    for edit_group in file_edit_patterns:
        potential_patterns.append({
            "type": "file_edit",
            "files": edit_group["files"]
        })

    # Analyze with LLM
    analyzed_patterns = analyze_with_llm(potential_patterns)

    if not analyzed_patterns:
        sys.exit(0)

    # Load pattern history
    home_path = resolve_home_path()
    if not home_path:
        sys.exit(0)

    patterns_dir = home_path / ".state" / "patterns"
    existing_patterns = load_pattern_history(patterns_dir)

    # Merge new patterns with history
    suggestions_to_show = []

    for pattern in analyzed_patterns:
        if pattern.pattern_id in existing_patterns:
            # Update existing pattern
            merged = merge_pattern_occurrence(existing_patterns[pattern.pattern_id], session_id)
            save_pattern(merged, patterns_dir)

            # Check if we should suggest now
            if should_suggest(merged):
                suggestions_to_show.append(merged)
        else:
            # New pattern
            pattern.sessions = [session_id]
            save_pattern(pattern, patterns_dir)
            existing_patterns[pattern.pattern_id] = pattern

    # Output suggestions (only show one at a time to avoid overwhelming)
    if suggestions_to_show:
        # Show the highest confidence suggestion
        best_suggestion = max(suggestions_to_show, key=lambda p: p.confidence)
        output = format_suggestion(best_suggestion)
        print(output, flush=True)

    sys.exit(0)


if __name__ == "__main__":
    main()
