"""Tests for shipkit run command with agent support."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from shipkit.cli import main, _detect_installed_tool, _build_launch_command


class TestDetectInstalledTool:
    def test_detects_claude(self):
        """Test detection when Claude Code is installed."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: "/usr/bin/claude" if x == "claude" else None
            tool = _detect_installed_tool()
            assert tool == "claude"

    def test_detects_kiro(self):
        """Test detection when Kiro is installed."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: "/usr/bin/kiro-cli" if x == "kiro-cli" else None
            tool = _detect_installed_tool()
            assert tool == "kiro"

    def test_detects_opencode(self):
        """Test detection when OpenCode is installed."""
        with patch("shutil.which") as mock_which:
            def which_side_effect(cmd):
                if cmd == "opencode":
                    return "/usr/bin/opencode"
                return None
            mock_which.side_effect = which_side_effect
            tool = _detect_installed_tool()
            assert tool == "opencode"

    def test_detects_gemini(self):
        """Test detection when Gemini CLI is installed."""
        with patch("shutil.which") as mock_which:
            def which_side_effect(cmd):
                if cmd == "gemini":
                    return "/usr/bin/gemini"
                return None
            mock_which.side_effect = which_side_effect
            tool = _detect_installed_tool()
            assert tool == "gemini"

    def test_returns_none_when_no_tool(self):
        """Test detection when no tool is installed."""
        with patch("shutil.which", return_value=None):
            tool = _detect_installed_tool()
            assert tool is None

    def test_prefers_claude_when_multiple(self):
        """Test Claude is preferred when multiple tools installed."""
        with patch("shutil.which") as mock_which:
            # All tools available
            mock_which.return_value = "/usr/bin/tool"
            tool = _detect_installed_tool()
            assert tool == "claude"


class TestBuildLaunchCommand:
    def test_claude_with_agent(self):
        """Test Claude Code launch command with agent."""
        cmd = _build_launch_command("claude", (), use_agent=True)
        assert cmd == ["claude", "--agent", "shipkit"]

    def test_claude_without_agent(self):
        """Test Claude Code launch command without agent."""
        cmd = _build_launch_command("claude", (), use_agent=False)
        assert cmd == ["claude"]

    def test_claude_with_prompt(self):
        """Test Claude Code with prompt."""
        cmd = _build_launch_command("claude", ("hello", "world"), use_agent=True)
        assert cmd == ["claude", "--agent", "shipkit", "hello world"]

    def test_kiro_with_agent(self):
        """Test Kiro launch command with agent."""
        cmd = _build_launch_command("kiro", (), use_agent=True)
        assert cmd == ["kiro-cli", "chat", "--agent", "shipkit"]

    def test_kiro_with_prompt(self):
        """Test Kiro with prompt."""
        cmd = _build_launch_command("kiro", ("test", "prompt"), use_agent=True)
        assert cmd == ["kiro-cli", "chat", "--agent", "shipkit", "test prompt"]

    def test_opencode_with_agent(self):
        """Test OpenCode launch command with agent."""
        cmd = _build_launch_command("opencode", (), use_agent=True)
        assert cmd == ["opencode", "--agent", "shipkit"]

    def test_opencode_with_prompt(self):
        """Test OpenCode with prompt (uses --prompt flag)."""
        cmd = _build_launch_command("opencode", ("test",), use_agent=True)
        assert cmd == ["opencode", "--agent", "shipkit", "--prompt", "test"]

    def test_gemini_no_agent_flag(self):
        """Test Gemini CLI has no agent flag (reads GEMINI.md)."""
        cmd = _build_launch_command("gemini", (), use_agent=True)
        assert cmd == ["gemini"]
        # Agent flag not added for Gemini (no support)

    def test_gemini_with_prompt(self):
        """Test Gemini with prompt."""
        cmd = _build_launch_command("gemini", ("prompt",), use_agent=True)
        assert cmd == ["gemini", "-p", "prompt"]

    def test_unknown_tool_raises(self):
        """Test unknown tool raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            _build_launch_command("unknown", (), use_agent=True)


class TestRunCommand:
    def test_run_with_no_agent_flag(self, tmp_home, tmp_repo, monkeypatch):
        """Test run command with --no-agent flag."""
        from shipkit.project import init_project
        import os

        init_project(tmp_repo, name="test-run")

        # Change to repo directory so sync_project works
        original_cwd = os.getcwd()
        os.chdir(tmp_repo)

        try:
            runner = CliRunner()

            # Mock subprocess.run globally
            with patch("subprocess.run") as mock_subprocess:
                result = runner.invoke(main, ["run", "--no-agent"])

                assert result.exit_code == 0, f"Command failed: {result.output}"

                # Should launch without --agent flag
                mock_subprocess.assert_called_once()
                call_args = mock_subprocess.call_args[0][0]
                assert "claude" in call_args
                assert "--agent" not in call_args
        finally:
            os.chdir(original_cwd)

    def test_run_defaults_to_agent(self, tmp_home, tmp_repo, monkeypatch):
        """Test run command uses agent by default."""
        from shipkit.project import init_project
        import os

        init_project(tmp_repo, name="test-run-agent")

        # Change to repo directory
        original_cwd = os.getcwd()
        os.chdir(tmp_repo)

        try:
            runner = CliRunner()

            with patch("subprocess.run") as mock_subprocess:
                result = runner.invoke(main, ["run"])

                assert result.exit_code == 0, f"Command failed: {result.output}"

                # Should launch WITH --agent flag by default
                mock_subprocess.assert_called_once()
                call_args = mock_subprocess.call_args[0][0]
                assert "--agent" in call_args
                assert "shipkit" in call_args
        finally:
            os.chdir(original_cwd)
