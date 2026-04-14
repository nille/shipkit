"""Data directory management for shipkit.

Shipkit stores metadata in ~/.config/shipkit/ (layer config, plugin state, sessions).
User skills/guidelines live in Claude Code's native ~/.claude/ directory.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from shipkit.config import SHIPKIT_HOME, ShipkitConfig


SEED_DIR = Path(__file__).parent.parent / "seed"

# Shipkit only manages its own metadata, not user skills/guidelines
HOME_DIRS = [
    "plugins",
    ".state/marketplace-cache",
    ".state/sessions",
    ".state/retro/pending",
    ".state/retro/processed",
]


def ensure_home() -> Path:
    """Ensure the shipkit metadata directory exists.

    Creates ~/.config/shipkit/ and subdirectories for shipkit's own state.
    User skills/guidelines live in ~/.claude/ (Claude Code native location).
    """
    home = SHIPKIT_HOME

    home.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    for d in HOME_DIRS:
        (home / d).mkdir(parents=True, exist_ok=True)

    # Create default config if none exists
    if not (home / "config.yaml").exists():
        ShipkitConfig().save()

    return home


def resolve_home() -> Path:
    """Resolve the shipkit metadata directory path.

    Raises DataDirError if the directory doesn't exist.
    """
    if not SHIPKIT_HOME.exists():
        raise DataDirError(
            "Shipkit not initialized. Run 'shipkit init' first."
        )
    return SHIPKIT_HOME


def validate_home(home: Path) -> list[str]:
    """Validate shipkit metadata directory structure, return list of warnings."""
    warnings = []
    for d in HOME_DIRS:
        if not (home / d).exists():
            warnings.append(f"Missing directory: {d}/")
    return warnings


class DataDirError(Exception):
    pass
