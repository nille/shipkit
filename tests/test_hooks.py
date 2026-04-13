"""Tests for shipkit hook library modules."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


class TestHookConfig:

    def test_resolve_home_path(self, initialized_home, monkeypatch):
        monkeypatch.setenv("SHIPKIT_HOME", str(initialized_home))

        # Import fresh — the hook lib uses its own resolution
        from shipkit.content.hooks.lib.config import resolve_home_path
        result = resolve_home_path()
        assert result == initialized_home

    def test_resolve_home_path_missing(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SHIPKIT_HOME", str(tmp_path / "nonexistent"))
        from shipkit.content.hooks.lib.config import resolve_home_path
        result = resolve_home_path()
        assert result is None

    def test_resolve_project_name(self, tmp_path):
        marker = tmp_path / ".shipkit"
        marker.write_text(json.dumps({"name": "my-project"}))

        from shipkit.content.hooks.lib.config import resolve_project_name
        result = resolve_project_name(tmp_path)
        assert result == "my-project"

    def test_resolve_project_name_missing(self, tmp_path):
        from shipkit.content.hooks.lib.config import resolve_project_name
        result = resolve_project_name(tmp_path)
        assert result is None

    def test_is_hook_session(self, monkeypatch):
        from shipkit.content.hooks.lib.config import is_hook_session
        assert not is_hook_session()
        monkeypatch.setenv("SHIPKIT_HOOK_SESSION", "1")
        assert is_hook_session()


class TestTranscript:

    @pytest.fixture
    def jsonl_transcript(self, tmp_path):
        """Create a sample JSONL transcript file."""
        transcript = tmp_path / "transcript.jsonl"
        lines = [
            {"type": "message", "message": {"role": "user", "content": "Hello"}},
            {"type": "message", "message": {"role": "assistant", "content": "Hi there!"}},
            {"type": "message", "message": {"role": "user", "content": "Fix the bug"}},
            {"type": "message", "message": {"role": "assistant", "content": "I'll fix it now."}},
            {"type": "message", "message": {"role": "user", "content": "Thanks"}},
            {"type": "message", "message": {"role": "assistant", "content": "Done!"}},
        ]
        transcript.write_text("\n".join(json.dumps(l) for l in lines) + "\n")
        return transcript

    def test_extract_turns(self, jsonl_transcript):
        from shipkit.content.hooks.lib.transcript import extract_turns
        turns = extract_turns(jsonl_transcript)
        assert len(turns) == 6
        assert turns[0]["role"] == "user"
        assert turns[0]["content"] == "Hello"

    def test_count_user_turns(self, jsonl_transcript):
        from shipkit.content.hooks.lib.transcript import extract_turns, count_user_turns
        turns = extract_turns(jsonl_transcript)
        assert count_user_turns(turns) == 3

    def test_generate_title(self, jsonl_transcript):
        from shipkit.content.hooks.lib.transcript import extract_turns, generate_title
        turns = extract_turns(jsonl_transcript)
        title = generate_title(turns)
        assert isinstance(title, str)
        assert len(title) > 0

    def test_build_summary(self, jsonl_transcript):
        from shipkit.content.hooks.lib.transcript import extract_turns, build_summary
        turns = extract_turns(jsonl_transcript)
        summary = build_summary(turns)
        assert "[user]" in summary
        assert "[assistant]" in summary

    def test_extract_turns_missing_file(self, tmp_path):
        from shipkit.content.hooks.lib.transcript import extract_turns
        turns = extract_turns(tmp_path / "nonexistent.jsonl")
        assert turns == []


class TestSessionContext:

    def test_format_session_context_empty(self, initialized_home, monkeypatch):
        monkeypatch.setenv("SHIPKIT_HOME", str(initialized_home))
        from shipkit.content.hooks.lib.session_context import format_session_context
        result = format_session_context()
        assert result == ""

    def test_format_session_context_with_sessions(self, initialized_home, monkeypatch):
        monkeypatch.setenv("SHIPKIT_HOME", str(initialized_home))
        sessions_dir = initialized_home / ".state" / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)

        session_data = {
            "session_id": "abc123",
            "timestamp": "2026-04-12T10:00:00Z",
            "title": "Fix auth bug",
            "summary": "Fixed the auth middleware token refresh issue",
            "project": None,
            "turn_count": 10,
        }
        (sessions_dir / "abc123.json").write_text(json.dumps(session_data))

        from shipkit.content.hooks.lib.session_context import format_session_context
        result = format_session_context()
        assert "Fix auth bug" in result

    def test_format_pending_retro_nudge_empty(self, initialized_home, monkeypatch):
        monkeypatch.setenv("SHIPKIT_HOME", str(initialized_home))
        from shipkit.content.hooks.lib.session_context import format_pending_retro_nudge
        result = format_pending_retro_nudge()
        assert result == ""

    def test_format_learned_preferences_empty(self, initialized_home, monkeypatch):
        monkeypatch.setenv("SHIPKIT_HOME", str(initialized_home))
        from shipkit.content.hooks.lib.session_context import format_learned_preferences
        result = format_learned_preferences()
        assert result == ""

    def test_format_learned_preferences_with_file(self, initialized_home, monkeypatch):
        monkeypatch.setenv("SHIPKIT_HOME", str(initialized_home))
        prefs = initialized_home / "guidelines" / "auto-learned.md"
        prefs.write_text(
            "---\ndescription: test\n---\n\n# Preferences\n\n- Be concise\n"
        )
        from shipkit.content.hooks.lib.session_context import format_learned_preferences
        result = format_learned_preferences()
        assert "Be concise" in result


class TestDebounce:

    def test_get_debounce_dir(self, initialized_home, monkeypatch):
        monkeypatch.setenv("SHIPKIT_HOME", str(initialized_home))
        from shipkit.content.hooks.lib.debounce import get_debounce_dir
        debounce_dir = get_debounce_dir()
        assert debounce_dir.exists()
        assert ".state" in str(debounce_dir)
        assert debounce_dir.name == "debounce"

    def test_cleanup_debounce(self, initialized_home, monkeypatch):
        monkeypatch.setenv("SHIPKIT_HOME", str(initialized_home))
        from shipkit.content.hooks.lib.debounce import get_debounce_dir, cleanup_debounce

        debounce_dir = get_debounce_dir()
        ns = "test-hook.sess123"
        (debounce_dir / f"{ns}.trigger").write_text("")
        (debounce_dir / f"{ns}.transcript").write_text("data")

        cleanup_debounce("test-hook", "sess123")
        assert not (debounce_dir / f"{ns}.trigger").exists()
        assert not (debounce_dir / f"{ns}.transcript").exists()
