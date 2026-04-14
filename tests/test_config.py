"""Tests for shipkit.config."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from shipkit.config import ShipkitConfig, ConfigError, CLAUDE_HOME


class TestShipkitConfig:

    def test_defaults(self):
        cfg = ShipkitConfig()
        assert cfg.layers_core is True
        assert cfg.layers_experimental is False
        assert cfg.layers_advanced is False
        assert cfg.marketplace_auto_check is True
        assert cfg.plugin_registries == ["github.com/nille/shipkit-marketplace"]

    def test_save_and_load(self, tmp_home):
        cfg = ShipkitConfig(
            layers_experimental=True,
            layers_advanced=True,
            plugin_registries=["custom.registry"]
        )
        cfg.save()
        loaded = ShipkitConfig.load()
        assert loaded.layers_experimental is True
        assert loaded.layers_advanced is True
        assert loaded.plugin_registries == ["custom.registry"]

    def test_load_missing_file(self, tmp_home):
        cfg = ShipkitConfig.load()
        assert cfg.layers_core is True
        assert cfg.layers_experimental is False

    def test_load_empty_file(self, tmp_home):
        from shipkit.config import CONFIG_PATH
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text("")
        cfg = ShipkitConfig.load()
        assert cfg.layers_core is True

    def test_saves_layer_config(self, tmp_home):
        cfg = ShipkitConfig(layers_experimental=True, layers_advanced=True)
        cfg.save()

        from shipkit.config import CONFIG_PATH
        data = yaml.safe_load(CONFIG_PATH.read_text())

        assert data["layers"]["core"] is True
        assert data["layers"]["experimental"] is True
        assert data["layers"]["advanced"] is True

    def test_marketplace_config(self, tmp_home):
        cfg = ShipkitConfig(marketplace_auto_check=False, marketplace_last_check="2026-04-14")
        cfg.save()

        from shipkit.config import CONFIG_PATH
        data = yaml.safe_load(CONFIG_PATH.read_text())

        assert data["marketplace"]["auto_check"] is False
        assert data["marketplace"]["last_check"] == "2026-04-14"


class TestClaudeHome:

    def test_claude_home_constant(self):
        """Test CLAUDE_HOME points to ~/.claude"""
        assert CLAUDE_HOME == Path.home() / ".claude"
