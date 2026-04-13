"""Content validation for shipkit.

Validates the structure and integrity of shipkit content:
skills, steering, hooks, plugins, JSON configs, and PII scanning.

Can be run as:
    shipkit doctor --lint    (via CLI)
    python -m shipkit.lint   (standalone)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml


# ── Result accumulator ────────────────────────────────────

class Results:
    def __init__(self, verbose: bool = True):
        self.errors = 0
        self.warnings = 0
        self.verbose = verbose

    def ok(self, label: str) -> None:
        if self.verbose:
            print(f"  + {label}")

    def err(self, label: str, msg: str = "") -> None:
        self.errors += 1
        print(f"  ! {label}{f': {msg}' if msg else ''}")

    def warn(self, label: str, msg: str = "") -> None:
        self.warnings += 1
        print(f"  ~ {label}{f': {msg}' if msg else ''}")

    @property
    def passed(self) -> bool:
        return self.errors == 0


# ── Frontmatter helpers ──────────────────────────────────

def _fm_raw(text: str) -> str | None:
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    return m.group(1) if m else None


def _fm_field(fm: str, field: str) -> str | None:
    m = re.search(rf"^{re.escape(field)}:\s*(.+)$", fm, re.MULTILINE)
    return m.group(1).strip().strip("'\"") if m else None


# ── Content root ─────────────────────────────────────────

CONTENT_DIR = Path(__file__).parent / "content"


# ── Checks ───────────────────────────────────────────────

def check_json(results: Results) -> None:
    """Validate all JSON files in seed/ and content/."""
    pkg_root = Path(__file__).parent.parent
    json_files = list(pkg_root.glob("seed/**/*.json")) + list(CONTENT_DIR.glob("**/*.json"))

    if not json_files:
        results.warn("json", "no JSON files found")
        return

    for f in sorted(json_files):
        rel = str(f.relative_to(pkg_root))
        try:
            json.loads(f.read_text())
            results.ok(rel)
        except json.JSONDecodeError as e:
            results.err(rel, str(e))


def check_skills(results: Results) -> None:
    """Validate skill structure: SKILL.md must exist in each skill directory."""
    skills_dir = CONTENT_DIR / "skills"
    if not skills_dir.is_dir():
        results.err("skills/", "directory not found")
        return

    for skill_dir in sorted(d for d in skills_dir.iterdir() if d.is_dir()):
        prefix = f"skills/{skill_dir.name}"
        skill_md = skill_dir / "SKILL.md"

        if not skill_md.exists():
            results.err(prefix, "missing SKILL.md")
            continue

        text = skill_md.read_text()

        # Check it starts with a heading
        if not text.strip().startswith("#"):
            results.warn(prefix, "SKILL.md doesn't start with a heading")

        # Check minimum length
        if len(text.strip()) < 50:
            results.warn(prefix, "SKILL.md is very short (<50 chars)")

        # Check references/ if present
        refs = skill_dir / "references"
        if refs.is_dir() and not any(refs.iterdir()):
            results.warn(prefix, "references/ directory is empty")

        results.ok(prefix)


def check_steering(results: Results) -> None:
    """Validate steering files: must be markdown, have reasonable content."""
    steering_dir = CONTENT_DIR / "steering"
    if not steering_dir.is_dir():
        results.err("steering/", "directory not found")
        return

    for f in sorted(steering_dir.glob("*.md")):
        rel = f"steering/{f.name}"
        text = f.read_text()

        if len(text.strip()) < 20:
            results.warn(rel, "very short (<20 chars)")
            continue

        # Check for frontmatter if present
        fm = _fm_raw(text)
        if fm:
            desc = _fm_field(fm, "description")
            if not desc:
                results.warn(rel, "has frontmatter but no 'description' field")

        results.ok(rel)


def check_hooks(results: Results) -> None:
    """Validate hook YAML definitions: required fields, valid events."""
    hooks_dir = CONTENT_DIR / "hooks"
    if not hooks_dir.is_dir():
        results.err("hooks/", "directory not found")
        return

    valid_events = {"session_start", "session_end", "user_prompt_submit"}

    for f in sorted(hooks_dir.glob("*.yaml")):
        rel = f"hooks/{f.name}"
        try:
            data = yaml.safe_load(f.read_text())
        except yaml.YAMLError as e:
            results.err(rel, f"invalid YAML: {e}")
            continue

        if not isinstance(data, dict):
            results.err(rel, "not a YAML mapping")
            continue

        for field in ("name", "event", "command"):
            if not data.get(field):
                results.err(rel, f"missing required field '{field}'")

        event = data.get("event", "")
        if event and event not in valid_events:
            results.warn(rel, f"unknown event '{event}' (expected: {', '.join(sorted(valid_events))})")

        if results.errors == 0:
            results.ok(rel)


def check_plugins(results: Results, home_path: Path | None = None) -> None:
    """Validate installed plugins: manifest, skills structure."""
    if home_path is None:
        from shipkit.config import SHIPKIT_HOME
        home_path = SHIPKIT_HOME

    plugins_dir = home_path / "plugins"
    if not plugins_dir.is_dir():
        results.ok("plugins/ (not present)")
        return

    plugin_dirs = sorted(d for d in plugins_dir.iterdir() if d.is_dir())
    if not plugin_dirs:
        results.ok("plugins/ (none installed)")
        return

    for plugin_dir in plugin_dirs:
        prefix = f"plugins/{plugin_dir.name}"
        has_error = False

        manifest = plugin_dir / "plugin.yaml"
        if not manifest.exists():
            results.err(prefix, "missing plugin.yaml")
            has_error = True
        else:
            try:
                data = yaml.safe_load(manifest.read_text())
                if not isinstance(data, dict):
                    results.err(prefix, "plugin.yaml is not a YAML mapping")
                    has_error = True
                else:
                    for field in ("name", "description"):
                        if not data.get(field):
                            results.err(prefix, f"plugin.yaml missing '{field}'")
                            has_error = True
            except yaml.YAMLError as e:
                results.err(prefix, f"plugin.yaml invalid YAML: {e}")
                has_error = True

        # Check skills
        skills = plugin_dir / "skills"
        if skills.is_dir():
            for skill in sorted(d for d in skills.iterdir() if d.is_dir()):
                if not (skill / "SKILL.md").exists():
                    results.err(f"{prefix}/skills/{skill.name}", "missing SKILL.md")
                    has_error = True

        if not has_error:
            results.ok(prefix)


def check_subagents(results: Results) -> None:
    """Validate subagent YAML definitions: required fields, valid models."""
    subagents_dir = CONTENT_DIR / "subagents"
    if not subagents_dir.is_dir():
        results.warn("subagents/", "directory not found")
        return

    valid_models = {"sonnet", "haiku", "opus"}

    for f in sorted(subagents_dir.glob("*.yaml")):
        rel = f"subagents/{f.name}"
        try:
            data = yaml.safe_load(f.read_text())
        except yaml.YAMLError as e:
            results.err(rel, f"invalid YAML: {e}")
            continue

        if not isinstance(data, dict):
            results.err(rel, "not a YAML mapping")
            continue

        for field in ("name", "description", "model", "prompt"):
            if not data.get(field):
                results.err(rel, f"missing required field '{field}'")

        model = data.get("model", "")
        if model and model not in valid_models:
            results.warn(rel, f"unknown model '{model}' (expected: {', '.join(sorted(valid_models))})")

        tools = data.get("tools", [])
        if not tools:
            results.warn(rel, "no tools defined")

        if results.errors == 0:
            results.ok(rel)


def check_pii(results: Results) -> None:
    """Scan content for PII patterns (emails, home directories)."""
    patterns = [re.compile(p) for p in [
        r"[a-z]{2,}@(gmail|yahoo|hotmail|outlook|company)\.\w+",
        r"/Users/[a-z]{2,}/",
        r"/home/[a-z]{2,}/",
    ]]
    # Placeholders and examples that are intentionally in content
    excludes = ["user@", "you@", "alias@", "/Users/you/", "/Users/alice/", "<home>/", "{home}"]

    skip_parts = {".venv", "venv", "node_modules", "__pycache__", ".git"}

    scan_dirs = [CONTENT_DIR, Path(__file__).parent.parent / "seed"]
    files = [
        p for d in scan_dirs if d.is_dir()
        for p in d.rglob("*")
        if p.is_file() and not (skip_parts & set(p.parts)) and p.suffix in (".md", ".yaml", ".json", ".py", ".txt")
    ]

    pkg_root = Path(__file__).parent.parent
    found = False
    for fpath in files:
        try:
            text = fpath.read_text(errors="ignore")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for pat in patterns:
                for m in pat.finditer(line):
                    if any(e.lower() in m.group(0).lower() for e in excludes):
                        continue
                    rel = str(fpath.relative_to(pkg_root))
                    results.err(f"{rel}:{lineno}", f"PII candidate: {m.group(0)}")
                    found = True

    if not found:
        results.ok("PII scan clean")


def check_links(results: Results) -> None:
    """Validate relative markdown links in content files."""
    pkg_root = Path(__file__).parent.parent
    md_files = list(CONTENT_DIR.rglob("*.md"))

    # Patterns that are templates/examples, not real links
    placeholder_patterns = re.compile(r"^(url|NNNN|example|placeholder|TODO)", re.IGNORECASE)

    for doc in sorted(md_files):
        for lineno, line in enumerate(doc.read_text().splitlines(), 1):
            for m in re.finditer(r"\[([^\]]*)\]\(([^)]+)\)", line):
                link = m.group(2)
                if re.match(r"(https?://|mailto:|#)", link):
                    continue
                path = link.split("#")[0]
                if not path or placeholder_patterns.match(path):
                    continue
                if not (doc.parent / path).exists():
                    rel = str(doc.relative_to(pkg_root))
                    results.err(f"{rel}:{lineno}", f"broken link: {link}")


# ── Runner ───────────────────────────────────────────────

CHECKS = [
    ("json",     "JSON Validation",    check_json),
    ("skills",   "Skill Structure",    check_skills),
    ("steering", "Steering Rules",     check_steering),
    ("hooks",    "Hook Definitions",   check_hooks),
    ("subagents","Subagent Definitions",check_subagents),
    ("plugins",  "Plugin Validation",  check_plugins),
    ("pii",      "PII Scan",           check_pii),
    ("links",    "Markdown Links",     check_links),
]


def run_all(verbose: bool = True) -> bool:
    """Run all checks. Returns True if all passed."""
    failed = 0
    for name, title, fn in CHECKS:
        print(f"--- {title} ---")
        r = Results(verbose=verbose)
        if fn == check_plugins:
            fn(r)  # uses default home_path
        else:
            fn(r)
        if not r.passed:
            failed += 1
        print()

    if failed == 0:
        print("All checks passed.")
    else:
        print(f"{failed} check(s) failed.")
    return failed == 0


def run_check(name: str, verbose: bool = True) -> bool:
    """Run a single check by name. Returns True if passed."""
    by_name = {n: (t, fn) for n, t, fn in CHECKS}
    if name not in by_name:
        print(f"Unknown check: {name}")
        print(f"Available: {', '.join(by_name)}")
        return False
    title, fn = by_name[name]
    print(f"--- {title} ---")
    r = Results(verbose=verbose)
    fn(r)
    return r.passed


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--list" in args:
        for name, title, _ in CHECKS:
            print(f"  {name:12s} {title}")
    elif args:
        sys.exit(0 if run_check(args[0]) else 1)
    else:
        sys.exit(0 if run_all() else 1)
