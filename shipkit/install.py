"""Installation logic for shipkit.

Handles copying package core content to user space and creating symlinks.
"""

from __future__ import annotations

import shutil
from pathlib import Path


def get_package_root() -> Path:
    """Get the root directory of the shipkit package."""
    return Path(__file__).parent


def sync_package_core_to_user_space(shipkit_home: Path, force: bool = False) -> dict[str, list[str]]:
    """Copy package core content to ~/.config/shipkit/core/ for user-friendly access.

    Args:
        shipkit_home: ~/.config/shipkit/ directory
        force: If True, overwrite existing core content (for upgrades)

    Returns:
        Dict with 'copied', 'skipped', 'errors' lists
    """
    package_root = get_package_root()
    result = {"copied": [], "skipped": [], "errors": []}

    # Layers to copy
    layers = {
        "core": package_root / "core",
        "experimental": package_root / "experimental",
        "advanced": package_root / "advanced",
    }

    for layer_name, source_dir in layers.items():
        if not source_dir.exists():
            result["errors"].append(f"{layer_name} not found in package: {source_dir}")
            continue

        dest_dir = shipkit_home / layer_name

        # If destination exists and force=False, skip
        if dest_dir.exists() and not force:
            result["skipped"].append(f"{layer_name} (already exists, use --force to update)")
            continue

        # Copy the entire layer directory
        try:
            if dest_dir.exists():
                shutil.rmtree(dest_dir)

            shutil.copytree(source_dir, dest_dir)
            result["copied"].append(f"{layer_name}/ → {dest_dir}")

        except Exception as e:
            result["errors"].append(f"Failed to copy {layer_name}: {e}")

    return result


def create_symlinks_to_claude(shipkit_home: Path, claude_home: Path) -> dict[str, list[str]]:
    """Create symlinks from ~/.config/shipkit/core/ to ~/.claude/ for native discovery.

    Args:
        shipkit_home: ~/.config/shipkit/ directory
        claude_home: ~/.claude/ directory

    Returns:
        Dict with 'created', 'skipped', 'errors' lists
    """
    result = {"created": [], "skipped": [], "errors": []}

    # Create ~/.claude/ if it doesn't exist
    claude_home.mkdir(parents=True, exist_ok=True)

    # Symlink skills from each layer
    layers_to_link = ["core", "experimental", "advanced"]

    for layer_name in layers_to_link:
        layer_skills = shipkit_home / layer_name / "skills"

        if not layer_skills.exists():
            continue

        # Iterate through each skill in this layer
        for skill_dir in layer_skills.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_name = skill_dir.name
            # Just use skill name (no layer prefix)
            target_link = claude_home / "skills" / skill_name

            # Create ~/.claude/skills/ if needed
            (claude_home / "skills").mkdir(parents=True, exist_ok=True)

            # If symlink already exists and points to correct location, skip
            if target_link.exists() or target_link.is_symlink():
                if target_link.is_symlink() and target_link.resolve() == skill_dir:
                    result["skipped"].append(f"{skill_name} (already linked)")
                    continue
                else:
                    # Remove stale/wrong link
                    target_link.unlink(missing_ok=True)

            # Create symlink
            try:
                target_link.symlink_to(skill_dir)
                result["created"].append(f"{layer_name}/{skill_name} → ~/.claude/skills/{skill_name}")
            except Exception as e:
                result["errors"].append(f"Failed to link {skill_name}: {e}")

    return result


def remove_broken_symlinks(claude_home: Path) -> list[str]:
    """Remove broken symlinks from ~/.claude/skills/ (cleanup).

    Returns:
        List of removed symlinks
    """
    removed = []
    skills_dir = claude_home / "skills"

    if not skills_dir.exists():
        return removed

    for item in skills_dir.iterdir():
        if item.is_symlink() and not item.exists():
            # Broken symlink
            item.unlink()
            removed.append(str(item.name))

    return removed
