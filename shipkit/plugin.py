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
    """Install a plugin from a Git repo URL, local path, or marketplace short name.

    Returns the installed plugin name.
    """
    plugins_dir = get_plugins_dir()
    source_path = Path(source).expanduser()

    # Check if it's a local directory
    if source_path.exists():
        manifest_path = source_path / "plugin.yaml"
        if not manifest_path.exists():
            raise PluginError(f"No plugin.yaml found in {source}")
        manifest = PluginManifest.load(manifest_path)
        plugin_name = name or manifest.name
        target = plugins_dir / plugin_name
        if target.exists():
            raise PluginError(f"Plugin '{plugin_name}' already installed. Uninstall first.")
        shutil.copytree(source_path, target)
        return plugin_name

    # Check if it's a short name (no /, no protocol, not a URL)
    if "/" not in source and not source.startswith(("http://", "https://", "git@")):
        # Try marketplace registries
        from shipkit.config import ShipkitConfig
        config = ShipkitConfig.load()
        for registry in config.plugin_registries:
            try:
                plugin_name = _install_from_registry(registry, source, name)
                return plugin_name
            except PluginError:
                continue  # Try next registry
        raise PluginError(
            f"Plugin '{source}' not found in any registry. "
            f"Searched: {', '.join(config.plugin_registries)}"
        )

    # Git repo install (full URL)
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


def _install_from_registry(registry: str, plugin_name: str, override_name: str | None = None) -> str:
    """Install a plugin from a marketplace registry.

    Clones the registry temporarily and copies the plugin subdirectory.
    """
    import tempfile

    plugins_dir = get_plugins_dir()

    # Normalize registry to git URL
    if not registry.startswith(("http://", "https://", "git@")):
        registry_url = f"https://{registry}.git"
    else:
        registry_url = registry

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Clone registry
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", registry_url, str(tmpdir_path / "registry")],
                check=True, capture_output=True, text=True,
            )
        except subprocess.CalledProcessError as e:
            raise PluginError(f"Failed to clone registry {registry}: {e.stderr.strip()}")

        registry_path = tmpdir_path / "registry"
        plugin_source = registry_path / plugin_name

        # Check if plugin exists in registry
        if not plugin_source.exists():
            raise PluginError(f"Plugin '{plugin_name}' not found in registry {registry}")

        manifest_path = plugin_source / "plugin.yaml"
        if not manifest_path.exists():
            raise PluginError(f"Plugin '{plugin_name}' in registry has no plugin.yaml")

        # Install the plugin
        manifest = PluginManifest.load(manifest_path)
        final_name = override_name or manifest.name
        target = plugins_dir / final_name

        if target.exists():
            raise PluginError(f"Plugin '{final_name}' already installed. Uninstall first.")

        shutil.copytree(plugin_source, target)
        return final_name


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
