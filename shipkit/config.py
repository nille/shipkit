"""Configuration management for shipkit.

Shipkit stores metadata in ~/.config/shipkit/ (layer preferences, plugin state).
User content lives in Claude Code's native ~/.claude/ directory.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# Shipkit metadata directory
SHIPKIT_HOME = Path(os.environ.get("SHIPKIT_HOME", "~/.config/shipkit")).expanduser()
CONFIG_PATH = SHIPKIT_HOME / "config.yaml"

# Claude Code native directory
CLAUDE_HOME = Path.home() / ".claude"


@dataclass
class ShipkitConfig:
    """Shipkit configuration stored in ~/.config/shipkit/config.yaml"""

    # Which package layers to include when syncing
    layers_core: bool = True  # Always true (required)
    layers_experimental: bool = False  # Opt-in
    layers_advanced: bool = False  # Opt-in

    # Marketplace settings
    marketplace_auto_check: bool = True
    marketplace_last_check: str = ""

    # Plugin registry (installed marketplace plugins)
    plugin_registries: list[str] = field(default_factory=lambda: ["github.com/nille/shipkit-marketplace"])

    def save(self) -> None:
        """Save config to ~/.config/shipkit/config.yaml"""
        SHIPKIT_HOME.mkdir(parents=True, exist_ok=True)

        data = {
            "layers": {
                "core": self.layers_core,
                "experimental": self.layers_experimental,
                "advanced": self.layers_advanced,
            },
            "marketplace": {
                "auto_check": self.marketplace_auto_check,
                "last_check": self.marketplace_last_check,
            },
        }

        if self.plugin_registries != ["github.com/nille/shipkit-marketplace"]:
            data["plugin_registries"] = self.plugin_registries

        CONFIG_PATH.write_text(yaml.dump(data, default_flow_style=False))

    @classmethod
    def load(cls) -> ShipkitConfig:
        """Load config from ~/.config/shipkit/config.yaml"""
        if not CONFIG_PATH.exists():
            return cls()

        data = yaml.safe_load(CONFIG_PATH.read_text()) or {}

        layers = data.get("layers", {})
        marketplace = data.get("marketplace", {})

        return cls(
            layers_core=layers.get("core", True),
            layers_experimental=layers.get("experimental", False),
            layers_advanced=layers.get("advanced", False),
            marketplace_auto_check=marketplace.get("auto_check", True),
            marketplace_last_check=marketplace.get("last_check", ""),
            plugin_registries=data.get("plugin_registries", ["github.com/nille/shipkit-marketplace"])
        )


class ConfigError(Exception):
    pass
