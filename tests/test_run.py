"""Tests for shipkit run command (Claude Code only)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from shipkit.cli import main


class TestRunCommand:
    def test_run_checks_claude_installed(self, initialized_home, tmp_repo, monkeypatch):
        """Test run command checks if Claude Code is installed."""
        runner = CliRunner()

        # Change to temp repo directory
        monkeypatch.chdir(tmp_repo)

        # Initialize a project first
        result = runner.invoke(main, ["init", "--skip-alias"])
        assert result.exit_code == 0

        # Mock Claude not being installed
        with patch("shutil.which", return_value=None):
            result = runner.invoke(main, ["run"])

            assert result.exit_code != 0
            assert "Claude Code not found" in result.output

    def test_run_with_agent(self, initialized_home, tmp_repo, monkeypatch):
        """Test run command launches with shipkit agent."""
        runner = CliRunner()

        monkeypatch.chdir(tmp_repo)

        # Initialize a project
        result = runner.invoke(main, ["init", "--skip-alias"])
        assert result.exit_code == 0

        # Mock subprocess.run and shutil.which
        with patch("subprocess.run") as mock_run, \
             patch("shutil.which", return_value="/usr/bin/claude"):

            result = runner.invoke(main, ["run"])

            # Should call claude with shipkit agent
            assert mock_run.called
            call_args = mock_run.call_args[0][0]
            assert "claude" in call_args
            assert "--agent" in call_args
            assert "shipkit" in call_args

    def test_run_without_agent(self, initialized_home, tmp_repo, monkeypatch):
        """Test run command with --no-agent flag."""
        runner = CliRunner()

        monkeypatch.chdir(tmp_repo)

        result = runner.invoke(main, ["init", "--skip-alias"])
        assert result.exit_code == 0

        with patch("subprocess.run") as mock_run, \
             patch("shutil.which", return_value="/usr/bin/claude"):

            result = runner.invoke(main, ["run", "--no-agent"])

            # Should call claude without agent
            assert mock_run.called
            call_args = mock_run.call_args[0][0]
            assert "claude" in call_args
            assert "--agent" not in call_args

    def test_run_with_prompt(self, initialized_home, tmp_repo, monkeypatch):
        """Test run command with initial prompt."""
        runner = CliRunner()

        monkeypatch.chdir(tmp_repo)

        result = runner.invoke(main, ["init", "--skip-alias"])
        assert result.exit_code == 0

        with patch("subprocess.run") as mock_run, \
             patch("shutil.which", return_value="/usr/bin/claude"):

            result = runner.invoke(main, ["run", "test prompt"])

            # Should pass prompt to claude
            assert mock_run.called
            call_args = mock_run.call_args[0][0]
            assert "claude" in call_args
            assert "test prompt" in call_args
