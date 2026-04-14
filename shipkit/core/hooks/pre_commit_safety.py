#!/usr/bin/env python3
"""Pre-commit safety check hook for shipkit.

Runs before tool use (pre_tool_use event). Scans git staged files when user
attempts to commit, looking for:
- Secrets (AWS keys, API tokens, credentials)
- Debug artifacts (console.log, debugger, print statements)
- Common mistakes (merge conflicts, large files, .env files)

If issues found, outputs INSTRUCTION for Claude to warn the user and block the commit.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# Hook lib is in the same package
sys.path.insert(0, str(Path(__file__).parent))

from lib.config import is_hook_session
from lib.llm_client import call_claude, is_llm_available


@dataclass
class Finding:
    """A detected issue in staged files."""
    severity: str  # "CRITICAL" (block), "WARNING" (warn)
    category: str  # "SECRET", "DEBUG", "MISTAKE"
    file: str
    line: int | None
    message: str


# Patterns to detect

SECRET_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "AWS access key"),
    (r"['\"]?(aws_access_key_id|aws_secret_access_key)['\"]?\s*[:=]\s*['\"]?[\w/+]{20,}", "AWS credential"),
    (r"['\"]?(api[_-]?key|api[_-]?token|secret)['\"]?\s*[:=]\s*['\"]?[\w-]{20,}", "API key/token"),
    (r"-----BEGIN (RSA |EC )?PRIVATE KEY-----", "Private key"),
    (r"['\"]?(password|passwd|pwd)['\"]?\s*[:=]\s*['\"]?[^'\"\s]{8,}", "Password"),
    (r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", "JWT token"),
    (r"github_pat_[0-9A-Za-z_]{82}", "GitHub personal access token"),
    (r"ghp_[0-9A-Za-z]{36}", "GitHub personal access token (classic)"),
]

DEBUG_PATTERNS = [
    (r"console\.(log|debug|info)\s*\(", "console.log() statement", [".js", ".ts", ".jsx", ".tsx"]),
    (r"\bdebugger\b", "debugger statement", [".js", ".ts", ".jsx", ".tsx"]),
    (r"^\s*print\s*\(", "print() statement", [".py"]),  # Only flag if at start of line (not in logging modules)
    (r"\bpdb\.set_trace\(\)", "pdb debugger", [".py"]),
    (r"\bbreakpoint\(\)", "breakpoint() call", [".py"]),
]

MISTAKE_PATTERNS = [
    (r"^<{7} ", "Merge conflict marker"),
    (r"^={7}$", "Merge conflict marker"),
    (r"^>{7} ", "Merge conflict marker"),
    (r"TODO|FIXME|XXX|HACK", "TODO/FIXME comment"),  # Warning, not critical
]

# Files that should never be committed
DANGEROUS_FILES = [
    ".env",
    ".env.local",
    ".env.production",
    "credentials.json",
    "service-account.json",
    "secrets.yaml",
    "private_key.pem",
    ".aws/credentials",
]


def should_scan(event: dict) -> bool:
    """Check if this tool use is commit-related and should trigger scan."""
    tool_name = event.get("tool", "")

    # Check for /commit skill
    if tool_name == "Skill":
        skill_name = event.get("parameters", {}).get("skill", "")
        if skill_name == "commit":
            return True

    # Check for direct git commit via Bash
    if tool_name == "Bash":
        command = event.get("parameters", {}).get("command", "")
        if "git commit" in command:
            return True

    return False


def get_staged_files() -> list[tuple[str, str]]:
    """Get list of staged files and their content.

    Returns: List of (filename, content) tuples
    """
    try:
        # Get staged file names
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            return []

        files = result.stdout.strip().split("\n")
        files = [f for f in files if f]  # Remove empty lines

        # Read content for each file
        staged_files = []
        for file in files:
            if not Path(file).exists():
                continue

            try:
                # Read with error handling for binary files
                content = Path(file).read_text(errors="ignore")
                staged_files.append((file, content))
            except Exception:
                # Skip files we can't read
                continue

        return staged_files

    except Exception:
        return []


def scan_for_secrets(file: str, content: str) -> list[Finding]:
    """Scan file content for secrets and credentials."""
    findings = []

    for pattern, description in SECRET_PATTERNS:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            line_num = content[:match.start()].count("\n") + 1
            findings.append(Finding(
                severity="CRITICAL",
                category="SECRET",
                file=file,
                line=line_num,
                message=description,
            ))

    return findings


def scan_for_debug(file: str, content: str) -> list[Finding]:
    """Scan file content for debug statements."""
    findings = []

    file_ext = Path(file).suffix

    for pattern, description, extensions in DEBUG_PATTERNS:
        # Only check if file extension matches
        if extensions and file_ext not in extensions:
            continue

        for match in re.finditer(pattern, content, re.MULTILINE):
            line_num = content[:match.start()].count("\n") + 1

            # Skip if in comments (basic heuristic)
            line_start = content.rfind("\n", 0, match.start()) + 1
            line_content = content[line_start:match.end()]
            if line_content.strip().startswith(("#", "//")):
                continue

            findings.append(Finding(
                severity="CRITICAL",
                category="DEBUG",
                file=file,
                line=line_num,
                message=description,
            ))

    return findings


def scan_for_mistakes(file: str, content: str) -> list[Finding]:
    """Scan file content for common mistakes."""
    findings = []

    for pattern, description in MISTAKE_PATTERNS:
        for match in re.finditer(pattern, content, re.MULTILINE):
            line_num = content[:match.start()].count("\n") + 1

            # TODO/FIXME is warning, merge conflicts are critical
            severity = "WARNING" if "TODO" in pattern else "CRITICAL"

            findings.append(Finding(
                severity=severity,
                category="MISTAKE",
                file=file,
                line=line_num,
                message=description,
            ))

    return findings


def check_dangerous_files(files: list[str]) -> list[Finding]:
    """Check if any dangerous files are being committed."""
    findings = []

    for file in files:
        filename = Path(file).name
        if filename in DANGEROUS_FILES:
            findings.append(Finding(
                severity="CRITICAL",
                category="SECRET",
                file=file,
                line=None,
                message=f"Dangerous file: {filename} should not be committed",
            ))

    return findings


def check_large_files(files: list[str]) -> list[Finding]:
    """Check for large files (>1MB) that might be binaries."""
    findings = []

    for file in files:
        if not Path(file).exists():
            continue

        size = Path(file).stat().st_size
        if size > 1_000_000:  # 1MB
            findings.append(Finding(
                severity="WARNING",
                category="MISTAKE",
                file=file,
                line=None,
                message=f"Large file ({size // 1024}KB) - is this a binary?",
            ))

    return findings


def verify_with_llm(findings: list[Finding], staged_files: list[tuple[str, str]]) -> list[Finding]:
    """Use LLM to verify if findings are real issues or false positives.

    Context-aware analysis that understands:
    - Test fixtures vs real secrets
    - Intentional debug code vs mistakes
    - Codebase conventions
    """
    if not findings:
        return []

    # Check if LLM is available and not disabled
    if not is_llm_available() or os.environ.get("SHIPKIT_NO_LLM") == "1":
        # Fallback to regex-only (all findings are real)
        return findings

    try:
        # Build context for LLM
        findings_text = []
        for i, f in enumerate(findings, 1):
            loc = f"line {f.line}" if f.line else "unknown"
            findings_text.append(f"{i}. {f.file} ({loc}): {f.message} [{f.category}]")

        # Get snippets of code around each finding
        file_contents = dict(staged_files)
        snippets = []
        for f in findings:
            if f.file in file_contents and f.line:
                content = file_contents[f.file]
                lines = content.split("\n")
                start = max(0, f.line - 3)
                end = min(len(lines), f.line + 2)
                snippet = "\n".join(f"{i+1}: {lines[i]}" for i in range(start, end))
                snippets.append(f"\n{f.file} (around line {f.line}):\n```\n{snippet}\n```")

        prompt = f"""Review these potential security issues in staged files about to be committed:

