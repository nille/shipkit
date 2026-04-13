"""Tests for shipkit.plugin."""

from __future__ import annotations

from pathlib import Path

import pytest

from shipkit.plugin import (
    install_plugin, uninstall_plugin, list_plugins,
    PluginError, _repo_to_name,
)


@pytest.fixture
def local_plugin(tmp_path):
    """Create a local plugin directory."""
    plugin_dir = tmp_path / "my-local-plugin"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.yaml").write_text(
        "name: my-plugin\ndescription: A test plugin\nauthor: test\nversion: 1.0.0\n"
    )
    (plugin_dir / "skills").mkdir()
    skill_dir = plugin_dir / "skills" / "hello"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Hello\n\nSay hello.\n")
    return plugin_dir


class TestInstallPlugin:

    def test_install_local(self, initialized_home, local_plugin):
        name = install_plugin(str(local_plugin))
        assert name == "my-plugin"
        installed = initialized_home / "plugins" / "my-plugin"
        assert installed.exists()
        assert (installed / "plugin.yaml").exists()

    def test_install_local_custom_name(self, initialized_home, local_plugin):
        name = install_plugin(str(local_plugin), name="custom")
        assert name == "custom"
        assert (initialized_home / "plugins" / "custom").exists()

    def test_install_rejects_duplicate(self, initialized_home, local_plugin):
        install_plugin(str(local_plugin))
        with pytest.raises(PluginError, match="already installed"):
            install_plugin(str(local_plugin))

    def test_install_rejects_no_manifest(self, initialized_home, tmp_path):
        no_manifest = tmp_path / "bad-plugin"
        no_manifest.mkdir()
        with pytest.raises(PluginError, match="No plugin.yaml"):
            install_plugin(str(no_manifest))


class TestUninstallPlugin:

    def test_uninstall(self, initialized_home, local_plugin):
        install_plugin(str(local_plugin))
        uninstall_plugin("my-plugin")
        assert not (initialized_home / "plugins" / "my-plugin").exists()

    def test_uninstall_missing(self, initialized_home):
        with pytest.raises(PluginError, match="not installed"):
            uninstall_plugin("nonexistent")


class TestListPlugins:

    def test_empty_list(self, initialized_home):
        assert list_plugins() == []

    def test_list_installed(self, initialized_home, local_plugin):
        install_plugin(str(local_plugin))
        plugins = list_plugins()
        assert len(plugins) == 1
        assert plugins[0]["name"] == "my-plugin"
        assert plugins[0]["skills"] == 1


class TestRepoToName:

    def test_https_url(self):
        assert _repo_to_name("https://github.com/user/my-tool.git") == "my-tool"

    def test_strips_shipkit_prefix(self):
        assert _repo_to_name("https://github.com/user/shipkit-plugin-auth.git") == "auth"

    def test_strips_plugin_prefix(self):
        assert _repo_to_name("https://github.com/user/plugin-lint.git") == "lint"

    def test_ssh_url(self):
        assert _repo_to_name("git@github.com:user/my-tool.git") == "my-tool"

    def test_trailing_slash(self):
        assert _repo_to_name("https://github.com/user/my-tool/") == "my-tool"
