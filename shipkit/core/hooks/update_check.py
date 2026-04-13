#!/usr/bin/env python3
"""Session-start hook: check for newer shipkit version on PyPI.

Uses a daily cache to avoid network calls on every session.
Cache file lives at <home>/.state/update-check.cache
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

# Hook lib is in the same package
sys.path.insert(0, str(Path(__file__).parent))

from lib.config import resolve_home_path, is_hook_session

CACHE_MAX_AGE = 86400  # 24 hours
PYPI_URL = "https://pypi.org/pypi/shipkit/json"
PYPI_TIMEOUT = 5


def _get_installed_version() -> str:
    """Get the installed shipkit version."""
    try:
        from importlib.metadata import version
        return version("shipkit")
    except Exception:
        return ""


def _read_cache(cache_file: Path) -> dict:
    """Read KEY=value cache file into a dict."""
    result = {}
    if not cache_file.is_file():
        return result
    for line in cache_file.read_text().splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip()
    return result


def _cache_is_fresh(cache_file: Path) -> bool:
    """Check if cache file exists and is less than CACHE_MAX_AGE seconds old."""
    if not cache_file.is_file():
        return False
    age = time.time() - cache_file.stat().st_mtime
    return age < CACHE_MAX_AGE


def _fetch_latest_version() -> str:
    """Query PyPI for the latest shipkit version."""
    try:
        req = urllib.request.Request(PYPI_URL, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=PYPI_TIMEOUT) as resp:
            data = json.loads(resp.read())
            return data.get("info", {}).get("version", "")
    except Exception:
        return ""


def _output_update_message(latest: str, current: str) -> None:
    """Print the update notification for agent context injection."""
    print(f"INSTRUCTION: shipkit {latest} is available (current: {current}). "
          f'Mention once at a natural pause: "There\'s a new shipkit version ({latest}). '
          f"Run `pip install --upgrade shipkit` to update.\" "
          f"Then don't mention it again this session.")


def main() -> None:
    if is_hook_session():
        return

    home_path = resolve_home_path()
    if not home_path:
        return

    cache_file = home_path / ".state" / "update-check.cache"

    current = _get_installed_version()
    if not current:
        return

    # Fast path: read cache if fresh
    if _cache_is_fresh(cache_file):
        cache = _read_cache(cache_file)
        latest = cache.get("LATEST", "")
        cached_current = cache.get("CURRENT", "")
        if latest and cached_current == current and latest != current:
            _output_update_message(latest, current)
        return

    # Slow path: query PyPI
    latest = _fetch_latest_version()
    if not latest:
        return

    # Write cache
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(f"CURRENT={current}\nLATEST={latest}\n")

    if latest != current:
        _output_update_message(latest, current)


if __name__ == "__main__":
    main()
