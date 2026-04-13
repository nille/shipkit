"""Tests for shipkit CLI commands via Click's CliRunner."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from shipkit.cli import main


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def cli_project(initialized_home, tmp_repo, monkeypatch):
    """A registered project with cwd set to the repo."""
    from shipkit.project import init_project
    init_project(tmp_repo, name="cli-test")
    monkeypatch.chdir(tmp_repo)
    return tmp_repo


class TestVersion:

    def test_version_flag(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "shipkit" in result.output


class TestInit:

    def test_init_registers_project(self, runner, initialized_home, tmp_repo, monkeypatch):
        monkeypatch.chdir(tmp_repo)
        result = runner.invoke(main, ["init"])
        assert result.exit_code == 0
        assert "registered" in result.output
        assert (tmp_repo / ".shipkit").exists()

    def test_init_with_name(self, runner, initialized_home, tmp_repo, monkeypatch):
        monkeypatch.chdir(tmp_repo)
        result = runner.invoke(main, ["init", "--name", "custom"])
        assert result.exit_code == 0
        assert "custom" in result.output

    def test_init_with_template(self, runner, initialized_home, tmp_repo, monkeypatch):
        monkeypatch.chdir(tmp_repo)
        result = runner.invoke(main, ["init", "--template", "python"])
        assert result.exit_code == 0
        assert "registered" in result.output

    def test_init_duplicate_fails(self, runner, cli_project):
        result = runner.invoke(main, ["init"])
        assert result.exit_code != 0
        assert "Already registered" in result.output


class TestSync:

    def test_sync_default(self, runner, cli_project):
        result = runner.invoke(main, ["sync"])
        assert result.exit_code == 0
        assert (cli_project / "CLAUDE.md").exists()

    def test_sync_dry_run(self, runner, cli_project):
        result = runner.invoke(main, ["sync", "--dry-run"])
        assert result.exit_code == 0
        assert "dry-run" in result.output
        assert not (cli_project / "CLAUDE.md").exists()

    def test_sync_tool_override(self, runner, cli_project):
        result = runner.invoke(main, ["sync", "--tool", "kiro"])
        assert result.exit_code == 0
        assert (cli_project / ".kiro" / "guidelines").exists()

    def test_sync_not_registered(self, runner, initialized_home, tmp_path, monkeypatch):
        unregistered = tmp_path / "nope"
        unregistered.mkdir()
        monkeypatch.chdir(unregistered)
        result = runner.invoke(main, ["sync"])
        assert result.exit_code != 0
        assert "Not a shipkit project" in result.output


class TestStatus:

    def test_status_registered(self, runner, cli_project):
        result = runner.invoke(main, ["status"])
        assert result.exit_code == 0
        assert "cli-test" in result.output
        assert "Template:" in result.output

    def test_status_not_registered(self, runner, initialized_home, tmp_path, monkeypatch):
        unregistered = tmp_path / "nope"
        unregistered.mkdir()
        monkeypatch.chdir(unregistered)
        result = runner.invoke(main, ["status"])
        assert result.exit_code == 0
        assert "not registered" in result.output


class TestDoctor:

    def test_doctor_healthy(self, runner, cli_project):
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0
        assert "All checks passed" in result.output

    def test_doctor_no_home(self, runner, tmp_path, monkeypatch):
        nonexistent = tmp_path / "does-not-exist"
        import shipkit.config
        monkeypatch.setattr(shipkit.config, "SHIPKIT_HOME", nonexistent)
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0
        assert "not initialized" in result.output

    def test_doctor_lint(self, runner, initialized_home):
        result = runner.invoke(main, ["doctor", "--lint"])
        assert result.exit_code == 0

    def test_doctor_check(self, runner, initialized_home):
        result = runner.invoke(main, ["doctor", "--check", "json"])
        assert result.exit_code == 0


class TestProjectsList:

    def test_empty(self, runner, initialized_home):
        result = runner.invoke(main, ["projects", "list"])
        assert result.exit_code == 0
        assert "No projects" in result.output

    def test_with_projects(self, runner, cli_project):
        result = runner.invoke(main, ["projects", "list"])
        assert result.exit_code == 0
        assert "cli-test" in result.output


class TestTemplateList:

    def test_lists_templates(self, runner, initialized_home):
        result = runner.invoke(main, ["template", "list"])
        assert result.exit_code == 0
        # Seed templates should be found
        assert "default" in result.output or "No templates" in result.output


class TestTemplateCreate:

    def test_create_from_project(self, runner, cli_project, initialized_home):
        result = runner.invoke(main, ["template", "create", "my-tpl"])
        assert result.exit_code == 0
        assert "my-tpl" in result.output
        assert (initialized_home / "templates" / "my-tpl").exists()

    def test_create_duplicate_fails(self, runner, cli_project, initialized_home):
        runner.invoke(main, ["template", "create", "dupe"])
        result = runner.invoke(main, ["template", "create", "dupe"])
        assert result.exit_code != 0
        assert "already exists" in result.output


class TestPluginList:

    def test_empty(self, runner, initialized_home):
        result = runner.invoke(main, ["plugin", "list"])
        assert result.exit_code == 0
        assert "No plugins" in result.output

    def test_with_plugin(self, runner, initialized_home):
        plugin_dir = initialized_home / "plugins" / "test-plug"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.yaml").write_text(
            "name: test-plug\ndescription: A test\nauthor: me\n"
        )
        result = runner.invoke(main, ["plugin", "list"])
        assert result.exit_code == 0
        assert "test-plug" in result.output


class TestPluginInstall:

    def test_install_local(self, runner, initialized_home, tmp_path):
        src = tmp_path / "my-plugin"
        src.mkdir()
        (src / "plugin.yaml").write_text(
            "name: my-plugin\ndescription: Test\nauthor: me\n"
        )
        result = runner.invoke(main, ["plugin", "install", str(src)])
        assert result.exit_code == 0
        assert "installed" in result.output

    def test_install_no_manifest(self, runner, initialized_home, tmp_path):
        src = tmp_path / "bad-plugin"
        src.mkdir()
        result = runner.invoke(main, ["plugin", "install", str(src)])
        assert result.exit_code != 0
        assert "plugin.yaml" in result.output


class TestPluginUninstall:

    def test_uninstall(self, runner, initialized_home):
        plugin_dir = initialized_home / "plugins" / "rm-me"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.yaml").write_text("name: rm-me\ndescription: x\nauthor: x\n")
        result = runner.invoke(main, ["plugin", "uninstall", "rm-me"])
        assert result.exit_code == 0
        assert "uninstalled" in result.output

    def test_uninstall_missing(self, runner, initialized_home):
        result = runner.invoke(main, ["plugin", "uninstall", "ghost"])
        assert result.exit_code != 0
        assert "not installed" in result.output


class TestAlias:

    def test_generates_snippet(self, runner, cli_project):
        result = runner.invoke(main, ["alias", "sk"])
        assert result.exit_code == 0
        assert "_sk_shipkit" in result.output
        assert "noglob" in result.output
        assert str(cli_project) in result.output

    def test_generates_for_named_project(self, runner, cli_project, initialized_home):
        result = runner.invoke(main, ["alias", "dev", "--project", "cli-test"])
        assert result.exit_code == 0
        assert "_dev_shipkit" in result.output

    def test_install_appends_to_rc(self, runner, cli_project, tmp_path, monkeypatch):
        rc = tmp_path / ".zshrc"
        rc.write_text("# existing config\n")
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        monkeypatch.setenv("SHELL", "/bin/zsh")
        result = runner.invoke(main, ["alias", "sk", "--install"])
        assert result.exit_code == 0
        assert "added" in result.output
        content = rc.read_text()
        assert "_sk_shipkit" in content
        assert "# shipkit alias: sk" in content

    def test_install_detects_duplicate(self, runner, cli_project, tmp_path, monkeypatch):
        rc = tmp_path / ".zshrc"
        rc.write_text("_sk_shipkit() { cd /tmp && shipkit run; }\n")
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        monkeypatch.setenv("SHELL", "/bin/zsh")
        result = runner.invoke(main, ["alias", "sk", "--install"])
        assert result.exit_code == 0
        assert "already exists" in result.output

    def test_install_fish(self, runner, cli_project, tmp_path, monkeypatch):
        fish_config = tmp_path / ".config" / "fish" / "config.fish"
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        monkeypatch.setenv("SHELL", "/usr/bin/fish")
        result = runner.invoke(main, ["alias", "sk", "--install"])
        assert result.exit_code == 0
        assert "added" in result.output
        content = fish_config.read_text()
        assert "function sk" in content
        assert "shipkit run $argv" in content

    def test_fish_snippet(self, runner, cli_project, monkeypatch):
        monkeypatch.setenv("SHELL", "/usr/bin/fish")
        result = runner.invoke(main, ["alias", "sk"])
        assert result.exit_code == 0
        assert "function sk" in result.output
        assert "$argv" in result.output

    def test_not_in_project(self, runner, initialized_home, tmp_path, monkeypatch):
        unregistered = tmp_path / "nope"
        unregistered.mkdir()
        monkeypatch.chdir(unregistered)
        result = runner.invoke(main, ["alias", "sk"])
        assert result.exit_code != 0
