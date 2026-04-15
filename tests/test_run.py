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

        # Mock Claude not being installed
        with patch("shutil.which", return_value=None):
            result = runner.invoke(main, ["run"])

            assert result.exit_code != 0
            assert "Claude Code not found" in result.output

    def test_run_with_agent(self, initialized_home, tmp_repo, monkeypatch):
        """Test run command launches with shipkit agent."""
        runner = CliRunner()

        monkeypatch.chdir(tmp_repo)

        # Mock subprocess.run and shutil.which
        with patch("subprocess.run") as mock_run, \
             patch("shutil.which", return_value="/usr/bin/claude"):

            result = runner.invoke(main, ["run"])

            # Should call claude with shipkit agent
            assert mock_run.called
            call_args = mock_run.call_args[0][0]
            assert "claude" in call_args
            assert "--agent" in call_args
            agent_arg = call_args[call_args.index("--agent") + 1]
            assert agent_arg.startswith("shipkit")

    def test_run_without_agent(self, initialized_home, tmp_repo, monkeypatch):
        """Test run command with --no-agent flag."""
        runner = CliRunner()

        monkeypatch.chdir(tmp_repo)

        with patch("subprocess.run") as mock_run, \
             patch("shutil.which", return_value="/usr/bin/claude"):

            result = runner.invoke(main, ["run", "--no-agent"])

            # Should call claude without agent
            assert mock_run.called
            call_args = mock_run.call_args[0][0]
            assert "claude" in call_args
            assert "--agent" not in call_args

    def test_run_first_time_injects_init_hint(self, initialized_home, tmp_repo, monkeypatch):
        """Test run command injects init hint for uninitialized projects."""
        runner = CliRunner()

        monkeypatch.chdir(tmp_repo)

        # Ensure no agent file exists (first run)
        agent_file = tmp_repo / ".claude" / "agents" / "shipkit.md"
        assert not agent_file.exists()

        with patch("subprocess.run") as mock_run, \
             patch("shutil.which", return_value="/usr/bin/claude"):

            result = runner.invoke(main, ["run"])

            assert mock_run.called
            call_args = mock_run.call_args[0][0]
            # Should include init hint in the prompt
            prompt_arg = call_args[-1]
            assert "/init" in prompt_arg

    def test_run_existing_project_no_hint(self, initialized_home, tmp_repo, monkeypatch):
        """Test run command does NOT inject init hint for already-initialized projects."""
        runner = CliRunner()

        monkeypatch.chdir(tmp_repo)

        # Create the agent file to simulate an initialized project
        agent_dir = tmp_repo / ".claude" / "agents"
        agent_dir.mkdir(parents=True, exist_ok=True)
        (agent_dir / "shipkit.md").write_text("---\nname: shipkit\n---\n")

        with patch("subprocess.run") as mock_run, \
             patch("shutil.which", return_value="/usr/bin/claude"):

            result = runner.invoke(main, ["run"])

            assert mock_run.called
            call_args = mock_run.call_args[0][0]
            # Should NOT include any init hint (just claude + --agent)
            assert len(call_args) == 3  # claude, --agent, "shipkit v..."

    def test_run_with_prompt(self, initialized_home, tmp_repo, monkeypatch):
        """Test run command with initial prompt."""
        runner = CliRunner()

        monkeypatch.chdir(tmp_repo)

        # Create agent file so we test prompt passthrough without init hint
        agent_dir = tmp_repo / ".claude" / "agents"
        agent_dir.mkdir(parents=True, exist_ok=True)
        (agent_dir / "shipkit.md").write_text("---\nname: shipkit\n---\n")

        with patch("subprocess.run") as mock_run, \
             patch("shutil.which", return_value="/usr/bin/claude"):

            result = runner.invoke(main, ["run", "test prompt"])

            # Should pass prompt to claude
            assert mock_run.called
            call_args = mock_run.call_args[0][0]
            assert "claude" in call_args
            assert "test prompt" in call_args
