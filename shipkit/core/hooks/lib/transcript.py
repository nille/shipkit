"""Transcript extraction and parsing for hook scripts.

Handles Claude Code JSONL transcripts and provides utilities for
extracting conversation turns, building summaries, and generating
session metadata.
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path


def extract_turns(transcript_path: Path, max_turns: int = 200) -> list[dict]:
    """Extract conversation turns from a Claude Code JSONL transcript.

    Returns a list of dicts with 'role' and 'content' fields.
    """
    turns = []
    if not transcript_path.exists():
        return turns

    try:
        for line in transcript_path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Claude Code wraps turns: {"type": "message", "message": {"role": ..., "content": ...}}
            if entry.get("type") == "message" and isinstance(entry.get("message"), dict):
                entry = entry["message"]

            role = entry.get("role", entry.get("type", ""))
            content = entry.get("content", entry.get("message", ""))

            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict):
                        text = block.get("text", block.get("content", ""))
                        if text:
                            text_parts.append(str(text))
                    elif isinstance(block, str):
                        text_parts.append(block)
                content = "\n".join(text_parts)

            if role and content:
                turns.append({"role": str(role), "content": str(content)})

            if len(turns) >= max_turns:
                break
    except (OSError, UnicodeDecodeError):
        pass

    return turns


def build_summary(turns: list[dict], max_chars: int = 10000) -> str:
    """Build a compact summary of the conversation for analysis."""
    if not turns:
        return ""

    lines = []
    total = 0
    for turn in turns:
        role = turn["role"]
        content = turn["content"]
        if len(content) > 500:
            content = content[:500] + "..."
        line = f"[{role}] {content}"
        if total + len(line) > max_chars:
            break
        lines.append(line)
        total += len(line)

    return "\n\n".join(lines)


def generate_title(turns: list[dict]) -> str:
    """Generate a short title from the first user message."""
    for turn in turns:
        if turn["role"] in ("user", "human"):
            text = turn["content"].strip()
            # Take first line, truncate to ~60 chars
            first_line = text.split("\n")[0]
            if len(first_line) > 60:
                first_line = first_line[:57] + "..."
            return first_line
    return "Untitled session"


def session_fingerprint(turns: list[dict]) -> str:
    """Generate a short fingerprint from the last assistant response.

    Used for deduplication and session matching.
    """
    for turn in reversed(turns):
        if turn["role"] in ("assistant",):
            text = turn["content"][-200:]
            return hashlib.sha256(text.encode()).hexdigest()[:12]
    return ""


def count_user_turns(turns: list[dict]) -> int:
    """Count the number of user turns in a conversation."""
    return sum(1 for t in turns if t["role"] in ("user", "human"))


def parse_transcript(transcript_path: Path) -> dict:
    """Parse a Claude Code transcript into structured format with tool uses.

    Returns: Dict with structure:
        {
            "sessionId": "...",
            "turns": [
                {
                    "role": "user|assistant",
                    "assistant_content": [
                        {"type": "tool_use", "tool": "Bash", "parameters": {...}},
                        {"type": "text", "text": "..."},
                        ...
                    ]
                },
                ...
            ]
        }
    """
    if not transcript_path.exists():
        return {"sessionId": "unknown", "turns": []}

    turns = []

    try:
        for line in transcript_path.read_text().splitlines():
            if not line.strip():
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Claude Code format: {"type": "message", "message": {...}}
            if entry.get("type") == "message":
                msg = entry.get("message", {})
                role = msg.get("role", "")
                content = msg.get("content", [])

                turn = {"role": role, "assistant_content": []}

                # Parse content blocks
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict):
                            block_type = block.get("type")

                            if block_type == "tool_use":
                                turn["assistant_content"].append({
                                    "type": "tool_use",
                                    "tool": block.get("name", ""),
                                    "parameters": block.get("input", {}),
                                })
                            elif block_type == "text":
                                turn["assistant_content"].append({
                                    "type": "text",
                                    "text": block.get("text", ""),
                                })

                if turn["assistant_content"]:
                    turns.append(turn)

    except Exception:
        pass

    return {
        "sessionId": str(transcript_path.stem),
        "turns": turns,
    }