{chr(10).join(findings_text)}

Code snippets:
{chr(10).join(snippets)}

For each finding, determine:
1. Is this a REAL issue (actual secret/debug code that shouldn't be committed)?
2. Or a FALSE POSITIVE (test fixture, example, intentional)?

Context to consider:
- Test files (test_, spec_, fixture_) can have mock credentials
- Example/documentation code with placeholder values is OK
- Constants like TEST_API_KEY or EXAMPLE_TOKEN are usually safe
- Debug code in debug.py or dev-only files may be intentional

Respond with JSON array:
[
  {{"index": 1, "real_issue": true, "reason": "Real AWS key that would work", "severity": "CRITICAL"}},
  {{"index": 2, "real_issue": false, "reason": "Test fixture constant"}},
  ...
]

Be conservative: if uncertain, mark as real_issue. Only mark false_positive if clearly safe."""

        response = call_claude(prompt, model="claude-haiku-4", max_tokens=2000, temperature=0.0)

        # Parse LLM response
        # Extract JSON from response (may have markdown fences)
        json_match = response
        if "```json" in response:
            json_match = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_match = response.split("```")[1].split("```")[0].strip()

        verifications = json.loads(json_match)

        # Filter findings based on LLM verification
        verified_findings = []
        for v in verifications:
            idx = v["index"] - 1  # Convert to 0-based
            if 0 <= idx < len(findings) and v["real_issue"]:
                finding = findings[idx]
                # Update severity if LLM suggests different
                if "severity" in v:
                    finding.severity = v["severity"]
                verified_findings.append(finding)

        return verified_findings

    except Exception as e:
        # If LLM fails, fallback to regex findings (safer to warn than miss)
        import sys
        print(f"# LLM verification failed: {e}", file=sys.stderr)
        return findings


def format_findings(findings: list[Finding]) -> str:
    """Format findings for Claude context injection."""
    if not findings:
        return ""

    # Group by severity and category
    critical = [f for f in findings if f.severity == "CRITICAL"]
    warnings = [f for f in findings if f.severity == "WARNING"]

    if not critical and not warnings:
        return ""

    output = ["INSTRUCTION: Pre-commit safety check found issues. Tell the user:\n"]
    output.append("\"⚠️  Pre-commit safety check found issues:\n")

    if critical:
        output.append("\n🚨 BLOCKING ISSUES:\n")

        # Group by category
        secrets = [f for f in critical if f.category == "SECRET"]
        debug = [f for f in critical if f.category == "DEBUG"]
        mistakes = [f for f in critical if f.category == "MISTAKE"]

        if secrets:
            output.append("\nSECRETS (will expose credentials!):\n")
            for f in secrets:
                loc = f"line {f.line}" if f.line else "detected"
                output.append(f"  - {f.file}: {f.message} ({loc})\n")

        if debug:
            output.append("\nDEBUG CODE (left in by mistake?):\n")
            for f in debug:
                loc = f"line {f.line}" if f.line else "detected"
                output.append(f"  - {f.file}: {f.message} ({loc})\n")

        if mistakes:
            output.append("\nMISTAKES:\n")
            for f in mistakes:
                loc = f"line {f.line}" if f.line else "detected"
                output.append(f"  - {f.file}: {f.message} ({loc})\n")

    if warnings:
        output.append("\n⚠️  WARNINGS (review recommended):\n")
        for f in warnings:
            loc = f"line {f.line}" if f.line else "detected"
            output.append(f"  - {f.file}: {f.message} ({loc})\n")

    output.append("\nBefore committing:\n")
    output.append("  1. Review and fix these issues\n")
    output.append("  2. If intentional, user can bypass with: git commit --no-verify\n")
    output.append("\nWould you like me to help fix these issues?\"\n")

    return "".join(output)


def main():
    """Main hook entry point - hybrid regex + LLM scanning."""
    # Skip if we're in a hook-spawned session (prevent recursion)
    if is_hook_session():
        sys.exit(0)

    try:
        # Read event from stdin (pre_tool_use event from Claude Code)
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    # Check if this is a commit action
    if not should_scan(event):
        sys.exit(0)

    # Get staged files
    staged_files = get_staged_files()
    if not staged_files:
        # No staged files, let it proceed
        sys.exit(0)

    # Phase 1: Fast regex scan (catches obvious issues in ~10ms)
    all_findings = []

    # Check dangerous filenames
    filenames = [f for f, _ in staged_files]
    all_findings.extend(check_dangerous_files(filenames))
    all_findings.extend(check_large_files(filenames))

    # Scan file contents with regex
    for file, content in staged_files:
        all_findings.extend(scan_for_secrets(file, content))
        all_findings.extend(scan_for_debug(file, content))
        all_findings.extend(scan_for_mistakes(file, content))

    if not all_findings:
        # Clean commit, exit fast
        sys.exit(0)

    # Phase 2: LLM verification (context-aware, filters false positives)
    # Only runs if issues found in Phase 1
    verified_findings = verify_with_llm(all_findings, staged_files)

    # If critical issues found after LLM verification, block
    critical = [f for f in verified_findings if f.severity == "CRITICAL"]

    if critical:
        output = format_findings(verified_findings)
        print(output, flush=True)
        # Exit non-zero to block the commit
        sys.exit(1)

    # If only warnings remain after LLM review, output them but don't block
    if verified_findings:
        output = format_findings(verified_findings)
        print(output, flush=True)

    # Allow commit to proceed
    sys.exit(0)


if __name__ == "__main__":
    main()
