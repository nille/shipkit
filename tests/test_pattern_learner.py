"""Tests for pattern learner hook."""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

import pytest


@pytest.fixture
def patterns_dir(tmp_path):
    """Create a temporary patterns directory."""
    p = tmp_path / "patterns"
    p.mkdir()
    return p


@pytest.fixture
def sample_transcript(tmp_path):
    """Create a sample session transcript."""
    transcript = {
        "sessionId": "test-session-123",
        "turns": [
            {
                "assistant_content": [
                    {"type": "tool_use", "tool": "Bash", "parameters": {"command": "grep -r ERROR logs/"}},
                ]
            },
            {
                "assistant_content": [
                    {"type": "tool_use", "tool": "Bash", "parameters": {"command": "tail -100 logs/app.log"}},
                ]
            },
            {
                "assistant_content": [
                    {"type": "tool_use", "tool": "Bash", "parameters": {"command": "systemctl restart myapp"}},
                ]
            },
            {
                "assistant_content": [
                    {"type": "tool_use", "tool": "Bash", "parameters": {"command": "curl localhost:8080/health"}},
                ]
            },
        ]
    }

    transcript_file = tmp_path / "transcript.json"
    transcript_file.write_text(json.dumps(transcript))
    return transcript_file


class TestCommandSequenceExtraction:

    def test_extracts_bash_sequence(self):
        """Test extraction of bash command sequences."""
        from shipkit.core.hooks.pattern_learner import extract_command_sequences

        transcript = {
            "turns": [
                {"assistant_content": [{"type": "tool_use", "tool": "Bash", "parameters": {"command": "cmd1"}}]},
                {"assistant_content": [{"type": "tool_use", "tool": "Bash", "parameters": {"command": "cmd2"}}]},
                {"assistant_content": [{"type": "tool_use", "tool": "Bash", "parameters": {"command": "cmd3"}}]},
            ]
        }

        sequences = extract_command_sequences(transcript)

        assert len(sequences) == 1
        assert sequences[0]["commands"] == ["cmd1", "cmd2", "cmd3"]
        assert sequences[0]["length"] == 3

    def test_ignores_short_sequences(self):
        """Test that sequences < 3 commands are ignored."""
        from shipkit.core.hooks.pattern_learner import extract_command_sequences

        transcript = {
            "turns": [
                {"assistant_content": [{"type": "tool_use", "tool": "Bash", "parameters": {"command": "cmd1"}}]},
                {"assistant_content": [{"type": "tool_use", "tool": "Bash", "parameters": {"command": "cmd2"}}]},
            ]
        }

        sequences = extract_command_sequences(transcript)
        assert len(sequences) == 0

    def test_sequence_broken_by_non_bash(self):
        """Test that non-bash tools break sequences."""
        from shipkit.core.hooks.pattern_learner import extract_command_sequences

        transcript = {
            "turns": [
                {"assistant_content": [{"type": "tool_use", "tool": "Bash", "parameters": {"command": "cmd1"}}]},
                {"assistant_content": [{"type": "tool_use", "tool": "Bash", "parameters": {"command": "cmd2"}}]},
                {"assistant_content": [{"type": "tool_use", "tool": "Read", "parameters": {"file_path": "test"}}]},
                {"assistant_content": [{"type": "tool_use", "tool": "Bash", "parameters": {"command": "cmd3"}}]},
            ]
        }

        sequences = extract_command_sequences(transcript)
        # Should not find any 3+ sequence (broken by Read)
        assert len(sequences) == 0


class TestFileEditPatterns:

    def test_extracts_coedited_files(self):
        """Test extraction of files edited together."""
        from shipkit.core.hooks.pattern_learner import extract_file_edit_patterns

        transcript = {
            "turns": [
                {
                    "assistant_content": [
                        {"type": "tool_use", "tool": "Edit", "parameters": {"file_path": "routes.ts"}},
                        {"type": "tool_use", "tool": "Edit", "parameters": {"file_path": "controller.ts"}},
                        {"type": "tool_use", "tool": "Edit", "parameters": {"file_path": "tests/api.test.ts"}},
                    ]
                },
            ]
        }

        patterns = extract_file_edit_patterns(transcript)

        assert len(patterns) == 1
        assert "routes.ts" in patterns[0]["files"]
        assert "controller.ts" in patterns[0]["files"]
        assert "tests/api.test.ts" in patterns[0]["files"]

    def test_ignores_single_file_edits(self):
        """Test that single file edits are not patterns."""
        from shipkit.core.hooks.pattern_learner import extract_file_edit_patterns

        transcript = {
            "turns": [
                {"assistant_content": [{"type": "tool_use", "tool": "Edit", "parameters": {"file_path": "app.py"}}]},
            ]
        }

        patterns = extract_file_edit_patterns(transcript)
        assert len(patterns) == 0


