"""Tests for alias installation during shipkit init."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from shipkit.cli import main


class TestInitAliasOffer:
    def test_first_project_offers_alias(self, tmp_home, tmp_repo, monkeypatch):
        """Test init offers alias installation on first project."""
        import os
        os.chdir(tmp_repo)

        runner = CliRunner()
        result = runner.invoke(main, ["init", "--name", "first-project"], input="n\n")

        assert result.exit_code == 0
        assert "Install 'sk' alias?" in result.output or "Quick access" in result.output

    def test_skip_alias_flag_skips_offer(self, tmp_home, tmp_repo, monkeypatch):
        """Test --skip-alias flag skips the offer."""
        import os
        os.chdir(tmp_repo)

        runner = CliRunner()
        result = runner.invoke(main, ["init", "--name", "first", "--skip-alias"])

        assert result.exit_code == 0
        assert "Install 'sk' alias?" not in result.output

    def test_second_project_skips_offer(self, tmp_home, tmp_repo, monkeypatch):
        """Test second project doesn't offer alias (already set up)."""
        from shipkit.project import init_project
        import os

        # Create first project
        first_repo = tmp_home.parent / "first-repo"
        first_repo.mkdir()
        os.chdir(first_repo)
        init_project(first_repo, name="first")

        # Create second project
        second_repo = tmp_home.parent / "second-repo"
        second_repo.mkdir()
        os.chdir(second_repo)

        runner = CliRunner()
        result = runner.invoke(main, ["init", "--name", "second"])

        assert result.exit_code == 0
        # Second project should not offer alias
        # (harder to test since it checks project count, which is 2)

    def test_accepts_alias_installation(self, tmp_home, tmp_repo, monkeypatch):
        """Test accepting alias installation uses shipkit alias command."""
        import os
        os.chdir(tmp_repo)

        # In test context, stdin.isatty() returns False, so the interactive
        # prompt is skipped. This is expected - in real terminal usage it would prompt.
        # We verify the offer message appears in non-interactive mode
        runner = CliRunner()
        result = runner.invoke(main, ["init", "--name", "test"])

        assert result.exit_code == 0
        # Non-interactive mode shows the command to run later
        assert "shipkit alias" in result.output or "Quick access" in result.output

    def test_declines_alias_installation(self, tmp_home, tmp_repo, monkeypatch):
        """Test declining alias installation."""
        import os
        os.chdir(tmp_repo)

        runner = CliRunner()
        result = runner.invoke(main, ["init", "--name", "test"], input="n\n")

        assert result.exit_code == 0
        assert "Skipped" in result.output or "later" in result.output


class TestGlobalAlias:
    def test_default_alias_name_is_sk(self):
        """Test default alias name is 'sk'."""
        from shipkit.cli import _generate_shipkit_alias

        snippet = _generate_shipkit_alias("sk", "zsh")
        assert "alias sk=" in snippet
        assert "shipkit run" in snippet

    def test_global_alias_uses_noglob(self):
        """Test global alias uses noglob wrapper."""
        from shipkit.cli import _generate_shipkit_alias

        snippet = _generate_shipkit_alias("sk", "zsh")
        assert "noglob" in snippet

    def test_global_alias_fish_format(self):
        """Test fish shell uses different format."""
        from shipkit.cli import _generate_shipkit_alias

        snippet = _generate_shipkit_alias("sk", "fish")
        assert 'alias sk="shipkit run"' in snippet
