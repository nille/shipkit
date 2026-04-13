"""Tests for shipkit.lint."""

from __future__ import annotations

from pathlib import Path

import pytest

from shipkit.lint import (
    Results, check_json, check_skills, check_steering,
    check_hooks, check_plugins, check_pii, check_links,
    run_all,
)


class TestResults:

    def test_starts_passing(self):
        r = Results(verbose=False)
        assert r.passed
        assert r.errors == 0
        assert r.warnings == 0

    def test_err_marks_failed(self):
        r = Results(verbose=False)
        r.err("test", "bad")
        assert not r.passed
        assert r.errors == 1

    def test_warn_still_passes(self):
        r = Results(verbose=False)
        r.warn("test", "minor")
        assert r.passed
        assert r.warnings == 1


class TestCheckJson:

    def test_validates_package_json(self):
        r = Results(verbose=False)
        check_json(r)
        assert r.passed


class TestCheckSkills:

    def test_validates_package_skills(self):
        r = Results(verbose=False)
        check_skills(r)
        assert r.passed


class TestCheckSteering:

    def test_validates_package_steering(self):
        r = Results(verbose=False)
        check_steering(r)
        assert r.passed


class TestCheckHooks:

    def test_validates_package_hooks(self):
        r = Results(verbose=False)
        check_hooks(r)
        assert r.passed


class TestCheckPii:

    def test_no_pii_in_package(self):
        r = Results(verbose=False)
        check_pii(r)
        assert r.passed


class TestCheckLinks:

    def test_no_broken_links(self):
        r = Results(verbose=False)
        check_links(r)
        assert r.passed


class TestCheckPlugins:

    def test_validates_plugins(self, initialized_home):
        r = Results(verbose=False)
        check_plugins(r, home_path=initialized_home)
        assert r.passed

    def test_catches_bad_plugin(self, initialized_home):
        bad = initialized_home / "plugins" / "bad-plugin"
        bad.mkdir(parents=True)
        r = Results(verbose=False)
        check_plugins(r, home_path=initialized_home)
        assert not r.passed


class TestRunAll:

    def test_all_pass(self):
        assert run_all(verbose=False)
