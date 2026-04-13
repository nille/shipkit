"""Structured logging for hook scripts.

Writes timestamped, ANSI-stripped log entries to vault log files.
Supports rotation and debug mode. No external dependencies.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path

from .config import resolve_vault_path

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
_MAX_LOG_SIZE = 1_000_000  # 1 MB


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return _ANSI_RE.sub("", text)


def get_log_path(name: str) -> Path:
    """Get the log file path for a named hook.

    Logs live in <vault>/logs/<name>.log.
    """
    vault = resolve_vault_path()
    if vault is None:
        return Path("/tmp") / f"shipkit-{name}.log"

    logs_dir = vault / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir / f"{name}.log"


def rotate_if_needed(log_path: Path) -> None:
    """Rotate log file if it exceeds max size. Keeps one backup."""
    if not log_path.exists():
        return
    if log_path.stat().st_size < _MAX_LOG_SIZE:
        return

    backup = log_path.with_suffix(".log.1")
    if backup.exists():
        backup.unlink()
    log_path.rename(backup)


def log_entry(name: str, message: str, context: str | None = None) -> None:
    """Append a timestamped log entry."""
    log_path = get_log_path(name)
    rotate_if_needed(log_path)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    clean_msg = strip_ansi(message)
    entry = f"[{ts}] {clean_msg}"
    if context:
        entry += f" | {strip_ansi(context)}"

    with open(log_path, "a") as f:
        f.write(entry + "\n")


def debug_log(name: str, message: str) -> None:
    """Log only when SHIPKIT_DEBUG=1 is set."""
    if os.environ.get("SHIPKIT_DEBUG") == "1":
        log_entry(name, f"[DEBUG] {message}")


def open_log_file(name: str):
    """Open the log file for writing (for subprocess redirection).

    Returns a file object suitable for subprocess stdout/stderr.
    """
    log_path = get_log_path(name)
    rotate_if_needed(log_path)
    return open(log_path, "a")
