"""Tests for shipkit.sync."""

from __future__ import annotations

from pathlib import Path

import pytest

from shipkit.sync import sync_project, sync_all


class TestSyncProject:

    def test_sync_creates_claude_md(self, registered_project):
        repo, name = registered_project
        result = sync_project(repo_path=repo)
        assert (repo / "CLAUDE.md").exists()
        assert any("CLAUDE.md" in f for f in result.files_written)

    def test_sync_dry_run(self, registered_project):
        repo, name = registered_project
        result = sync_project(repo_path=repo, dry_run=True)
        assert not (repo / "CLAUDE.md").exists()


class TestSyncAll:

    def test_sync_all_multiple_projects(self, initialized_home, tmp_path):
        from shipkit.project import init_project

        repos = []
        for i in range(2):
            repo = tmp_path / f"repo-{i}"
            repo.mkdir()
            init_project(repo, name=f"proj-{i}")
            repos.append(repo)

        results = sync_all()
        assert len(results) == 2
        for repo in repos:
            assert (repo / "CLAUDE.md").exists()

    def test_sync_all_handles_missing_repo(self, initialized_home, tmp_path):
        from shipkit.project import init_project

        repo = tmp_path / "real-repo"
        repo.mkdir()
        init_project(repo, name="real")

        # Manually create a project entry pointing to a nonexistent repo
        fake_dir = initialized_home / "projects" / "fake"
        fake_dir.mkdir(parents=True)
        (fake_dir / "project.yaml").write_text(
            "name: fake\nrepo_path: /nonexistent/path\ntemplate: default\n"
        )

        results = sync_all()
        assert "fake" in results
        assert len(results["fake"].warnings) > 0
