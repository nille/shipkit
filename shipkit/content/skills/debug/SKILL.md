# Debug

Systematic debugging workflow. Use when user says "debug this", "fix this bug", "why is this failing", "it's broken", or describes unexpected behavior.

## Overview

Guides a structured debugging process: reproduce the issue, isolate the cause, fix it, and verify the fix. Prevents the common trap of guessing at solutions without understanding the root cause.

## Parameters

- **symptom** (required): What's going wrong — error message, unexpected behavior, or failing test
- **context** (optional): Where it happens — file, endpoint, action, environment

## Workflow

### 1. Understand the Symptom

Get the full picture before investigating.

**Constraints:**
- Read any error messages or stack traces completely
- Ask for reproduction steps if not provided
- Identify: what's expected vs. what's actually happening
- Check if this is a regression: `git log --oneline -20` to see recent changes
- Do NOT propose fixes yet — understand first

### 2. Reproduce

Confirm the issue is reproducible.

**Constraints:**
- If there's a failing test, run it: confirm it actually fails
- If it's a runtime issue, identify the minimal reproduction path
- If you can't reproduce, say so — debugging without reproduction is guesswork
- Record the exact error output for reference

### 3. Isolate

Narrow down the root cause.

**Strategies (try in order):**
1. **Read the stack trace** — follow the call chain to the origin
2. **Check recent changes** — `git diff` and `git log` for changes in the affected area
3. **Add instrumentation** — strategic log statements or debugger breakpoints
4. **Binary search** — if the cause isn't obvious, use `git bisect` to find the introducing commit
5. **Simplify** — remove complexity until the bug disappears, then add back to find the trigger

**Constraints:**
- You MUST identify the root cause before proposing a fix
- You MUST explain the causal chain: what triggers the bug, why it manifests the way it does
- If the root cause is in a dependency, identify the exact version and known issue
- If multiple potential causes exist, rank them by likelihood

### 4. Fix

Apply the minimal correct fix.

**Constraints:**
- Fix the root cause, not the symptom
- The fix should be the smallest change that resolves the issue
- Do NOT refactor surrounding code as part of a bug fix
- If the fix requires a design change, explain the trade-off and get approval
- Show the fix to the user before applying

### 5. Verify

Confirm the fix works and doesn't break anything.

**Constraints:**
- Re-run the reproduction from step 2 — confirm it passes
- Run the project's test suite — confirm no regressions
- If the bug was in an edge case, add a test covering that case
- Check for similar patterns elsewhere in the codebase that might have the same bug

### 6. Report

Summarize what happened.

**Format:**
```markdown
## Bug: <one-line description>

**Symptom:** <what was happening>
**Root cause:** <why it was happening>
**Fix:** <what was changed>
**Verification:** <how we confirmed it's fixed>
**Regression risk:** <low/medium/high — what could break>
```

## Examples

### Runtime Error

```
User: "the API returns 500 on /users/:id when the user has no avatar"
Agent: [reads the error log]
       "Stack trace points to src/api/users.ts:84 — `avatar.url` is 
       accessed without null check. Let me verify..."
       
       [reads the code, confirms avatar can be null]
       
       "Root cause: `formatUser()` at line 84 assumes `user.avatar` 
       is always present, but it's nullable in the schema. When a 
       user has no avatar, `avatar.url` throws TypeError.
       
       Fix: add optional chaining — `user.avatar?.url ?? null`
       
       Want me to apply this?"
```
