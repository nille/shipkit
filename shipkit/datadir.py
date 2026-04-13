"""Data directory management for shipkit.

The shipkit home directory (~/.config/shipkit/ by default) holds all user
content: skills, steering, projects, plugins, and machine state. It is
auto-created on first use via ensure_home().
"""

from __future__ import annotations

import shutil
from pathlib import Path

from shipkit.config import SHIPKIT_HOME, ShipkitConfig


SEED_DIR = Path(__file__).parent.parent / "seed"

HOME_DIRS = [
    "skills",
    "steering",
    "references",
    "templates",
    "projects",
    "hooks",
    "plugins",
    ".state/sessions",
    ".state/retro/pending",
    ".state/retro/processed",
]


def ensure_home() -> Path:
    """Ensure the shipkit home directory exists with required structure.

    Creates the directory and subdirectories on first use. Safe to call
    repeatedly — existing content is never overwritten.
    """
    home = SHIPKIT_HOME

    if home.exists() and (home / "skills").exists():
        return home  # Already initialized

    home.mkdir(parents=True, exist_ok=True)

    for d in HOME_DIRS:
        (home / d).mkdir(parents=True, exist_ok=True)

    # Copy seed templates if available and not already present
    seed_templates = SEED_DIR / "templates"
    templates_dir = home / "templates"
    if seed_templates.exists() and not any(templates_dir.iterdir()):
        shutil.copytree(seed_templates, templates_dir, dirs_exist_ok=True)

    # Create default config if none exists
    if not (home / "config.yaml").exists():
        ShipkitConfig().save()

    return home


def resolve_home() -> Path:
    """Resolve the shipkit home directory path.

    Raises DataDirError if the home directory doesn't exist.
    """
    if not SHIPKIT_HOME.exists():
        raise DataDirError(
            "Ship-kit not initialized. Run 'shipkit init' in a project first."
        )
    return SHIPKIT_HOME


def validate_home(home: Path) -> list[str]:
    """Validate home directory structure, return list of warnings."""
    warnings = []
    for d in HOME_DIRS:
        if not (home / d).exists():
            warnings.append(f"Missing directory: {d}/")
    return warnings


class DataDirError(Exception):
    pass
