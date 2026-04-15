"""Tests for shipkit compilers (Claude Code only)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shipkit.compilers.base import CompileContext, get_compiler


@pytest.fixture
def compile_ctx(initialized_home, tmp_repo):
    """Create a CompileContext for testing."""
    return CompileContext(
        shipkit_home=initialized_home,
        repo_path=tmp_repo,
    )


class TestCompileContext:

    def test_layer_properties(self, compile_ctx):
        ctx = compile_ctx
        assert ctx.package_core_guidelines.name == "guidelines"
        assert "core" in str(ctx.package_core_guidelines)
        # User guidelines point to ~/.claude/ now
        assert ".claude" in str(ctx.user_guidelines)

    def test_guidelines_layers_order(self, compile_ctx):
        """Test guidelines layers in precedence order (lowest first)."""
        ctx = compile_ctx
        layers = ctx.guidelines_layers
        # core → user → team (experimental/advanced disabled by default)
        assert len(layers) >= 3
        assert ctx.package_core_guidelines in layers
        assert ctx.user_guidelines in layers
        assert ctx.team_guidelines in layers

    def test_plugin_dirs_empty(self, compile_ctx):
        assert compile_ctx.plugin_dirs == []

    def test_plugin_dirs_with_plugins(self, compile_ctx):
        plugins_dir = compile_ctx.shipkit_home / "plugins" / "my-plugin"
        plugins_dir.mkdir(parents=True)
        (plugins_dir / "plugin.yaml").write_text("name: my-plugin\n")
        assert len(compile_ctx.plugin_dirs) == 1

    def test_plugins_in_layer_order(self, compile_ctx):
        """Test plugins appear in layer order between package and user."""
        plugins_dir = compile_ctx.shipkit_home / "plugins" / "my-plugin"
        plugins_dir.mkdir(parents=True)
        (plugins_dir / "plugin.yaml").write_text("name: my-plugin\n")
        (plugins_dir / "guidelines").mkdir()

        layers = compile_ctx.guidelines_layers
        # core → [experimental] → [advanced] → plugins → user → team
        assert "plugins" in str(layers)


    def test_mcp_layers_includes_project(self, compile_ctx):
        """Test MCP layers include project-level path as highest precedence."""
        ctx = compile_ctx
        layers = ctx.mcp_layers
        # Last layer should be the project-level MCP (highest precedence)
        assert layers[-1] == ctx.team_mcp
        assert str(ctx.repo_path / ".claude" / "mcp.json") == str(layers[-1])

    def test_team_mcp_property(self, compile_ctx):
        """Test team_mcp points to .claude/mcp.json in project."""
        ctx = compile_ctx
        expected = ctx.repo_path / ".claude" / "mcp.json"
        assert ctx.team_mcp == expected


class TestGetCompiler:

    def test_get_claude_compiler(self):
        compiler = get_compiler("claude")
        assert compiler.name == "Claude Code"

    def test_unknown_compiler(self):
        with pytest.raises(ValueError, match="No compiler for 'nonexistent'"):
            get_compiler("nonexistent")


class TestClaudeCompiler:

    def test_generates_claude_md(self, compile_ctx):
        compiler = get_compiler("claude")
        result = compiler.compile(compile_ctx)
        claude_md = compile_ctx.repo_path / "CLAUDE.md"
        assert claude_md.exists()
        content = claude_md.read_text()
        assert "SHIPKIT:BEGIN" in content
        assert "SHIPKIT:END" in content
        assert "CLAUDE.md" in result.files_written

    def test_preserves_user_content(self, compile_ctx):
        claude_md = compile_ctx.repo_path / "CLAUDE.md"
        claude_md.write_text("My custom notes\n")
        compiler = get_compiler("claude")
        compiler.compile(compile_ctx)
        content = claude_md.read_text()
        assert "My custom notes" in content
        assert "SHIPKIT:BEGIN" in content

    def test_preserves_existing_user_content_below_sentinel(self, compile_ctx):
        claude_md = compile_ctx.repo_path / "CLAUDE.md"
        claude_md.write_text(
            "<!-- SHIPKIT:BEGIN — managed by shipkit, do not edit above SHIPKIT:END -->\n"
            "old managed\n"
            "<!-- SHIPKIT:END -->\n"
            "\nMy custom notes\n"
        )
        compiler = get_compiler("claude")
        compiler.compile(compile_ctx)
        content = claude_md.read_text()
        assert "My custom notes" in content
        assert "old managed" not in content  # replaced

    def test_discovery_instructions_in_claude_md(self, compile_ctx):
        """CLAUDE.md contains discovery instructions (not compiled skill catalog)."""
        compiler = get_compiler("claude")
        compiler.compile(compile_ctx)
        content = (compile_ctx.repo_path / "CLAUDE.md").read_text()
        assert "Skill Discovery" in content
        assert "Guideline Discovery" in content

    def test_skills_not_compiled_uses_discovery(self, compile_ctx):
        """Skills are NOT compiled - discovered at runtime via guideline."""
        compiler = get_compiler("claude")
        result = compiler.compile(compile_ctx)
        # Skills should NOT be written to .claude/commands/
        assert not any("commands/" in f for f in result.files_written)
        # Discovery guideline should be in CLAUDE.md
        content = (compile_ctx.repo_path / "CLAUDE.md").read_text()
        assert "Skill Discovery" in content

    def test_generates_mcp_json(self, compile_ctx):
        compiler = get_compiler("claude")
        result = compiler.compile(compile_ctx)
        mcp_path = compile_ctx.repo_path / ".mcp.json"
        if mcp_path.exists():
            data = json.loads(mcp_path.read_text())
            assert "mcpServers" in data

    def test_dry_run_no_writes(self, compile_ctx):
        compiler = get_compiler("claude")
        result = compiler.compile(compile_ctx, dry_run=True)
        assert not (compile_ctx.repo_path / "CLAUDE.md").exists()
        assert all("dry-run" in f for f in result.files_written)

    def test_user_guidelines_merged(self, compile_ctx, monkeypatch):
        # Add a user guideline file (in Claude Code native location)
        # Need to mock CLAUDE_HOME for test
        test_claude_home = compile_ctx.shipkit_home.parent / ".claude"
        test_claude_home.mkdir(parents=True, exist_ok=True)

        import shipkit.config
        import shipkit.compilers.base
        monkeypatch.setattr(shipkit.config, "CLAUDE_HOME", test_claude_home)
        monkeypatch.setattr(shipkit.compilers.base, "CLAUDE_HOME", test_claude_home)

        # Create user guidelines
        user_guidelines = test_claude_home / "guidelines"
        user_guidelines.mkdir(parents=True)
        (user_guidelines / "custom.md").write_text("# Custom Rule\n\nBe concise.\n")

        compiler = get_compiler("claude")
        compiler.compile(compile_ctx)
        content = (compile_ctx.repo_path / "CLAUDE.md").read_text()
        assert "Be concise" not in content  # Not compiled, discovered at runtime
        assert "Guideline Discovery" in content