class TestPatternStorage:

    def test_save_and_load_pattern(self, patterns_dir):
        """Test saving and loading patterns."""
        from shipkit.core.hooks.pattern_learner import Pattern, save_pattern, load_pattern_history

        pattern = Pattern(
            pattern_id="abc123",
            pattern_type="command_sequence",
            description="Debug workflow",
            occurrences=3,
            first_seen="2026-04-14T10:00:00",
            last_seen="2026-04-14T15:00:00",
            sessions=["s1", "s2", "s3"],
            automatable=True,
            suggested_skill_name="debug-service",
            confidence=0.9,
            commands=["grep ERROR", "tail logs", "restart"],
        )

        save_pattern(pattern, patterns_dir)

        # Load it back
        loaded = load_pattern_history(patterns_dir)

        assert "abc123" in loaded
        assert loaded["abc123"].pattern_type == "command_sequence"
        assert loaded["abc123"].occurrences == 3
        assert loaded["abc123"].suggested_skill_name == "debug-service"

    def test_merge_pattern_occurrence(self):
        """Test merging new occurrence into existing pattern."""
        from shipkit.core.hooks.pattern_learner import Pattern, merge_pattern_occurrence

        existing = Pattern(
            pattern_id="test",
            pattern_type="command_sequence",
            description="Test",
            occurrences=2,
            first_seen="2026-04-14T10:00:00",
            last_seen="2026-04-14T11:00:00",
            sessions=["s1", "s2"],
            automatable=True,
            suggested_skill_name="test-skill",
            confidence=0.8,
        )

        merged = merge_pattern_occurrence(existing, "s3")

        assert merged.occurrences == 3
        assert "s3" in merged.sessions
        assert len(merged.sessions) == 3


class TestSuggestionThreshold:

    def test_suggests_after_threshold(self):
        """Test that patterns are only suggested after threshold."""
        from shipkit.core.hooks.pattern_learner import Pattern, should_suggest

        pattern = Pattern(
            pattern_id="test",
            pattern_type="command_sequence",
            description="Test",
            occurrences=3,
            first_seen="2026-04-14T10:00:00",
            last_seen="2026-04-14T15:00:00",
            sessions=["s1", "s2", "s3"],
            automatable=True,
            suggested_skill_name="test-skill",
            confidence=0.9,
        )

        assert should_suggest(pattern, threshold=3)

    def test_not_suggests_below_threshold(self):
        """Test that patterns below threshold aren't suggested."""
        from shipkit.core.hooks.pattern_learner import Pattern, should_suggest

        pattern = Pattern(
            pattern_id="test",
            pattern_type="command_sequence",
            description="Test",
            occurrences=2,  # Below threshold
            first_seen="2026-04-14T10:00:00",
            last_seen="2026-04-14T11:00:00",
            sessions=["s1", "s2"],
            automatable=True,
            suggested_skill_name="test-skill",
            confidence=0.9,
        )

        assert not should_suggest(pattern, threshold=3)

    def test_not_suggests_low_confidence(self):
        """Test that low confidence patterns aren't suggested."""
        from shipkit.core.hooks.pattern_learner import Pattern, should_suggest

        pattern = Pattern(
            pattern_id="test",
            pattern_type="command_sequence",
            description="Test",
            occurrences=5,
            first_seen="2026-04-14T10:00:00",
            last_seen="2026-04-14T15:00:00",
            sessions=["s1", "s2", "s3", "s4", "s5"],
            automatable=True,
            suggested_skill_name="test-skill",
            confidence=0.5,  # Too low
        )

        assert not should_suggest(pattern, threshold=3)

    def test_not_suggests_not_automatable(self):
        """Test that patterns marked not automatable aren't suggested."""
        from shipkit.core.hooks.pattern_learner import Pattern, should_suggest

        pattern = Pattern(
            pattern_id="test",
            pattern_type="command_sequence",
            description="Test",
            occurrences=5,
            first_seen="2026-04-14T10:00:00",
            last_seen="2026-04-14T15:00:00",
            sessions=["s1", "s2", "s3", "s4", "s5"],
            automatable=False,  # LLM said no
            suggested_skill_name=None,
            confidence=0.9,
        )

        assert not should_suggest(pattern, threshold=3)


class TestPatternHash:

    def test_same_commands_same_hash(self):
        """Test that identical commands produce same hash."""
        from shipkit.core.hooks.pattern_learner import hash_pattern

        pattern1 = "cmd1|cmd2|cmd3"
        pattern2 = "cmd1|cmd2|cmd3"

        assert hash_pattern(pattern1) == hash_pattern(pattern2)

    def test_different_commands_different_hash(self):
        """Test that different commands produce different hash."""
        from shipkit.core.hooks.pattern_learner import hash_pattern

        pattern1 = "cmd1|cmd2|cmd3"
        pattern2 = "cmd1|cmd2|cmd4"

        assert hash_pattern(pattern1) != hash_pattern(pattern2)
