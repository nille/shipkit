"""Tests for shipkit.sync."""

from __future__ import annotations

from pathlib import Path

import pytest

from shipkit.sync import sync_project


class TestSyncProject:

    def test_sync_creates_claude_md(self, initialized_home, tmp_repo, monkeypatch):
        monkeypatch.chdir(tmp_repo)
        result = sync_project(repo_path=tmp_repo)
        assert (tmp_repo / "CLAUDE.md").exists()
        assert any("CLAUDE.md" in f for f in result.files_written)

    def test_sync_dry_run(self, initialized_home, tmp_repo, monkeypatch):
        monkeypatch.chdir(tmp_repo)
        result = sync_project(repo_path=tmp_repo, dry_run=True)
        assert not (tmp_repo / "CLAUDE.md").exists()

    def test_sync_requires_git_repo(self, initialized_home, tmp_path):
        """Test that sync fails if not in a git repo."""
        non_git_dir = tmp_path / "not-a-repo"
        non_git_dir.mkdir()

        from shipkit.project import ProjectError
        with pytest.raises(ProjectError, match="Not a git repository"):
            sync_project(repo_path=non_git_dir)

    def test_sync_defaults_to_cwd(self, initialized_home, tmp_repo, monkeypatch):
        """Test that sync uses cwd when repo_path not provided."""
        monkeypatch.chdir(tmp_repo)
        result = sync_project()  # No repo_path argument
        assert (tmp_repo / "CLAUDE.md").exists()
