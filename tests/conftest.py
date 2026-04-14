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
    """Create a temporary git repo directory."""
    repo = tmp_path / "my-project"
    repo.mkdir()

    # Initialize as git repo (required by shipkit)
    (repo / ".git").mkdir()

    return repo


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repo with actual git init."""
    repo = tmp_path / "my-project"
    repo.mkdir()

    import subprocess
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)

    return repo


@pytest.fixture
def sample_skill(tmp_path):
    """Create a sample skill directory."""
    skill_dir = tmp_path / "skills" / "greet"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Greet\n\nSay hello.\n")
    return skill_dir


@pytest.fixture
def sample_guidelines(tmp_path):
    """Create a sample guidelines file."""
    guidelines_dir = tmp_path / "guidelines"
    guidelines_dir.mkdir(parents=True)
    (guidelines_dir / "my-rule.md").write_text("# My Rule\n\nAlways be polite.\n")
    return guidelines_dir
