"""Tests for custom agent configuration generation (Claude Code only)."""

from __future__ import annotations

import pytest
import yaml

from shipkit.compilers.agents import (
    generate_claude_agent,
    write_claude_agent,
)
from shipkit.compilers.base import CompileContext


@pytest.fixture
def temp_ctx(tmp_path):
    """Create a temporary compile context."""
    shipkit_home = tmp_path / "shipkit-home"
    repo = tmp_path / "repo"
    shipkit_home.mkdir()
    repo.mkdir()
    (repo / ".git").mkdir()  # Make it a git repo

    return CompileContext(
        shipkit_home=shipkit_home,
        repo_path=repo,
    )


class TestClaudeAgent:
    def test_generates_markdown_with_frontmatter(self, temp_ctx):
        """Test Claude agent generates Markdown with YAML frontmatter."""
        agent = generate_claude_agent(temp_ctx)

        assert isinstance(agent, str)
        assert agent.startswith("---\n")
        assert "name: shipkit" in agent
        assert "description:" in agent

    def test_includes_required_frontmatter_fields(self, temp_ctx):
        """Test Claude agent includes required fields."""
        agent = generate_claude_agent(temp_ctx)

        # Extract frontmatter
        lines = agent.split("\n")
        assert lines[0] == "---"

        # Find closing ---
        end_idx = None
        for i, line in enumerate(lines[1:], 1):
            if line == "---":
                end_idx = i
                break

        assert end_idx is not None

        frontmatter_text = "\n".join(lines[1:end_idx])
        frontmatter = yaml.safe_load(frontmatter_text)

        assert frontmatter["name"] == "shipkit"
        assert "description" in frontmatter
        assert "model" in frontmatter
        assert "tools" in frontmatter

    def test_includes_system_prompt_body(self, temp_ctx):
        """Test Claude agent includes system prompt body."""
        agent = generate_claude_agent(temp_ctx)

        # Should have content after frontmatter
        assert "You are **Shipkit**" in agent
        assert "productivity assistant" in agent.lower()

    def test_includes_claude_specific_instructions(self, temp_ctx):
        """Test Claude agent includes Claude Code specific usage."""
        agent = generate_claude_agent(temp_ctx)

        assert "Claude Code" in agent
        assert "/commit" in agent or "slash command" in agent.lower()

    def test_write_claude_agent_creates_file(self, temp_ctx):
        """Test write_claude_agent creates agent file."""
        agent_file = write_claude_agent(temp_ctx, dry_run=False)

        assert agent_file is not None
        assert agent_file.exists()
        assert agent_file.name == "shipkit.md"
        assert ".claude/agents" in str(agent_file)


class TestDryRun:
    def test_dry_run_returns_path_without_writing(self, temp_ctx):
        """Test dry_run mode doesn't create files."""
        claude_path = write_claude_agent(temp_ctx, dry_run=True)

        # Should return path but not create file
        assert claude_path is not None
        assert not claude_path.exists()
