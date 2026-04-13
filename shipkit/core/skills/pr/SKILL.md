# Pull Request

Create well-described pull requests from the current branch. Use when user says "create pr", "open pr", "pull request", or wants to submit work for review.

## Overview

Analyzes all commits on the current branch (relative to the base branch), generates a descriptive PR title and body, and creates the PR via the GitHub CLI.

## Parameters

- **base** (optional): Base branch to compare against (default: auto-detect main/master)
- **draft** (optional, default: false): Create as draft PR
- **reviewers** (optional): Comma-separated list of reviewer usernames

## Workflow

### 1. Analyze Branch State

Understand what the PR contains.

**Constraints:**
- Run `git log <base>..HEAD --oneline` to see all commits
- Run `git diff <base>...HEAD --stat` for a file-level summary
- Run `git diff <base>...HEAD` to read the actual changes
- Auto-detect the base branch: check for `main`, then `master`, then the default branch from `git remote show origin`
- If the branch has no commits ahead of base, inform user and stop
- Check if the branch is pushed to remote; if not, note that it needs to be pushed

### 2. Generate PR Title and Description

Create a clear, reviewable PR description.

**Title constraints:**
- Under 70 characters
- Imperative mood
- Should describe the overall change, not list individual commits
- If all commits share a type (feat, fix, etc.), use it as prefix

**Description format:**
```markdown
## Summary

Brief description of what this PR does and why.

## Changes

- Bullet points summarizing key changes
- Grouped by area if touching multiple parts

## Test Plan

- How to verify these changes work
- Any manual testing steps needed
```

**Constraints:**
- Read the actual diffs, not just commit messages
- Explain WHY, not just WHAT
- If the PR fixes an issue, include "Fixes #NNN" or "Closes #NNN"
- Mention any breaking changes prominently
- Note any deployment considerations or migration steps

### 3. Push and Create PR

Submit the pull request.

**Constraints:**
- Show the title and description to user before creating
- Ask for confirmation before proceeding
- Push the branch if not already pushed: `git push -u origin <branch>`
- Use `gh pr create` to create the PR
- If `gh` CLI is not available, output the PR description for manual creation
- Apply --draft flag if requested
- Add reviewers if specified

**Command:**
```bash
gh pr create --title "..." --body "..." [--draft] [--reviewer ...]
```

### 4. Report Result

After creating the PR, report:
- PR URL
- PR number
- Any warnings (e.g., CI not configured, no reviewers assigned)

## Examples

### Feature PR

**Branch:** `feat/user-preferences`
**Commits:** 3 commits adding preferences endpoint

**Title:** `Add user preferences API endpoint`

**Body:**
```markdown
## Summary

Adds a new REST endpoint for storing and retrieving user UI preferences
(theme, locale, notification settings). This unblocks the frontend team's
work on the settings page.

## Changes

- New `GET/PUT /api/v1/users/:id/preferences` endpoint
- Preferences database table with migration
- Input validation and error handling
- Integration tests covering CRUD operations

## Test Plan

- Run `make test` — all new tests should pass
- Manual: `curl -X PUT .../preferences -d '{"theme":"dark"}'` then GET to verify
```
