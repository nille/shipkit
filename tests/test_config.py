"""Tests for shipkit.config."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from shipkit.config import ShipkitConfig, ProjectConfig, ResolvedConfig, ConfigError


class TestShipkitConfig:

    def test_defaults(self):
        cfg = ShipkitConfig()
        assert cfg.plugin_registries == ["github.com/nille/shipkit-marketplace"]

    def test_save_and_load(self, tmp_home):
        cfg = ShipkitConfig(plugin_registries=["custom.registry"])
        cfg.save()
        loaded = ShipkitConfig.load()
        assert loaded.plugin_registries == ["custom.registry"]

    def test_load_missing_file(self, tmp_home):
        cfg = ShipkitConfig.load()
        assert cfg.plugin_registries == ["github.com/nille/shipkit-marketplace"]

    def test_load_empty_file(self, tmp_home):
        from shipkit.config import CONFIG_PATH
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text("")
        cfg = ShipkitConfig.load()
        assert cfg.plugin_registries == ["github.com/nille/shipkit-marketplace"]


class TestProjectConfig:

    def test_defaults(self):
        cfg = ProjectConfig()
        assert cfg.name == ""
        assert cfg.template == "default"

    def test_save_and_load(self, tmp_path):
        yaml_path = tmp_path / "project.yaml"
        cfg = ProjectConfig(name="my-proj", repo_path="/tmp/repo", template="python")
        cfg.save(yaml_path)

        loaded = ProjectConfig.load(yaml_path)
        assert loaded.name == "my-proj"
        assert loaded.repo_path == "/tmp/repo"
        assert loaded.template == "python"

    def test_load_missing_file(self, tmp_path):
        cfg = ProjectConfig.load(tmp_path / "nonexistent.yaml")
        assert cfg.name == ""


class TestResolvedConfig:

    def test_resolve_no_home(self, tmp_path, monkeypatch):
        nonexistent = tmp_path / "does-not-exist"
        import shipkit.config
        monkeypatch.setattr(shipkit.config, "SHIPKIT_HOME", nonexistent)
        with pytest.raises(ConfigError, match="not initialized"):
            ResolvedConfig.resolve()

    def test_resolve_defaults(self, initialized_home):
        cfg = ResolvedConfig.resolve()
        assert cfg.home_path == initialized_home
        assert cfg.project_name == ""
