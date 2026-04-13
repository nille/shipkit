"""Plugin system for shipkit.

Plugins are Git repositories that provide skills, hooks, steering, and
references that extend shipkit. They install into <home>/plugins/<name>/.

Plugin structure:
    plugin.yaml          # Manifest (name, description, author, version)
    skills/              # Skills (same format as shipkit skills)
    hooks/               # Hooks (same YAML + script format)
    steering/            # Steering rules (markdown)
    references/          # Shared reference docs
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml

from shipkit.datadir import resolve_home, DataDirError


@dataclass
class PluginManifest:
    name: str
    description: str
    author: str
    version: str = "0.1.0"
    repo: str = ""

    @classmethod
    def load(cls, path: Path) -> PluginManifest:
        data = yaml.safe_load(path.read_text())
        return cls(
            name=data.get("name", path.parent.name),
            description=data.get("description", ""),
            author=data.get("author", ""),
            version=data.get("version", "0.1.0"),
            repo=data.get("repo", ""),
        )


class PluginError(Exception):
    pass


def get_plugins_dir() -> Path:
    """Get the plugins directory."""
    home = resolve_home()
    plugins_dir = home / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    return plugins_dir


def install_plugin(source: str, name: str | None = None) -> str:
    """Install a plugin from a Git repo URL or local path.

    Returns the installed plugin name.
    """
    plugins_dir = get_plugins_dir()
    source_path = Path(source).expanduser()

    if source_path.exists():
        # Local directory install
        manifest_path = source_path / "plugin.yaml"
        if not manifest_path.exists():
            raise PluginError(f"No plugin.yaml found in {source}")
        manifest = PluginManifest.load(manifest_path)
        plugin_name = name or manifest.name
        target = plugins_dir / plugin_name
        if target.exists():
            raise PluginError(f"Plugin '{plugin_name}' already installed. Uninstall first.")
        shutil.copytree(source_path, target)
    else:
        # Git repo install
        plugin_name = name or _repo_to_name(source)
        target = plugins_dir / plugin_name
        if target.exists():
            raise PluginError(f"Plugin '{plugin_name}' already installed. Uninstall first.")
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", source, str(target)],
                check=True, capture_output=True, text=True,
            )
        except subprocess.CalledProcessError as e:
            raise PluginError(f"Failed to clone {source}: {e.stderr.strip()}")
        except FileNotFoundError:
            raise PluginError("git not found. Install git to use plugin install.")

        # Validate manifest exists
        if not (target / "plugin.yaml").exists():
            shutil.rmtree(target)
            raise PluginError(f"Cloned repo has no plugin.yaml — not a valid shipkit plugin.")

    return plugin_name


def uninstall_plugin(name: str) -> None:
    """Remove an installed plugin."""
    plugins_dir = get_plugins_dir()
    target = plugins_dir / name
    if not target.exists():
        raise PluginError(f"Plugin '{name}' is not installed.")
    shutil.rmtree(target)


def list_plugins() -> list[dict]:
    """List all installed plugins."""
    plugins_dir = get_plugins_dir()
    results = []

    for plugin_dir in sorted(plugins_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue
        manifest_path = plugin_dir / "plugin.yaml"
        if manifest_path.exists():
            manifest = PluginManifest.load(manifest_path)
            skills_count = len([d for d in (plugin_dir / "skills").iterdir() if d.is_dir()]) if (plugin_dir / "skills").exists() else 0
            hooks_count = len(list((plugin_dir / "hooks").glob("*.yaml"))) if (plugin_dir / "hooks").exists() else 0
            results.append({
                "name": manifest.name,
                "description": manifest.description,
                "author": manifest.author,
                "version": manifest.version,
                "skills": skills_count,
                "hooks": hooks_count,
                "path": str(plugin_dir),
            })
        else:
            results.append({
                "name": plugin_dir.name,
                "description": "(no manifest)",
                "author": "",
                "version": "",
                "skills": 0,
                "hooks": 0,
                "path": str(plugin_dir),
            })

    return results


def update_plugin(name: str) -> None:
    """Update an installed plugin by pulling latest from its git remote."""
    plugins_dir = get_plugins_dir()
    target = plugins_dir / name
    if not target.exists():
        raise PluginError(f"Plugin '{name}' is not installed.")

    git_dir = target / ".git"
    if not git_dir.exists():
        raise PluginError(f"Plugin '{name}' was not installed from git — can't update.")

    try:
        subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=str(target), check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as e:
        raise PluginError(f"Failed to update '{name}': {e.stderr.strip()}")


def _repo_to_name(url: str) -> str:
    """Extract a plugin name from a git repo URL."""
    # Handle both HTTPS and SSH URLs
    name = url.rstrip("/").split("/")[-1]
    if name.endswith(".git"):
        name = name[:-4]
    # Strip common prefixes
    for prefix in ("shipkit-plugin-", "shipkit-", "plugin-"):
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    return name
