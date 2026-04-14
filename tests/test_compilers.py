"""Tests for shipkit compilers (Claude Code only)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shipkit.compilers.base import CompileContext, get_compiler


@pytest.fixture
def compile_ctx(initialized_home, tmp_repo):
    """Create a CompileContext for testing."""
    from shipkit.project import init_project
    name = init_project(tmp_repo, name="test-proj")
    return CompileContext(
        home_path=initialized_home,
        repo_path=tmp_repo,
        project_name=name,
    )


class TestCompileContext:

    def test_layer_properties(self, compile_ctx):
        ctx = compile_ctx
        assert ctx.package_guidelines.name == "guidelines"
        assert ctx.user_guidelines == ctx.home_path / "guidelines"

    def test_guidelines_layers_order(self, compile_ctx):
        layers = compile_ctx.guidelines_layers
        assert len(layers) >= 2  # package, user (plugins may be added)
        assert layers[0] == compile_ctx.package_guidelines
        assert layers[1] == compile_ctx.user_guidelines

    def test_plugin_dirs_empty(self, compile_ctx):
        assert compile_ctx.plugin_dirs == []

    def test_plugin_dirs_with_plugins(self, compile_ctx):
        plugins_dir = compile_ctx.home_path / "plugins" / "my-plugin"
        plugins_dir.mkdir(parents=True)
        (plugins_dir / "plugin.yaml").write_text("name: my-plugin\n")
        assert len(compile_ctx.plugin_dirs) == 1

    def test_plugins_in_layer_order(self, compile_ctx):
        plugins_dir = compile_ctx.home_path / "plugins" / "my-plugin"
        plugins_dir.mkdir(parents=True)
        (plugins_dir / "plugin.yaml").write_text("name: my-plugin\n")
        (plugins_dir / "guidelines").mkdir()

        layers = compile_ctx.guidelines_layers
        # package, user, plugins
        assert len(layers) == 3
        assert "plugins" in str(layers[2])


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

    def test_user_guidelines_merged(self, compile_ctx):
        # Add a user guidelines file
        user_guidelines = compile_ctx.home_path / "guidelines"
        (user_guidelines / "custom.md").write_text("# Custom Rule\n\nBe concise.\n")

        compiler = get_compiler("claude")
        compiler.compile(compile_ctx)
        content = (compile_ctx.repo_path / "CLAUDE.md").read_text()
        assert "Be concise" not in content  # Not compiled, discovered at runtime
        assert "Guideline Discovery" in content


