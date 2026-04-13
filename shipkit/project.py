"""Project registration and management for shipkit.

Handles the two-way link between home project entries and repo markers.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from shipkit.config import ProjectConfig
from shipkit.datadir import resolve_home, ensure_home, SEED_DIR


MARKER_FILE = ".shipkit"


def init_project(repo_path: Path, name: str | None = None, template: str = "default") -> str:
    """Register the repo as a shipkit project.

    Creates:
    - <home>/projects/<name>/project.yaml
    - <repo>/.shipkit marker file
    """
    repo_path = repo_path.resolve()
    home_path = ensure_home()

    if name is None:
        name = repo_path.name

    # Check for existing registration
    marker = repo_path / MARKER_FILE
    if marker.exists():
        existing = json.loads(marker.read_text())
        raise ProjectError(f"Already registered as project '{existing.get('name', '?')}'")

    project_dir = home_path / "projects" / name
    if project_dir.exists():
        raise ProjectError(f"Project '{name}' already exists in home. Choose a different name.")

    # Create project entry
    project_dir.mkdir(parents=True)
    (project_dir / "guidelines").mkdir()
    (project_dir / "knowledge").mkdir()
    (project_dir / "skills").mkdir()

    # Apply template content if it exists
    template_dir = home_path / "templates" / template
    if not template_dir.exists():
        # Fall back to seed templates shipped with the package
        template_dir = SEED_DIR / "templates" / template
    if template_dir.exists():
        for subdir in ["guidelines", "skills"]:
            src = template_dir / subdir
            if src.exists():
                dst = project_dir / subdir
                for item in src.iterdir():
                    dest_item = dst / item.name
                    if item.is_dir():
                        shutil.copytree(item, dest_item, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, dest_item)

    cfg = ProjectConfig(name=name, repo_path=str(repo_path), template=template)
    cfg.save(project_dir / "project.yaml")

    # Create repo marker
    marker.write_text(json.dumps({"name": name}, indent=2) + "\n")

    return name


def resolve_project(repo_path: Path | None = None) -> tuple[str, Path]:
    """Resolve current project name and home project dir from cwd or given path.

    Returns (project_name, home_project_dir).
    """
    if repo_path is None:
        repo_path = Path.cwd()
    repo_path = repo_path.resolve()

    marker = repo_path / MARKER_FILE
    if not marker.exists():
        raise ProjectError(f"Not a shipkit project (no {MARKER_FILE} found). Run 'shipkit init' first.")

    data = json.loads(marker.read_text())
    name = data.get("name", repo_path.name)

    home_path = resolve_home()
    project_dir = home_path / "projects" / name

    if not project_dir.exists():
        raise ProjectError(f"Project '{name}' not found in home at {project_dir}")

    return name, project_dir


def list_projects() -> list[dict]:
    """List all registered projects."""
    home_path = resolve_home()
    projects_dir = home_path / "projects"
    if not projects_dir.exists():
        return []

    results = []
    for project_dir in sorted(projects_dir.iterdir()):
        if not project_dir.is_dir():
            continue
        project_yaml = project_dir / "project.yaml"
        cfg = ProjectConfig.load(project_yaml)
        repo_exists = Path(cfg.repo_path).exists() if cfg.repo_path else False
        results.append({
            "name": cfg.name or project_dir.name,
            "repo_path": cfg.repo_path,
            "template": cfg.template,
            "repo_exists": repo_exists,
        })
    return results


class ProjectError(Exception):
    pass
