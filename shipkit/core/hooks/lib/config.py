"""Configuration resolution for hook scripts.

Resolves shipkit home path, project name, and detects hook session context.
No external dependencies — uses only stdlib.
"""

from __future__ import annotations

import os
from pathlib import Path


def resolve_home_path() -> Path | None:
    """Resolve the shipkit home directory.

    The home directory is the shipkit data/config directory, defaulting
    to ~/.config/shipkit/ (overridable via SHIPKIT_HOME).
    """
    home = Path(os.environ.get("SHIPKIT_HOME", "~/.config/shipkit")).expanduser()
    if home.exists():
        return home
    return None


# Keep old name as alias for compatibility during migration
resolve_vault_path = resolve_home_path


def resolve_project_name(cwd: str | Path | None = None) -> str | None:
    """Resolve the project name from the .shipkit marker in cwd."""
    if cwd is None:
        cwd = Path.cwd()
    cwd = Path(cwd)

    marker = cwd / ".shipkit"
    if not marker.exists():
        return None

    try:
        import json
        data = json.loads(marker.read_text())
        return data.get("name")
    except Exception:
        return None


def is_hook_session() -> bool:
    """Check if we're running inside a hook-spawned subagent.

    Prevents recursive hook triggers when hooks spawn AI agents.
    """
    return os.environ.get("SHIPKIT_HOOK_SESSION", "") == "1"


def get_shipkit_dir() -> Path:
    """Get the shipkit package directory (where content/ lives)."""
    return Path(__file__).parent.parent.parent


def load_config(home_path: Path) -> dict | None:
    """Load config.yaml from shipkit home.

    Returns: dict with config keys, or None if file doesn't exist
    """
    config_file = home_path / "config.yaml"
    if not config_file.exists():
        return None

    try:
        # Simple YAML parsing without external dependencies
        # Only handles basic key: value format
        config = {}
        for line in config_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, _, value = line.partition(":")
                config[key.strip()] = value.strip()
        return config
    except Exception:
        return None
