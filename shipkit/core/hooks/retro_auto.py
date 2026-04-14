#!/usr/bin/env python3
"""Autonomous learning loop hook for shipkit.

Runs at session start (SessionStart / spawn). Checks for pending retro
suggestions and observations, classifies them as learnable vs structural,
and auto-promotes learnable rules.

Learnable rules go to:
- <home>/guidelines/auto-learned.md (cross-cutting)
- <home>/skills/<skill-name>/learned.md (skill-specific)

Structural changes stay in .state/retro/pending/ for manual triage via /retro.

Also runs consolidation on a 7-day cycle: groups related rules, merges
duplicates, enforces token budgets.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from hooks.lib.config import resolve_home_path, is_hook_session
from hooks.lib.logging_util import log_entry, debug_log


HOOK_NAME = "retro-auto"
CONSOLIDATION_INTERVAL_DAYS = 7


def main():
    if is_hook_session():
        sys.exit(0)

    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        event = {}

    vault_path = resolve_home_path()
    if vault_path is None:
        sys.exit(0)

    guidelines_dir = vault_path / "guidelines"
    guidelines_dir.mkdir(parents=True, exist_ok=True)
    skills_dir = vault_path / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Check if there's work to do
    pending_dir = vault_path / ".state" / "retro" / "pending"
    observations_file = vault_path / ".state" / "retro" / "observations.jsonl"
    state_dir = vault_path / ".state" / "retro"
    state_dir.mkdir(parents=True, exist_ok=True)
    last_promoted = state_dir / ".last-promoted"

    has_pending = pending_dir.exists() and any(pending_dir.glob("*.json"))
    has_observations = observations_file.exists() and observations_file.stat().st_size > 0

    if not has_pending and not has_observations:
        debug_log(HOOK_NAME, "No pending suggestions or observations")
        sys.exit(0)

    # Check if anything changed since last promotion
    if last_promoted.exists():
        last_promoted_time = last_promoted.stat().st_mtime
        newest_change = 0
        if has_pending:
            for pf in pending_dir.glob("*.json"):
                newest_change = max(newest_change, pf.stat().st_mtime)
        if has_observations:
            newest_change = max(newest_change, observations_file.stat().st_mtime)
        if newest_change <= last_promoted_time:
            debug_log(HOOK_NAME, "No changes since last promotion")
            # Still check consolidation
            _maybe_consolidate(vault_path)
            sys.exit(0)

    # Process observations — count occurrences, promote if threshold met
    promoted_count = 0
    if has_observations:
        promoted_count += _process_observations(vault_path)

    # Process pending suggestions — auto-promote learnable ones
    if has_pending:
        promoted_count += _process_pending(vault_path)

    if promoted_count > 0:
        log_entry(HOOK_NAME, f"Auto-promoted {promoted_count} learnable rules")

    # Update last-promoted marker
    last_promoted.touch()

    # Check if consolidation is due
    _maybe_consolidate(vault_path)


def _process_observations(vault_path: Path) -> int:
    """Count observation occurrences and promote those over threshold."""
    observations_file = vault_path / ".state" / "retro" / "observations.jsonl"
    if not observations_file.exists():
        return 0

    # Count occurrences by title
    counts: dict[str, dict] = {}
    try:
        for line in observations_file.read_text().splitlines():
            if not line.strip():
                continue
            try:
                obs = json.loads(line)
                title = obs.get("title", "")
                if title not in counts:
                    counts[title] = {"count": 0, "type": obs.get("type", ""), "target": obs.get("target")}
                counts[title]["count"] += 1
            except json.JSONDecodeError:
                continue
    except OSError:
        return 0

    # Promote observations with 3+ occurrences
    promoted = 0
    for title, info in counts.items():
        if info["count"] >= 3:
            _promote_rule(vault_path, title, info["count"], info.get("target"))
            promoted += 1

    return promoted


def _process_pending(vault_path: Path) -> int:
    """Process pending suggestions — auto-promote learnable ones."""
    pending_dir = vault_path / ".state" / "retro" / "pending"
    promoted = 0

    for pf in sorted(pending_dir.glob("*.json")):
        try:
            data = json.loads(pf.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        suggestions = data.get("suggestions", [])
        remaining = []
        for s in suggestions:
            if _is_learnable(s):
                target = s.get("target")
                title = s.get("suggestion", s.get("title", ""))
                _promote_rule(vault_path, title, 1, target)
                promoted += 1
                debug_log(HOOK_NAME, f"Auto-promoted: {s.get('title', '')}")
            else:
                remaining.append(s)

        # Update pending file — remove promoted suggestions
        if len(remaining) < len(suggestions):
            if remaining:
                data["suggestions"] = remaining
                pf.write_text(json.dumps(data, indent=2) + "\n")
            else:
                # All suggestions promoted — move to processed
                processed_dir = vault_path / ".state" / "retro" / "processed"
                processed_dir.mkdir(parents=True, exist_ok=True)
                pf.rename(processed_dir / pf.name)

    return promoted


def _is_learnable(suggestion: dict) -> bool:
    """Classify a suggestion as learnable vs structural.

    Learnable: single-sentence behavioral constraint, changes a default/format.
    Structural: requires workflow changes, new steps, error handling.
    """
    stype = suggestion.get("type", "")
    severity = suggestion.get("severity", "low")
    text = suggestion.get("suggestion", "")

    # Guidelines updates and knowledge are typically learnable
    if stype in ("guidelines_update", "knowledge"):
        return True

    # New skills and new guidelines files are structural
    if stype in ("new_skill", "new_guidelines"):
        return False

    # Skill improvements: check if it's a simple rule vs structural change
    if stype == "skill_improvement":
        structural_signals = [
            "add a step", "add step", "new step",
            "error handling", "handle the case",
            "check for", "validate", "verify before",
            "workflow", "rewrite",
        ]
        text_lower = text.lower()
        if any(signal in text_lower for signal in structural_signals):
            return False
        return True

    return False


def _promote_rule(vault_path: Path, rule_text: str, count: int, target: str | None) -> None:
    """Write a learnable rule to the appropriate file."""
    if target and "/" in target:
        # Extract skill name from target path
        parts = target.split("/")
        for i, part in enumerate(parts):
            if part == "skills" and i + 1 < len(parts):
                skill_name = parts[i + 1]
                skill_dir = vault_path / "skills" / skill_name
                skill_dir.mkdir(parents=True, exist_ok=True)
                _append_to_learned_file(
                    skill_dir / "learned.md",
                    rule_text, count, f"Learned: {skill_name}",
                    f"Learned rules for the {skill_name} skill.",
                    token_budget=1000,
                )
                return

    # Cross-cutting rule → guidelines/auto-learned.md
    _append_to_learned_file(
        vault_path / "guidelines" / "auto-learned.md",
        rule_text, count, "Auto-Learned Preferences",
        "Cross-cutting behavioral preferences. Customizations + auto-learned.",
        token_budget=3000,
    )


def _append_to_learned_file(
    path: Path,
    rule_text: str,
    count: int,
    title: str,
    description: str,
    token_budget: int,
) -> None:
    """Append a rule to a learned file's Auto-Learned section."""
    if not path.exists():
        # Create with template
        path.write_text(
            f"---\n"
            f'description: "{description}"\n'
            f"---\n\n"
            f"# {title}\n\n"
            f"## Customizations\n"
            f"<!-- User-maintained. Retro-auto does NOT touch this section. -->\n\n"
            f"## Auto-Learned\n"
            f"<!-- Auto-maintained by retro-auto. Token budget: {token_budget}. -->\n\n"
            f"- {rule_text} ({count}x)\n"
        )
        return

    content = path.read_text()

    # Check if rule already exists (by first 50 chars)
    rule_prefix = rule_text[:50].lower()
    for line in content.splitlines():
        if line.strip().startswith("- ") and rule_prefix in line.lower():
            # Update count
            import re
            new_line = re.sub(r"\((\d+)x\)", lambda m: f"({int(m.group(1)) + count}x)", line)
            if new_line != line:
                content = content.replace(line, new_line)
                path.write_text(content)
            return

    # Append new rule after "## Auto-Learned" section
    if "## Auto-Learned" in content:
        # Find the end of the Auto-Learned comment line and append after it
        lines = content.splitlines()
        insert_idx = len(lines)
        found_section = False
        for i, line in enumerate(lines):
            if "## Auto-Learned" in line:
                found_section = True
            elif found_section and not line.strip().startswith("<!--"):
                insert_idx = i
                break

        lines.insert(insert_idx, f"- {rule_text} ({count}x)")
        path.write_text("\n".join(lines) + "\n")
    else:
        # Fallback: append to end
        with open(path, "a") as f:
            f.write(f"\n- {rule_text} ({count}x)\n")


def _maybe_consolidate(vault_path: Path) -> None:
    """Run consolidation if the 7-day interval has passed."""
    state_dir = vault_path / ".state" / "retro"
    state_dir.mkdir(parents=True, exist_ok=True)
    marker = state_dir / ".last-consolidated"

    if marker.exists():
        age_days = (time.time() - marker.stat().st_mtime) / 86400
        if age_days < CONSOLIDATION_INTERVAL_DAYS:
            return

    # Consolidation is a manual process — we just flag it
    # The retro skill handles actual consolidation with user approval
    log_entry(HOOK_NAME, "Consolidation due — run /retro to consolidate learned rules")
    marker.touch()


if __name__ == "__main__":
    main()
