"""Tests for shipkit migrate command."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from shipkit.cli import main
from shipkit.config import ShipkitConfig, SHIPKIT_HOME


@pytest.fixture
def temp_home(monkeypatch, tmp_path):
    """Set up a temporary shipkit home."""
    home = tmp_path / "shipkit_home"
    home.mkdir()

    # Set SHIPKIT_HOME and CONFIG_PATH
    monkeypatch.setenv("SHIPKIT_HOME", str(home))
    monkeypatch.setattr("shipkit.config.SHIPKIT_HOME", home)
    monkeypatch.setattr("shipkit.config.CONFIG_PATH", home / "config.yaml")

    # Create config
    cfg = ShipkitConfig(cli_tool="claude")
    cfg.save()

    return home


@pytest.fixture
def temp_claude_dir(tmp_path):
    """Set up a temporary ~/.claude/ directory with content."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()

    # Create skills
    skills_dir = claude_dir / "skills"
    skills_dir.mkdir()
    (skills_dir / "test-skill").mkdir()
    (skills_dir / "test-skill" / "SKILL.md").write_text("# Test Skill")

    # Create guidelines
    guidelines_dir = claude_dir / "guidelines"
    guidelines_dir.mkdir()
    (guidelines_dir / "test-guideline.md").write_text("# Test Guideline")

    return claude_dir


def test_migrate_dry_run(temp_home, temp_claude_dir, monkeypatch):
    """Test migrate --dry-run shows what would be migrated."""
    # Mock Path.home() to return temp directory
    monkeypatch.setattr(
        "pathlib.Path.home", lambda: temp_claude_dir.parent
    )

    runner = CliRunner()
    result = runner.invoke(main, ["migrate", "--to", "kiro", "--dry-run"])

    assert result.exit_code == 0
    assert "Migration plan: claude → kiro" in result.output
    assert "skills:" in result.output
    assert "(dry-run: no files moved)" in result.output


def test_migrate_same_tool(temp_home):
    """Test migrating to the same tool shows appropriate message."""
    runner = CliRunner()
    result = runner.invoke(main, ["migrate", "--to", "claude"])

    assert result.exit_code == 0
    assert "Already configured for claude" in result.output


def test_migrate_no_content(temp_home, tmp_path, monkeypatch):
    """Test migrating when source directories don't exist."""
    # Mock Path.home() with empty dirs
    empty_home = tmp_path / "empty_home"
    empty_home.mkdir()
    (empty_home / ".claude").mkdir()

    monkeypatch.setattr("pathlib.Path.home", lambda: empty_home)

    runner = CliRunner()
    result = runner.invoke(main, ["migrate", "--to", "kiro", "--dry-run"])

    assert result.exit_code == 0
    assert "No content to migrate" in result.output


def test_migrate_updates_config(temp_home, temp_claude_dir, monkeypatch):
    """Test that migration updates config.yaml."""
    # Mock Path.home()
    monkeypatch.setattr(
        "pathlib.Path.home", lambda: temp_claude_dir.parent
    )

    runner = CliRunner()
    # Use input to confirm migration
    result = runner.invoke(
        main,
        ["migrate", "--to", "kiro"],
        input="y\n"
    )

    assert result.exit_code == 0

    # Check config was updated
    cfg = ShipkitConfig.load()
    assert cfg.cli_tool == "kiro"


def test_migrate_kiro_uses_steering(temp_home, temp_claude_dir, monkeypatch):
    """Test that migrating to Kiro uses 'steering' not 'guidelines'."""
    monkeypatch.setattr(
        "pathlib.Path.home", lambda: temp_claude_dir.parent
    )

    runner = CliRunner()
    result = runner.invoke(main, ["migrate", "--to", "kiro", "--dry-run"])

    assert result.exit_code == 0
    # Should show "steering" for Kiro
    assert "steering:" in result.output or ".kiro/steering" in result.output


def test_migrate_creates_target_dirs(temp_home, temp_claude_dir, monkeypatch):
    """Test that migration creates target directories."""
    monkeypatch.setattr(
        "pathlib.Path.home", lambda: temp_claude_dir.parent
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["migrate", "--to", "gemini"],
        input="y\n"
    )

    assert result.exit_code == 0

    # Check target directories exist
    gemini_dir = temp_claude_dir.parent / ".gemini"
    assert (gemini_dir / "skills").exists()
    assert (gemini_dir / "guidelines").exists()


def test_migrate_merge_existing_content(temp_home, tmp_path, monkeypatch):
    """Test migrating when target already has content (merge scenario)."""
    home = tmp_path / "home"
    home.mkdir()

    # Create source (Claude)
    claude_dir = home / ".claude"
    claude_dir.mkdir()
    (claude_dir / "skills").mkdir()
    (claude_dir / "skills" / "skill-a").mkdir()
    (claude_dir / "skills" / "skill-a" / "SKILL.md").write_text("A")

    # Create target (Kiro) with existing content
    kiro_dir = home / ".kiro"
    kiro_dir.mkdir()
    (kiro_dir / "skills").mkdir()
    (kiro_dir / "skills" / "skill-b").mkdir()
    (kiro_dir / "skills" / "skill-b" / "SKILL.md").write_text("B")

    monkeypatch.setattr("pathlib.Path.home", lambda: home)

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["migrate", "--to", "kiro", "--dry-run"]
    )

    assert result.exit_code == 0
    # Dry run should work even with existing content
    assert "Migration plan" in result.output
