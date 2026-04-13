"""Tests for shipkit.project."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shipkit.project import init_project, resolve_project, list_projects, ProjectError


class TestInitProject:

    def test_creates_marker_and_project_dir(self, initialized_home, tmp_repo):
        name = init_project(tmp_repo)
        marker = tmp_repo / ".shipkit"
        assert marker.exists()
        data = json.loads(marker.read_text())
        assert data["name"] == tmp_repo.name

        project_dir = initialized_home / "projects" / name
        assert project_dir.exists()
        assert (project_dir / "guidelines").is_dir()
        assert (project_dir / "skills").is_dir()
        assert (project_dir / "knowledge").is_dir()
        assert (project_dir / "project.yaml").exists()

    def test_custom_name(self, initialized_home, tmp_repo):
        name = init_project(tmp_repo, name="custom-name")
        assert name == "custom-name"
        assert (initialized_home / "projects" / "custom-name").exists()

    def test_rejects_duplicate_registration(self, initialized_home, tmp_repo):
        init_project(tmp_repo)
        with pytest.raises(ProjectError, match="Already registered"):
            init_project(tmp_repo)

    def test_rejects_duplicate_name(self, initialized_home, tmp_repo, tmp_path):
        init_project(tmp_repo, name="shared-name")
        other_repo = tmp_path / "other-repo"
        other_repo.mkdir()
        with pytest.raises(ProjectError, match="already exists"):
            init_project(other_repo, name="shared-name")

    def test_auto_creates_home(self, tmp_home, tmp_repo):
        """init_project calls ensure_home, so it works even before explicit init."""
        name = init_project(tmp_repo)
        assert (tmp_home / "skills").is_dir()


class TestResolveProject:

    def test_resolves_registered_project(self, registered_project):
        repo, expected_name = registered_project
        name, project_dir = resolve_project(repo)
        assert name == expected_name
        assert project_dir.exists()

    def test_rejects_unregistered_directory(self, initialized_home, tmp_path):
        unregistered = tmp_path / "random-dir"
        unregistered.mkdir()
        with pytest.raises(ProjectError, match="Not a shipkit project"):
            resolve_project(unregistered)


class TestListProjects:

    def test_empty_list(self, initialized_home):
        assert list_projects() == []

    def test_lists_registered_projects(self, initialized_home, tmp_path):
        for i in range(3):
            repo = tmp_path / f"repo-{i}"
            repo.mkdir()
            init_project(repo, name=f"proj-{i}")

        projects = list_projects()
        assert len(projects) == 3
        names = [p["name"] for p in projects]
        assert "proj-0" in names
        assert "proj-1" in names
        assert "proj-2" in names
