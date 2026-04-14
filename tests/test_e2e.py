"""End-to-end smoke tests for the full shipkit workflow.

Tests the complete pipeline: init → sync → verify generated files.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


class TestEndToEndClaude:
    """Full workflow: sync for Claude Code, verify output."""

    def test_init_sync_generates_all_artifacts(self, initialized_home, tmp_repo, monkeypatch):
        from shipkit.sync import sync_project

        # Set SHIPKIT_HOME to initialized_home (has core content copied)
        monkeypatch.setenv("SHIPKIT_HOME", str(initialized_home))

        # Sync for Claude Code (default)
        result = sync_project(repo_path=tmp_repo)

        # Verify CLAUDE.md with discovery instructions
        claude_md = tmp_repo / "CLAUDE.md"
        assert claude_md.exists()
        content = claude_md.read_text()
        assert "SHIPKIT:BEGIN" in content
        assert "SHIPKIT:END" in content
        assert "Skill Discovery" in content

        # Skills NOT compiled (discovery mode)
        # No .claude/commands/ expected

        # Verify .claude/settings.json (hooks) - may or may not exist depending on hooks
        settings = tmp_repo / ".claude" / "settings.json"
        if settings.exists():
            settings_data = json.loads(settings.read_text())
            assert "hooks" in settings_data

        # Verify .mcp.json (only written if MCPs are configured)
        # With empty default, .mcp.json is not generated
        mcp = tmp_repo / ".mcp.json"
        if mcp.exists():
            mcp_data = json.loads(mcp.read_text())
            assert "mcpServers" in mcp_data

        # Verify no warnings or errors
        assert not result.warnings

    def test_resync_preserves_user_content(self, tmp_home, tmp_repo, monkeypatch):
        from shipkit.sync import sync_project

        # Set SHIPKIT_HOME to tmp_home
        monkeypatch.setenv("SHIPKIT_HOME", str(tmp_home))

        # First sync
        sync_project(repo_path=tmp_repo)

        # Add user content below sentinel
        claude_md = tmp_repo / "CLAUDE.md"
        content = claude_md.read_text()
        claude_md.write_text(content + "\n## My Custom Notes\n\nDo not lose this.\n")

        # Resync
        sync_project(repo_path=tmp_repo)

        # User content preserved
        new_content = claude_md.read_text()
        assert "My Custom Notes" in new_content
        assert "Do not lose this" in new_content
        assert "SHIPKIT:BEGIN" in new_content

    def test_user_guidelines_included(self, tmp_home, tmp_repo, monkeypatch):
        from shipkit.sync import sync_project

        # Set SHIPKIT_HOME to tmp_home
        monkeypatch.setenv("SHIPKIT_HOME", str(tmp_home))

        # Add a user guidelines rule
        guidelines_dir = tmp_home / "guidelines"
        guidelines_dir.mkdir(parents=True, exist_ok=True)
        (guidelines_dir / "my-rule.md").write_text("# My Rule\n\nAlways use tabs.\n")

        sync_project(repo_path=tmp_repo)

        content = (tmp_repo / "CLAUDE.md").read_text()
        assert "Guideline Discovery" in content

    def test_generates_claude_agent_config(self, tmp_home, tmp_repo, monkeypatch):
        """Test sync generates .claude/agents/shipkit.md."""
        from shipkit.sync import sync_project

        # Set SHIPKIT_HOME to tmp_home
        monkeypatch.setenv("SHIPKIT_HOME", str(tmp_home))

        sync_project(repo_path=tmp_repo)

        # Verify agent file exists
        agent_file = tmp_repo / ".claude" / "agents" / "shipkit.md"
        assert agent_file.exists()

        # Verify content structure
        content = agent_file.read_text()
        assert content.startswith("---\n")
        assert "name: shipkit" in content
        assert "You are **Shipkit**" in content


class TestEndToEndPlugins:
    """Verify plugins are included in the compile pipeline."""

    def test_plugin_content_compiled(self, tmp_home, tmp_repo, monkeypatch):
        from shipkit.sync import sync_project

        # Set SHIPKIT_HOME to tmp_home
        monkeypatch.setenv("SHIPKIT_HOME", str(tmp_home))

        # Install a fake plugin
        plugin_dir = tmp_home / "plugins" / "test-plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.yaml").write_text(
            "name: test-plugin\ndescription: Test plugin\nauthor: test\n"
        )
        plugin_guidelines = plugin_dir / "guidelines"
        plugin_guidelines.mkdir()
        (plugin_guidelines / "plugin-rule.md").write_text("# Plugin Rule\n\nFrom plugin.\n")

        sync_project(repo_path=tmp_repo)

        content = (tmp_repo / "CLAUDE.md").read_text()
        assert "From plugin" not in content  # Not compiled
        assert "Guideline Discovery" in content
