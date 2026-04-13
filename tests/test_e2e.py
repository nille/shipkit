"""End-to-end smoke tests for the full shipkit workflow.

Tests the complete pipeline: init → sync → verify generated files.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


class TestEndToEndClaude:
    """Full workflow: init a project, sync for Claude Code, verify output."""

    def test_init_sync_generates_all_artifacts(self, tmp_home, tmp_repo):
        from shipkit.project import init_project
        from shipkit.sync import sync_project

        # 1. Init the project
        name = init_project(tmp_repo, name="e2e-test")

        # 2. Sync for Claude Code (default)
        result = sync_project(repo_path=tmp_repo)

        # 3. Verify CLAUDE.md with discovery instructions
        claude_md = tmp_repo / "CLAUDE.md"
        assert claude_md.exists()
        content = claude_md.read_text()
        assert "SHIPKIT:BEGIN" in content
        assert "SHIPKIT:END" in content
        assert "Skill Discovery" in content

        # 4. Skills NOT compiled (discovery mode)
        # No .claude/commands/ expected

        # 5. Verify .claude/settings.json (hooks)
        settings = tmp_repo / ".claude" / "settings.json"
        assert settings.exists()
        settings_data = json.loads(settings.read_text())
        assert "hooks" in settings_data

        # 6. Verify .mcp.json
        mcp = tmp_repo / ".mcp.json"
        assert mcp.exists()
        mcp_data = json.loads(mcp.read_text())
        assert "mcpServers" in mcp_data

        # 7. Verify no warnings or errors
        assert not result.warnings

        # 8. Verify project marker
        marker = tmp_repo / ".shipkit"
        assert marker.exists()
        marker_data = json.loads(marker.read_text())
        assert marker_data["name"] == "e2e-test"

    def test_resync_preserves_user_content(self, tmp_home, tmp_repo):
        from shipkit.project import init_project
        from shipkit.sync import sync_project

        init_project(tmp_repo, name="e2e-preserve")

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

    def test_user_guidelines_included(self, tmp_home, tmp_repo):
        from shipkit.project import init_project
        from shipkit.sync import sync_project

        init_project(tmp_repo, name="e2e-guidelines")

        # Add a user guidelines rule
        guidelines_dir = tmp_home / "guidelines"
        guidelines_dir.mkdir(parents=True, exist_ok=True)
        (guidelines_dir / "my-rule.md").write_text("# My Rule\n\nAlways use tabs.\n")

        sync_project(repo_path=tmp_repo)

        content = (tmp_repo / "CLAUDE.md").read_text()
        assert "Guideline Discovery" in content



class TestEndToEndKiro:
    """Full workflow targeting Kiro compiler."""

    def test_init_sync_kiro(self, tmp_home, tmp_repo):
        from shipkit.project import init_project
        from shipkit.sync import sync_project

        init_project(tmp_repo, name="e2e-kiro")
        result = sync_project(repo_path=tmp_repo, tool="kiro")

        # Steering (Kiro uses "steering" not "guidelines")
        steering_dir = tmp_repo / ".kiro" / "steering"
        assert steering_dir.exists()
        md_files = list(steering_dir.glob("*.md"))
        assert len(md_files) >= 2  # skill-discovery + guideline-discovery

        # All managed files have marker
        for f in md_files:
            assert f.read_text().startswith("<!-- shipkit:managed -->")

        # Skills should NOT be compiled (discovery mode)
        # Discovery guideline should be in steering
        discovery_file = steering_dir / "skill-discovery.md"
        assert discovery_file.exists()

        # Agents (subagents still compiled for Kiro)
        agents_dir = tmp_repo / ".kiro" / "agents"
        assert agents_dir.exists()
        json_files = list(agents_dir.glob("*.json"))
        assert len(json_files) >= 1


class TestEndToEndPlugins:
    """Verify plugins are included in the compile pipeline."""

    def test_plugin_content_compiled(self, tmp_home, tmp_repo):
        from shipkit.project import init_project
        from shipkit.sync import sync_project

        init_project(tmp_repo, name="e2e-plugin")

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
        assert "From plugin" in content
