"""Sync orchestration for shipkit.

Orchestrates the compile pipeline: resolve layers, run compiler, write output.
"""

from __future__ import annotations

from pathlib import Path

from shipkit.compilers.base import CompileContext, CompileResult, get_compiler
from shipkit.datadir import resolve_home
from shipkit.project import ensure_claude_project


def sync_project(
    repo_path: Path | None = None,
    dry_run: bool = False,
) -> CompileResult:
    """Sync shipkit content to Claude Code config for the current project.

    Args:
        repo_path: Path to the repo. Defaults to cwd.
        dry_run: If True, report what would change without writing.

    Returns:
        CompileResult with files written, skipped, and warnings.
    """
    if repo_path is None:
        repo_path = Path.cwd()

    # Ensure we're in a git repo (suitable for shipkit)
    repo_path = ensure_claude_project(repo_path)

    shipkit_home = resolve_home()

    # Always use Claude Code compiler
    compiler = get_compiler("claude")

    ctx = CompileContext(
        shipkit_home=shipkit_home,
        repo_path=repo_path,
    )

    return compiler.compile(ctx, dry_run=dry_run)
