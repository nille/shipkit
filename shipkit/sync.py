"""Sync orchestration for shipkit.

Orchestrates the compile pipeline: resolve project, load layers, run compiler.
"""

from __future__ import annotations

from pathlib import Path

from shipkit.compilers.base import CompileContext, CompileResult, get_compiler
from shipkit.config import ResolvedConfig
from shipkit.project import resolve_project
from shipkit.datadir import resolve_home


def sync_project(
    repo_path: Path | None = None,
    dry_run: bool = False,
) -> CompileResult:
    """Sync shipkit content to Claude Code config for the given project.

    Args:
        repo_path: Path to the repo. Defaults to cwd.
        dry_run: If True, report what would change without writing.

    Returns:
        CompileResult with files written, skipped, and warnings.
    """
    if repo_path is None:
        repo_path = Path.cwd()
    repo_path = repo_path.resolve()

    home_path = resolve_home()
    project_name, _project_dir = resolve_project(repo_path)

    # Always use Claude Code compiler
    compiler = get_compiler("claude")

    ctx = CompileContext(
        home_path=home_path,
        repo_path=repo_path,
        project_name=project_name,
    )

    return compiler.compile(ctx, dry_run=dry_run)


def sync_all(dry_run: bool = False) -> dict[str, CompileResult]:
    """Sync all registered projects."""
    from shipkit.project import list_projects

    results = {}
    for project in list_projects():
        repo_path = Path(project["repo_path"])
        if not repo_path.exists():
            results[project["name"]] = CompileResult(
                files_written=[],
                files_skipped=[],
                warnings=[f"Repo path does not exist: {repo_path}"],
            )
            continue
        results[project["name"]] = sync_project(repo_path, dry_run=dry_run)
    return results
