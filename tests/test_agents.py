"""Tests for custom agent configuration generation."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from shipkit.compilers.agents import (
    generate_kiro_agent,
    generate_claude_agent,
    generate_opencode_agent,
    generate_gemini_context_header,
    write_kiro_agent,
    write_claude_agent,
    write_opencode_agent,
)
from shipkit.compilers.base import CompileContext


@pytest.fixture
def temp_ctx(tmp_path):
    """Create a temporary compile context."""
    home = tmp_path / "home"
    repo = tmp_path / "repo"
    home.mkdir()
    repo.mkdir()

    return CompileContext(
        home_path=home,
        repo_path=repo,
        project_name="test-project"
    )


class TestKiroAgent:
    def test_generates_valid_json(self, temp_ctx):
        """Test Kiro agent generates valid JSON."""
        agent = generate_kiro_agent(temp_ctx)

        assert isinstance(agent, dict)
        assert agent["name"] == "shipkit"
        assert agent["description"]
        assert agent["prompt"]
        assert "model" in agent

    def test_includes_schema_url(self, temp_ctx):
        """Test Kiro agent includes schema URL."""
        agent = generate_kiro_agent(temp_ctx)

        assert "$schema" in agent
        assert "agent-v1.json" in agent["$schema"]

    def test_includes_resources_array(self, temp_ctx):
        """Test Kiro agent includes resources for auto-loading."""
        agent = generate_kiro_agent(temp_ctx)

        assert "resources" in agent
        assert isinstance(agent["resources"], list)
        assert len(agent["resources"]) > 0

        # Should reference skills and guidelines
        resources_str = " ".join(agent["resources"])
        assert "skill://" in resources_str
        assert "file://" in resources_str
        assert ".kiro/skills" in resources_str
        assert ".kiro/steering" in resources_str  # Kiro uses "steering"

    def test_includes_allowed_tools(self, temp_ctx):
        """Test Kiro agent has sensible tool allowlist."""
        agent = generate_kiro_agent(temp_ctx)

        assert "allowedTools" in agent
        assert "read" in agent["allowedTools"]
        assert "write" in agent["allowedTools"]
        assert "shell" in agent["allowedTools"]

    def test_write_kiro_agent_creates_file(self, temp_ctx):
        """Test write_kiro_agent creates agent file."""
        agent_file = write_kiro_agent(temp_ctx, dry_run=False)

        assert agent_file is not None
        assert agent_file.exists()
        assert agent_file.name == "shipkit.json"
        assert ".kiro/agents" in str(agent_file)

        # Verify JSON is valid
        content = json.loads(agent_file.read_text())
        assert content["name"] == "shipkit"


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


class TestOpenCodeAgent:
    def test_generates_markdown_with_frontmatter(self, temp_ctx):
        """Test OpenCode agent generates Markdown with YAML frontmatter."""
        agent = generate_opencode_agent(temp_ctx)

        assert isinstance(agent, str)
        assert agent.startswith("---\n")
        assert "name: shipkit" in agent

    def test_includes_opencode_specific_fields(self, temp_ctx):
        """Test OpenCode agent includes mode and permission fields."""
        agent = generate_opencode_agent(temp_ctx)

        # Extract frontmatter
        lines = agent.split("\n")
        end_idx = lines.index("---", 1)
        frontmatter_text = "\n".join(lines[1:end_idx])
        frontmatter = yaml.safe_load(frontmatter_text)

        assert frontmatter["mode"] == "primary"
        assert "permission" in frontmatter
        assert "edit" in frontmatter["permission"]
        assert "bash" in frontmatter["permission"]

    def test_includes_color(self, temp_ctx):
        """Test OpenCode agent includes color customization."""
        agent = generate_opencode_agent(temp_ctx)

        assert "color:" in agent

    def test_write_opencode_agent_creates_file(self, temp_ctx):
        """Test write_opencode_agent creates agent file."""
        agent_file = write_opencode_agent(temp_ctx, dry_run=False)

        assert agent_file is not None
        assert agent_file.exists()
        assert agent_file.name == "shipkit.md"
        assert ".opencode/agents" in str(agent_file)


class TestGeminiContextHeader:
    def test_generates_markdown_header(self, temp_ctx):
        """Test Gemini context header generates markdown."""
        header = generate_gemini_context_header(temp_ctx)

        assert isinstance(header, str)
        assert "# Shipkit Agent Configuration" in header
        assert "You are **Shipkit**" in header

    def test_includes_identity_instruction(self, temp_ctx):
        """Test Gemini header instructs identity as Shipkit."""
        header = generate_gemini_context_header(temp_ctx)

        # Since Gemini doesn't have agent branding, we need explicit identity
        assert "You are \"Shipkit\"" in header or "You are **Shipkit**" in header

    def test_includes_gemini_specific_instructions(self, temp_ctx):
        """Test Gemini header includes Gemini CLI specific content."""
        header = generate_gemini_context_header(temp_ctx)

        assert "Gemini CLI" in header


class TestSystemPrompts:
    def test_all_agents_have_shipkit_branding(self, temp_ctx):
        """Test all agent types identify as Shipkit."""
        kiro = generate_kiro_agent(temp_ctx)
        claude = generate_claude_agent(temp_ctx)
        opencode = generate_opencode_agent(temp_ctx)
        gemini = generate_gemini_context_header(temp_ctx)

        # All should mention Shipkit
        assert "Shipkit" in kiro["prompt"]
        assert "Shipkit" in claude
        assert "Shipkit" in opencode
        assert "Shipkit" in gemini

    def test_all_agents_explain_skills(self, temp_ctx):
        """Test all agent types explain how skills work."""
        kiro = generate_kiro_agent(temp_ctx)
        claude = generate_claude_agent(temp_ctx)
        opencode = generate_opencode_agent(temp_ctx)
        gemini = generate_gemini_context_header(temp_ctx)

        # All should explain skills
        for content in [kiro["prompt"], claude, opencode, gemini]:
            assert "skill" in content.lower()

    def test_all_agents_mention_team_collaboration(self, temp_ctx):
        """Test all agents mention team collaboration aspect."""
        kiro = generate_kiro_agent(temp_ctx)
        claude = generate_claude_agent(temp_ctx)
        opencode = generate_opencode_agent(temp_ctx)
        gemini = generate_gemini_context_header(temp_ctx)

        # All should mention team or collaboration
        for content in [kiro["prompt"], claude, opencode, gemini]:
            assert "team" in content.lower() or "collaboration" in content.lower()


class TestDryRun:
    def test_dry_run_returns_path_without_writing(self, temp_ctx):
        """Test dry_run mode doesn't create files."""
        kiro_path = write_kiro_agent(temp_ctx, dry_run=True)
        claude_path = write_claude_agent(temp_ctx, dry_run=True)
        opencode_path = write_opencode_agent(temp_ctx, dry_run=True)

        # Should return paths but not create files
        assert kiro_path is not None
        assert claude_path is not None
        assert opencode_path is not None

        assert not kiro_path.exists()
        assert not claude_path.exists()
        assert not opencode_path.exists()
