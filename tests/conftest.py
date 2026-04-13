"""Shared fixtures for shipkit tests."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


@pytest.fixture
def tmp_home(tmp_path, monkeypatch):
    """Create a temporary shipkit home directory and point SHIPKIT_HOME to it."""
    home = tmp_path / "shipkit-home"
    home.mkdir()
    monkeypatch.setenv("SHIPKIT_HOME", str(home))

    # Force module-level constant to reload
    import shipkit.config
    monkeypatch.setattr(shipkit.config, "SHIPKIT_HOME", home)
    monkeypatch.setattr(shipkit.config, "CONFIG_PATH", home / "config.yaml")

    import shipkit.datadir
    monkeypatch.setattr(shipkit.datadir, "SHIPKIT_HOME", home)

    return home


@pytest.fixture
def initialized_home(tmp_home):
    """A fully initialized shipkit home directory."""
    from shipkit.datadir import ensure_home
    ensure_home()
    return tmp_home


@pytest.fixture
def tmp_repo(tmp_path):
    """Create a temporary repo directory."""
    repo = tmp_path / "my-project"
    repo.mkdir()
    return repo


@pytest.fixture
def registered_project(initialized_home, tmp_repo):
    """A repo registered as a shipkit project."""
    from shipkit.project import init_project
    init_project(tmp_repo, name="test-project")
    return tmp_repo, "test-project"


@pytest.fixture
def sample_skill(tmp_path):
    """Create a sample skill directory."""
    skill_dir = tmp_path / "skills" / "greet"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Greet\n\nSay hello.\n")
    return skill_dir


@pytest.fixture
def sample_steering(tmp_path):
    """Create a sample steering file."""
    steering_dir = tmp_path / "steering"
    steering_dir.mkdir(parents=True)
    (steering_dir / "my-rule.md").write_text("# My Rule\n\nAlways be polite.\n")
    return steering_dir
