"""Tests for shipkit.datadir."""

from __future__ import annotations

from pathlib import Path

import pytest

from shipkit.datadir import ensure_home, resolve_home, validate_home, DataDirError, HOME_DIRS


class TestEnsureHome:

    def test_creates_directories(self, tmp_home):
        home = ensure_home()
        assert home == tmp_home
        for d in HOME_DIRS:
            assert (home / d).is_dir(), f"Missing: {d}"

    def test_creates_config_yaml(self, tmp_home):
        ensure_home()
        assert (tmp_home / "config.yaml").exists()

    def test_idempotent(self, tmp_home):
        ensure_home()
        # Add a file to verify it's not wiped
        (tmp_home / "plugins" / "test.txt").write_text("test\n")
        ensure_home()
        assert (tmp_home / "plugins" / "test.txt").exists()

    def test_returns_path(self, tmp_home):
        result = ensure_home()
        assert isinstance(result, Path)
        assert result.exists()


class TestResolveHome:

    def test_returns_existing_home(self, initialized_home):
        result = resolve_home()
        assert result == initialized_home

    def test_raises_when_missing(self, tmp_home):
        # tmp_home exists but isn't initialized — the dir was created by fixture
        # but resolve_home checks if SHIPKIT_HOME exists
        import shutil
        shutil.rmtree(tmp_home)
        with pytest.raises(DataDirError, match="not initialized"):
            resolve_home()


class TestValidateHome:

    def test_valid_home(self, initialized_home):
        warnings = validate_home(initialized_home)
        assert warnings == []

    def test_missing_directories(self, tmp_home):
        tmp_home.mkdir(exist_ok=True)
        warnings = validate_home(tmp_home)
        assert len(warnings) > 0
        assert any("plugins" in w for w in warnings)

    def test_partial_structure(self, initialized_home):
        import shutil
        shutil.rmtree(initialized_home / "plugins")
        warnings = validate_home(initialized_home)
        assert len(warnings) == 1
        assert "plugins" in warnings[0]
