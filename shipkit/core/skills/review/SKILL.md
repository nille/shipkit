# Code Review

Review code changes for bugs, design issues, and improvements. Use when user says "review", "review this", "code review", "check my changes", or "review PR #N".

## Overview

Performs a structured code review of local changes, a specific commit, or a pull request. Focuses on correctness, security, maintainability, and adherence to project conventions.

## Parameters

- **target** (optional): What to review. One of:
  - `local` (default) — unstaged/staged changes in the working tree
  - `staged` — only staged changes
  - `commit:<sha>` — a specific commit
  - `pr:<number>` — a GitHub pull request
  - `branch:<name>` — diff of branch against its base
- **focus** (optional): Narrow the review scope (e.g., "security", "performance", "naming")

## Workflow

### 1. Gather Changes

Get the diff to review.

**Constraints:**
- For `local`: run `git diff` (unstaged) and `git diff --staged` (staged)
- For `staged`: run `git diff --staged` only
- For `commit:<sha>`: run `git show <sha>`
- For `pr:<number>`: run `gh pr diff <number>`
- For `branch:<name>`: run `git diff main...<name>` (auto-detect base)
- If no changes found, tell user and stop
- You MUST read the full diff, not just file names

### 2. Understand Context

Read surrounding code to understand the changes in context.

**Constraints:**
- For each modified file, read enough surrounding code to understand the change's impact
- Check for related test files — are tests added/updated for the changes?
- Look at recent commits on the same files for context on conventions
- Identify the project's language, framework, and testing patterns

### 3. Review

Analyze the changes systematically.

**Check for:**
- **Correctness** — logic errors, off-by-one, null/undefined handling, race conditions
- **Security** — injection vulnerabilities, auth gaps, secrets in code, unsafe deserialization
- **Error handling** — missing error cases, swallowed exceptions, unclear error messages
- **Naming and clarity** — misleading names, unclear intent, magic values
- **Duplication** — code that duplicates existing utilities or patterns in the codebase
- **Test coverage** — are new code paths tested? Are edge cases covered?
- **Performance** — unnecessary allocations, N+1 queries, missing indexes (only if obvious)
- **Breaking changes** — API contract changes, removed exports, changed return types

**Constraints:**
- You MUST read the actual code, not just describe what you'd check
- You MUST categorize findings by severity:
  - **Must fix** — bugs, security issues, data loss risks
  - **Should fix** — design problems, missing error handling, poor naming
  - **Consider** — style improvements, minor optimizations, alternative approaches
- You MUST provide specific line references for each finding
- You MUST NOT nitpick formatting if a formatter/linter is configured
- If the code looks good, say so — don't manufacture issues

### 4. Present Review

Format the review clearly.

**Format:**
```markdown
## Review: <what was reviewed>

### Summary
<1-2 sentences: overall assessment>

### Must Fix
- **[file:line]** Description of issue and why it matters
  ```suggestion
  suggested fix
  ```

### Should Fix
- **[file:line]** Description and recommendation

### Consider
- **[file:line]** Optional improvement

### What Looks Good
- <positive observations — acknowledge good patterns>
```

**Constraints:**
- Lead with the most important findings
- Include fix suggestions for must-fix items
- Keep the review actionable — every finding should have a clear next step
- If reviewing a PR, ask if user wants to post the review as a PR comment via `gh`

## Examples

### Local Changes Review

```
User: "review my changes"
Agent: [runs git diff, reads context]

       "## Review: auth middleware changes

       ### Summary
       Adds token refresh logic. Looks solid overall, one bug and
       a missing error case.

       ### Must Fix
       - **src/auth/refresh.ts:42** — refresh token is compared
         with `==` instead of timing-safe comparison. Use
         `crypto.timingSafeEqual()` to prevent timing attacks.

       ### Should Fix
       - **src/auth/refresh.ts:58** — if the refresh endpoint
         returns 401, the error is swallowed silently. Should
         redirect to login.

       ### What Looks Good
       - Clean separation of refresh logic from the main auth flow
       - Good use of the existing `TokenStore` abstraction"
```
