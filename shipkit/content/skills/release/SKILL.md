# Release

Manage releases with version bumping, changelog generation, and tagging. Use when user says "release", "cut a release", "bump version", "prepare release", or "tag a release".

## Overview

Creates a release by analyzing commits since the last tag, generating a changelog, bumping the version, and creating a git tag. Supports SemVer and CalVer versioning schemes.

## Parameters

- **bump** (optional): Version bump type — "patch", "minor", "major", or "auto" (default: "auto")
- **scheme** (optional): Versioning scheme — "semver" (default) or "calver"
- **dry-run** (optional, default: false): Preview the release without making changes

## Workflow

### 1. Check Release Readiness

Verify the repo is in a clean, releasable state.

**Constraints:**
- You MUST check for uncommitted changes: `git status --porcelain`
- You MUST check the current branch — warn if not on main/master
- You MUST find the last release tag: `git describe --tags --abbrev=0` or `git tag --sort=-v:refname | head -1`
- If no previous tags exist, this is the first release — note it and proceed
- You MUST check that CI/tests pass if a test command is available (look for test scripts in package.json, Makefile, etc.)
- If the repo isn't clean, tell user and stop

### 2. Analyze Changes

Understand what's being released.

**Constraints:**
- You MUST run `git log <last-tag>..HEAD --oneline` to see all commits since last release
- You MUST read the actual commit messages and diffs to understand the changes
- Categorize changes using conventional commit types:
  - **Breaking** — breaking changes (look for `BREAKING CHANGE:` or `!` in commits)
  - **Added** — new features (`feat:`)
  - **Fixed** — bug fixes (`fix:`)
  - **Changed** — other notable changes (`refactor:`, `perf:`)
  - **Other** — chores, docs, CI
- If no meaningful changes since last tag, tell user and stop

### 3. Determine Version

Calculate the new version number.

**For SemVer:**
- If `bump` is "auto": breaking → major, feat → minor, fix → patch
- If `bump` is explicit: use the specified bump
- Format: `vMAJOR.MINOR.PATCH`

**For CalVer:**
- Format: `vYYYY.MM.DD` (with `.N` suffix for multiple releases per day)

**Constraints:**
- You MUST show the user: current version → new version
- You MUST NOT proceed without confirmation

### 4. Generate Changelog

Create a human-readable changelog entry.

**Format:**
```markdown
## [vX.Y.Z] — YYYY-MM-DD

### Breaking
- Description of breaking change

### Added
- Description of new feature

### Fixed
- Description of bug fix

### Changed
- Description of other change
```

**Constraints:**
- Write changelog entries as human-readable descriptions, not raw commit messages
- Group related commits into single entries
- Omit chore/CI commits unless they affect users
- If a CHANGELOG.md exists, prepend the new entry
- If no CHANGELOG.md exists, ask user if they want one created
- Show the changelog to user for review before writing

### 5. Apply Release

Execute the version bump and tag.

**Constraints:**
- Update version in the appropriate file(s):
  - `package.json` (Node.js)
  - `pyproject.toml` / `setup.py` / `__init__.py` (Python)
  - `Cargo.toml` (Rust)
  - `go.mod` or version constant (Go)
  - Ask user if unsure which file holds the version
- Write the changelog entry
- Stage and commit: `git add -A && git commit -m "release: vX.Y.Z"`
- Create annotated tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
- Do NOT push automatically — ask user first

### 6. Publish

Push the release if requested.

**Constraints:**
- Ask user: "Push tag and commit to origin?"
- If yes: `git push origin main && git push origin vX.Y.Z`
- If a GitHub release is desired: `gh release create vX.Y.Z --title "vX.Y.Z" --notes "<changelog>"`
- Report the release URL

## Examples

### Auto-Detected SemVer Release

```
User: "cut a release"
Agent: [checks status, finds last tag v1.2.0, reads commits]

       "Since v1.2.0, there are 8 commits:
       - 2 features (feat)
       - 3 fixes
       - 3 chores
       
       Auto-detected bump: minor (new features, no breaking changes)
       v1.2.0 → v1.3.0
       
       Changelog:
       ## [v1.3.0] — 2026-04-12
       
       ### Added
       - User preferences API endpoint
       - Dark mode support in settings page
       
       ### Fixed
       - Token refresh no longer fails on expired sessions
       - CSV export handles unicode correctly
       - Pagination off-by-one on last page
       
       Look good?"

User: "ship it"
Agent: [updates version, writes changelog, commits, tags]
       "Tagged v1.3.0. Push to origin?"
```
