"""Tests for shipkit.config."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from shipkit.config import ShipkitConfig, ProjectConfig, ResolvedConfig, ConfigError


class TestShipkitConfig:

    def test_defaults(self):
        cfg = ShipkitConfig()
        assert cfg.cli_tool == "claude"

    def test_save_and_load(self, tmp_home):
        cfg = ShipkitConfig(cli_tool="kiro")
        cfg.save()
        loaded = ShipkitConfig.load()
        assert loaded.cli_tool == "kiro"

    def test_load_missing_file(self, tmp_home):
        cfg = ShipkitConfig.load()
        assert cfg.cli_tool == "claude"

    def test_load_empty_file(self, tmp_home):
        from shipkit.config import CONFIG_PATH
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text("")
        cfg = ShipkitConfig.load()
        assert cfg.cli_tool == "claude"


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

    def test_cli_tool_override(self, tmp_path):
        yaml_path = tmp_path / "project.yaml"
        cfg = ProjectConfig(name="p", repo_path="/tmp", cli_tool="kiro")
        cfg.save(yaml_path)

        loaded = ProjectConfig.load(yaml_path)
        assert loaded.cli_tool == "kiro"

    def test_cli_tool_not_written_when_empty(self, tmp_path):
        yaml_path = tmp_path / "project.yaml"
        cfg = ProjectConfig(name="p", repo_path="/tmp")
        cfg.save(yaml_path)

        raw = yaml.safe_load(yaml_path.read_text())
        assert "cli_tool" not in raw


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
        assert cfg.cli_tool == "claude"

    def test_resolve_with_config(self, initialized_home):
        ShipkitConfig(cli_tool="kiro").save()
        cfg = ResolvedConfig.resolve()
        assert cfg.cli_tool == "kiro"

    def test_resolve_project_overrides_cli_tool(self, registered_project):
        repo, name = registered_project
        from shipkit.config import SHIPKIT_HOME
        proj_yaml = SHIPKIT_HOME / "projects" / name / "project.yaml"
        proj_cfg = ProjectConfig.load(proj_yaml)
        proj_cfg.cli_tool = "kiro"
        proj_cfg.save(proj_yaml)

        cfg = ResolvedConfig.resolve(name)
        assert cfg.cli_tool == "kiro"
