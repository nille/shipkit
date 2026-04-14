"""Tests for pre-commit safety hook."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def git_repo(tmp_path):
    """Create a git repo for testing."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
    return repo


@pytest.fixture
def hook_script():
    """Get path to the pre_commit_safety.py script."""
    return Path(__file__).parent.parent / "shipkit" / "core" / "hooks" / "pre_commit_safety.py"


class TestSecretDetection:

    def test_detects_aws_access_key(self, git_repo, hook_script):
        """Test detection of AWS access keys."""
        # Create file with AWS key
        test_file = git_repo / "config.py"
        test_file.write_text("AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'\n")

        # Stage the file
        subprocess.run(["git", "add", "config.py"], cwd=git_repo, check=True)

        # Run hook with commit event
        event = {
            "tool": "Skill",
            "parameters": {"skill": "commit"}
        }

        result = subprocess.run(
            ["python3", str(hook_script)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            cwd=git_repo,
        )

        # Should block (exit 1) and output warning
        assert result.returncode == 1
        assert "AWS access key" in result.stdout
        assert "config.py" in result.stdout

    def test_detects_api_tokens(self, git_repo, hook_script):
        """Test detection of API tokens."""
        test_file = git_repo / "settings.ts"
        test_file.write_text('const API_KEY = "sk-proj-1234567890abcdefghij";\n')

        subprocess.run(["git", "add", "settings.ts"], cwd=git_repo, check=True)

        event = {"tool": "Skill", "parameters": {"skill": "commit"}}
        result = subprocess.run(
            ["python3", str(hook_script)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            cwd=git_repo,
        )

        assert result.returncode == 1
        assert "api key" in result.stdout.lower() or "token" in result.stdout.lower()

    def test_detects_github_pat(self, git_repo, hook_script):
        """Test detection of GitHub personal access tokens."""
        test_file = git_repo / "auth.py"
        test_file.write_text('GITHUB_TOKEN = "ghp_12345678901234567890123456789012abcd"\n')

        subprocess.run(["git", "add", "auth.py"], cwd=git_repo, check=True)

        event = {"tool": "Bash", "parameters": {"command": "git commit -m 'test'"}}
        result = subprocess.run(
            ["python3", str(hook_script)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            cwd=git_repo,
        )

        assert result.returncode == 1
        assert "github" in result.stdout.lower() or "token" in result.stdout.lower()


class TestDebugDetection:

    def test_detects_console_log(self, git_repo, hook_script):
        """Test detection of console.log() statements."""
        test_file = git_repo / "app.ts"
        test_file.write_text('console.log("debug info");\nconst x = 1;\n')

        subprocess.run(["git", "add", "app.ts"], cwd=git_repo, check=True)

        event = {"tool": "Skill", "parameters": {"skill": "commit"}}
        result = subprocess.run(
            ["python3", str(hook_script)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            cwd=git_repo,
        )

        assert result.returncode == 1
        assert "console.log" in result.stdout
        assert "app.ts" in result.stdout

    def test_detects_debugger_statement(self, git_repo, hook_script):
        """Test detection of debugger statements."""
        test_file = git_repo / "handler.js"
        test_file.write_text('function test() {\n  debugger;\n  return 42;\n}\n')

        subprocess.run(["git", "add", "handler.js"], cwd=git_repo, check=True)

        event = {"tool": "Bash", "parameters": {"command": "git commit -m 'test'"}}
        result = subprocess.run(
            ["python3", str(hook_script)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            cwd=git_repo,
        )

        assert result.returncode == 1
        assert "debugger" in result.stdout

    def test_detects_python_print(self, git_repo, hook_script):
        """Test detection of print() statements in Python."""
        test_file = git_repo / "app.py"
        test_file.write_text('def foo():\n    print("debug")\n    return 1\n')

        subprocess.run(["git", "add", "app.py"], cwd=git_repo, check=True)

        event = {"tool": "Skill", "parameters": {"skill": "commit"}}
        result = subprocess.run(
            ["python3", str(hook_script)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            cwd=git_repo,
        )

        assert result.returncode == 1
        assert "print()" in result.stdout


class TestMistakeDetection:

    def test_detects_merge_conflicts(self, git_repo, hook_script):
        """Test detection of merge conflict markers."""
        test_file = git_repo / "code.py"
        test_file.write_text('def foo():\n<<<<<<< HEAD\n    return 1\n=======\n    return 2\n>>>>>>> branch\n')

        subprocess.run(["git", "add", "code.py"], cwd=git_repo, check=True)

        event = {"tool": "Skill", "parameters": {"skill": "commit"}}
        result = subprocess.run(
            ["python3", str(hook_script)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            cwd=git_repo,
        )

        assert result.returncode == 1
        assert "Merge conflict" in result.stdout

    def test_warns_about_todos(self, git_repo, hook_script):
        """Test that TODO comments generate warnings (not block)."""
        test_file = git_repo / "code.py"
        test_file.write_text('def foo():\n    # TODO: implement this\n    pass\n')

        subprocess.run(["git", "add", "code.py"], cwd=git_repo, check=True)

        event = {"tool": "Skill", "parameters": {"skill": "commit"}}
        result = subprocess.run(
            ["python3", str(hook_script)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            cwd=git_repo,
        )

        # Should not block (exit 0), but should output warning
        assert result.returncode == 0
        assert "TODO" in result.stdout or "WARNING" in result.stdout


class TestDangerousFiles:

    def test_blocks_env_file(self, git_repo, hook_script):
        """Test that .env files are blocked."""
        test_file = git_repo / ".env"
        test_file.write_text("API_KEY=secret123\n")

        # Force add even if in gitignore
        subprocess.run(["git", "add", "-f", ".env"], cwd=git_repo, check=True)

        event = {"tool": "Skill", "parameters": {"skill": "commit"}}
        result = subprocess.run(
            ["python3", str(hook_script)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            cwd=git_repo,
        )

        assert result.returncode == 1
        assert ".env" in result.stdout
        assert "should not be committed" in result.stdout.lower() or "dangerous file" in result.stdout.lower()


class TestCleanCommit:

    def test_allows_clean_commit(self, git_repo, hook_script):
        """Test that clean files pass without issues."""
        test_file = git_repo / "app.py"
        test_file.write_text('def add(a, b):\n    """Add two numbers."""\n    return a + b\n')

        subprocess.run(["git", "add", "app.py"], cwd=git_repo, check=True)

        event = {"tool": "Skill", "parameters": {"skill": "commit"}}
        result = subprocess.run(
            ["python3", str(hook_script)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            cwd=git_repo,
        )

        # Should allow (exit 0)
        assert result.returncode == 0
        # Should not output warnings
        assert "⚠️" not in result.stdout


class TestSkipNonCommitActions:

    def test_skips_non_commit_actions(self, git_repo, hook_script):
        """Test that hook only runs for commit actions."""
        test_file = git_repo / "app.py"
        test_file.write_text('console.log("test");\n')  # Would normally be flagged

        subprocess.run(["git", "add", "app.py"], cwd=git_repo, check=True)

        # Event for a different tool (not commit)
        event = {"tool": "Read", "parameters": {"file_path": "app.py"}}
        result = subprocess.run(
            ["python3", str(hook_script)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            cwd=git_repo,
        )

        # Should not scan (exit 0, no output)
        assert result.returncode == 0
        assert not result.stdout.strip()


class TestLLMVerification:

    def test_llm_disabled_uses_regex_only(self, git_repo, hook_script, monkeypatch):
        """Test that LLM can be disabled with SHIPKIT_NO_LLM=1."""
        # Disable LLM
        monkeypatch.setenv("SHIPKIT_NO_LLM", "1")

        test_file = git_repo / "test_fixture.py"
        test_file.write_text('TEST_AWS_KEY = "AKIAIOSFODNN7EXAMPLE"  # Test fixture\n')

        subprocess.run(["git", "add", "test_fixture.py"], cwd=git_repo, check=True)

        event = {"tool": "Skill", "parameters": {"skill": "commit"}}
        result = subprocess.run(
            ["python3", str(hook_script)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            cwd=git_repo,
        )

        # Without LLM, regex catches this (even though it's a test fixture)
        assert result.returncode == 1
        assert "AWS" in result.stdout

    def test_llm_fallback_on_api_error(self, git_repo, hook_script, monkeypatch):
        """Test that hook falls back to regex if LLM fails."""
        # Set invalid API key (will cause LLM to fail)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "invalid-key")

        test_file = git_repo / "app.py"
        test_file.write_text('api_key = "sk-proj-1234567890abcdefghijklmnop"\n')

        subprocess.run(["git", "add", "app.py"], cwd=git_repo, check=True)

        event = {"tool": "Skill", "parameters": {"skill": "commit"}}
        result = subprocess.run(
            ["python3", str(hook_script)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            cwd=git_repo,
        )

        # Should still block (fallback to regex findings)
        assert result.returncode == 1
        assert "key" in result.stdout.lower() or "token" in result.stdout.lower()
