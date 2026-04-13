"""Debounced execution pattern for stop/session-end hooks.

Implements the trigger/waiter/runner pattern: rapid repeated invocations
coalesce into a single execution after a quiet period.

Pattern:
1. Hook fires → touches trigger file → spawns waiter
2. Waiter sleeps for debounce_secs
3. Waiter checks if trigger is still fresh (no newer trigger arrived)
4. If fresh → runs the actual work; if stale → exits (newer waiter handles it)
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from .config import resolve_vault_path
from .logging_util import log_entry, debug_log
from .process import spawn_detached, kill_pid_file


def get_debounce_dir() -> Path:
    """Get the directory for debounce state files."""
    vault = resolve_vault_path()
    base = vault / ".state" if vault else Path("/tmp") / "shipkit-state"
    debounce_dir = base / "debounce"
    debounce_dir.mkdir(parents=True, exist_ok=True)
    return debounce_dir


def debounced_spawn(
    hook_name: str,
    session_id: str,
    transcript_data: str,
    runner_cmd: list[str],
    debounce_secs: int = 60,
) -> None:
    """Trigger a debounced execution.

    Saves transcript data, touches a trigger file, kills any existing
    runner for this session, and spawns a waiter process.
    """
    debounce_dir = get_debounce_dir()
    namespace = f"{hook_name}.{session_id}"

    # Save transcript data for the runner
    transcript_file = debounce_dir / f"{namespace}.transcript"
    transcript_file.write_text(transcript_data)

    # Touch trigger file (mtime = timestamp of this invocation)
    trigger_file = debounce_dir / f"{namespace}.trigger"
    trigger_file.touch()

    # Kill any existing runner for this session
    pid_file = debounce_dir / f"{namespace}.pid"
    if pid_file.exists():
        killed = kill_pid_file(pid_file)
        if killed:
            debug_log(hook_name, f"Killed existing runner for {session_id}")

    # Spawn waiter process (re-invokes this hook script with --wait flag)
    waiter_cmd = [
        sys.executable, "-c",
        f"from shipkit.content.hooks.lib.debounce import _waiter_main; "
        f"_waiter_main({debounce_secs!r}, {hook_name!r}, {session_id!r}, {runner_cmd!r})"
    ]
    spawn_detached(waiter_cmd, log_name=f"{hook_name}-waiter")
    debug_log(hook_name, f"Spawned waiter for {session_id} (debounce={debounce_secs}s)")


def _waiter_main(
    debounce_secs: int,
    hook_name: str,
    session_id: str,
    runner_cmd: list[str],
) -> None:
    """Waiter process: sleep then check if trigger is still fresh."""
    debounce_dir = get_debounce_dir()
    namespace = f"{hook_name}.{session_id}"

    trigger_file = debounce_dir / f"{namespace}.trigger"
    if not trigger_file.exists():
        return

    # Record trigger mtime before sleeping
    trigger_mtime = trigger_file.stat().st_mtime
    time.sleep(debounce_secs)

    # Check if trigger is still fresh (no newer invocation)
    if not trigger_file.exists():
        return
    if trigger_file.stat().st_mtime != trigger_mtime:
        debug_log(hook_name, f"Stale trigger for {session_id}, newer waiter will handle")
        return

    # Trigger is fresh — run the actual work
    log_entry(hook_name, f"Running after {debounce_secs}s debounce for {session_id}")

    transcript_file = debounce_dir / f"{namespace}.transcript"
    pid_file = debounce_dir / f"{namespace}.pid"

    # Set up environment with transcript path
    env = {"SHIPKIT_TRANSCRIPT_FILE": str(transcript_file)}

    spawn_detached(
        runner_cmd,
        log_name=hook_name,
        env=env,
        pid_file=pid_file,
    )


def cleanup_debounce(hook_name: str, session_id: str) -> None:
    """Clean up debounce state files after successful run."""
    debounce_dir = get_debounce_dir()
    namespace = f"{hook_name}.{session_id}"

    for suffix in (".trigger", ".transcript", ".pid"):
        f = debounce_dir / f"{namespace}{suffix}"
        f.unlink(missing_ok=True)
