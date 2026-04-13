# Git Commit

Create meaningful git commits by analyzing actual changes. Use when user says "commit", "commit this", "commit changes", or wants to save work to git.

## Overview

Creates well-structured git commits by first analyzing the actual changes, then generating a meaningful commit message. Follows conventional commit format.

## Parameters

- **scope** (optional): Override auto-detected scope (e.g., "api", "frontend")
- **amend** (optional, default: false): Amend the previous commit instead of creating new

## Workflow

### 1. Check Repository State

Understand what needs to be committed.

**Constraints:**
- You MUST run `git status --short` to see changed files
- You MUST run `git diff` for unstaged changes or `git diff --staged` for staged changes
- You MUST determine committable files from the actual working tree state — NEVER infer from conversation history or memory of what was changed earlier in the session
- If no changes exist, inform user and stop
- Note if there are both staged and unstaged changes
- Before any `git stash`, `git checkout`, or `git reset`: list all modified/untracked files and warn the user which files would be at risk of loss

### 2. Analyze Changes

Understand the nature and purpose of the changes.

**Constraints:**
- You MUST read the actual diff content, not just file names
- You MUST identify:
  - What type of change (feat, fix, refactor, docs, chore, style, test)
  - What scope/area is affected
  - What the changes actually do (not just "updated X")
  - Why the changes matter (the impact)
- You MUST NOT generate a commit message without reading the diff
- Group related changes conceptually
- When a commit renames or deletes a file, grep the old filename/path across tracked files before committing. Flag stale references and fix them in the same commit.
- Verify all staged/changed files belong to the same logical change. If unrelated files are present, flag them for exclusion before committing.

### 3. Generate Commit Message

Create a meaningful commit message following conventional format.

**Format:**
```
type(scope): concise summary (imperative mood, <50 chars)

- Bullet points explaining what changed and why
- Focus on the "what" and "why", not the "how"
- Each bullet should be a complete thought
```

**Types:**
- `feat`: New feature or capability
- `fix`: Bug fix
- `refactor`: Code restructuring without behavior change
- `docs`: Documentation only (README, guides, comments)
- `chore`: Maintenance, dependencies, config
- `style`: Formatting, no code change
- `test`: Adding or updating tests

**Constraints:**
- You MUST use imperative mood ("Add feature" not "Added feature")
- You MUST keep subject line under 50 characters
- You MUST include body with bullet points for non-trivial changes
- You MUST explain WHY the change was made — what problem it solves or what was broken/missing before
- For `feat` and `refactor` commits, the body MUST start with a 1-2 sentence summary paragraph before bullet points
- Auto-detect scope from changed paths
- NEVER use generic messages like "Update files" or "Fix stuff"

### 4. Stage and Commit

Execute the commit.

**Constraints:**
- If changes are unstaged, ask user which files to stage
- You MAY suggest `git add -A` if all changes are related
- Show the commit message to user before committing
- Ask for confirmation before executing
- If amend is true, use `git commit --amend`
- When the user requests a content refinement to something just committed (same logical change, same files), prefer `git commit --amend` over a new commit
- Re-run `git diff` before committing to verify all changes are as expected

## Examples

### Simple Commit

**Changes:** Modified `src/auth/login.ts`

**Message:**
```
fix(auth): handle expired refresh tokens gracefully

- Return to login screen instead of showing a blank page
- Clear stale session data on token expiry
```

### Multi-file Commit

**Changes:** New API endpoint, updated tests, migration file

**Message:**
```
feat(api): add user preferences endpoint

Allows users to store and retrieve UI preferences (theme, locale,
notifications) via a new REST endpoint.

- Add GET/PUT /api/v1/users/:id/preferences
- Add preferences table migration
- Add integration tests for preference CRUD
```
