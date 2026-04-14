"""Simple project detection for shipkit.

No more project registry - just check if we're in a directory suitable for shipkit.
"""

from __future__ import annotations

from pathlib import Path


def is_claude_project(repo_path: Path | None = None) -> bool:
    """Check if directory is or could be a Claude Code project.

    Returns True if:
    - Has .claude/ directory, OR
    - Has .git/ directory (suitable for shipkit)
    """
    if repo_path is None:
        repo_path = Path.cwd()

    repo_path = repo_path.resolve()

    # Already a Claude Code project
    if (repo_path / ".claude").exists():
        return True

    # Git repo - suitable for shipkit
    if (repo_path / ".git").exists():
        return True

    return False


def ensure_claude_project(repo_path: Path | None = None) -> Path:
    """Ensure we're in a directory suitable for shipkit.

    Raises ProjectError if not in a git repo.
    """
    if repo_path is None:
        repo_path = Path.cwd()

    repo_path = repo_path.resolve()

    if not is_claude_project(repo_path):
        raise ProjectError(
            f"Not a git repository: {repo_path}\n"
            "Shipkit works in git repositories. Run 'git init' first."
        )

    return repo_path


class ProjectError(Exception):
    pass
