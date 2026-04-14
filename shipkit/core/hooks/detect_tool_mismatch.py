#!/usr/bin/env python3
"""Session-start hook: detect tool mismatch and suggest migration.

Checks if the current CLI tool matches the configured tool preference.
If there's a mismatch, suggests running /migrate-tool.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Hook lib is in the same package
sys.path.insert(0, str(Path(__file__).parent))

from lib.config import resolve_home_path, is_hook_session, load_config


def _detect_current_tool() -> str | None:
    """Detect which AI coding tool is running this session.

    Returns: 'claude', 'kiro', 'gemini', 'opencode', or None if unknown
    """
    # Check environment variables
    if os.environ.get("CLAUDE_CLI_VERSION") or os.environ.get("CLAUDE_CODE_VERSION"):
        return "claude"
    if os.environ.get("KIRO_VERSION") or os.environ.get("KIRO_CLI_VERSION"):
        return "kiro"
    if os.environ.get("GEMINI_CLI_VERSION"):
        return "gemini"
    if os.environ.get("OPENCODE_VERSION"):
        return "opencode"

    # Check parent process (fallback - less reliable)
    try:
        import psutil
        parent = psutil.Process(os.getppid())
        parent_name = parent.name().lower()

        if "claude" in parent_name:
            return "claude"
        if "kiro" in parent_name:
            return "kiro"
        if "gemini" in parent_name:
            return "gemini"
        if "opencode" in parent_name:
            return "opencode"
    except (ImportError, Exception):
        pass

    # Check current working directory for tool-native config files
    cwd = Path.cwd()
    if (cwd / "CLAUDE.md").exists():
        return "claude"
    if (cwd / ".kiro" / "steering").exists():
        return "kiro"
    if (cwd / "GEMINI.md").exists():
        return "gemini"
    if (cwd / "AGENTS.md").exists():
        return "opencode"

    return None


def _output_mismatch_message(configured: str, detected: str) -> None:
    """Print the tool mismatch notification for agent context injection."""
    print(
        f"INSTRUCTION: Tool mismatch detected. Configured: {configured}, Running: {detected}. "
        f"At a natural pause, mention: \"I notice you're using {detected} but shipkit is configured for {configured}. "
        f"Want to migrate? Say 'migrate tool' or run /migrate-tool to switch your personal skills and guidelines to {detected}.\" "
        f"Only mention this once per session."
    )


def main() -> None:
    if is_hook_session():
        return

    home_path = resolve_home_path()
    if not home_path:
        return

    # Load config
    cfg = load_config(home_path)
    if not cfg:
        return

    configured_tool = cfg.get("cli_tool", "claude")

    # Detect current tool
    detected_tool = _detect_current_tool()
    if not detected_tool:
        # Can't detect, skip
        return

    # Check for mismatch
    if configured_tool != detected_tool:
        _output_mismatch_message(configured_tool, detected_tool)


if __name__ == "__main__":
    main()
