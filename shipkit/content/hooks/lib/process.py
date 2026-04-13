"""Cross-platform detached process spawning and PID management.

Provides utilities for launching background processes that survive
the parent shell, and for tracking/killing them via PID files.
No external dependencies.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path

from .logging_util import open_log_file, debug_log


def spawn_detached(
    cmd: list[str],
    log_name: str | None = None,
    env: dict[str, str] | None = None,
    cwd: str | Path | None = None,
    pid_file: Path | None = None,
) -> int:
    """Launch a fully detached background process.

    Returns the PID of the spawned process.
    """
    merged_env = {**os.environ, **(env or {})}
    # Prevent recursive hook triggers
    merged_env["SHIPKIT_HOOK_SESSION"] = "1"

    kwargs: dict = {
        "env": merged_env,
        "cwd": str(cwd) if cwd else None,
    }

    if log_name:
        log_file = open_log_file(log_name)
        kwargs["stdout"] = log_file
        kwargs["stderr"] = log_file
    else:
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL

    kwargs["stdin"] = subprocess.DEVNULL

    if sys.platform == "win32":
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        DETACHED_PROCESS = 0x00000008
        kwargs["creationflags"] = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True

    proc = subprocess.Popen(cmd, **kwargs)

    if pid_file:
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(proc.pid))
        debug_log("process", f"PID {proc.pid} written to {pid_file}")

    return proc.pid


def kill_pid(pid: int) -> bool:
    """Kill a process by PID. Returns True if killed successfully."""
    try:
        if sys.platform == "win32":
            os.kill(pid, signal.SIGTERM)
        else:
            # Kill the process group
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        return True
    except (ProcessLookupError, PermissionError, OSError):
        return False


def kill_pid_file(pid_file: Path) -> bool:
    """Kill the process tracked by a PID file, then remove the file."""
    if not pid_file.exists():
        return False

    try:
        pid = int(pid_file.read_text().strip())
    except (ValueError, OSError):
        pid_file.unlink(missing_ok=True)
        return False

    result = kill_pid(pid)
    pid_file.unlink(missing_ok=True)
    return result
