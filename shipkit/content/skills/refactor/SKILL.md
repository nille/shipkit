# Refactor

Guided code refactoring with safety checks. Use when user says "refactor", "clean up", "restructure", "extract", "rename across", or "simplify this".

## Overview

Performs targeted refactoring operations with automated verification that behavior is preserved. Supports extract, rename, move, inline, simplify, and restructure operations.

## Parameters

- **target** (required): What to refactor — file path, function name, module, or "this file"
- **operation** (optional): Type of refactoring — "auto" (default, infer from context), "extract", "rename", "move", "inline", "simplify"
- **scope** (optional): How much to change — "minimal" (default), "module", "broad"

## Workflow

### 1. Understand Current State

Analyze the code targeted for refactoring.

**Constraints:**
- You MUST read the entire target file/module, not just the function in question
- Identify all callers and dependents of the code being changed
- Run `grep` / search to find all references across the codebase
- Check for existing tests that cover the target code
- If no tests exist for the target, warn the user before proceeding

### 2. Plan the Refactoring

Design the changes before making them.

**Constraints:**
- You MUST present a refactoring plan to the user before starting:
  ```
  Refactoring plan for src/auth/middleware.ts:
  - Extract token validation into validateToken() (lines 45-78)
  - Move rate limiting logic to src/auth/rate-limit.ts
  - Inline the single-use helper `_checkExpiry` (line 112)
  - Update 3 callers in src/routes/
  ```
- Explain *why* each change improves the code (readability, testability, reuse, etc.)
- Flag any changes that could affect external API contracts
- Wait for user confirmation before proceeding
- For "broad" scope: break the work into atomic commits

### 3. Execute the Refactoring

Make the changes systematically.

**Constraints:**
- Make one logical change at a time — do not mix unrelated refactors
- Update all callers and references for each change
- Preserve all existing behavior — refactoring must not change what the code does
- Update imports, re-exports, and type references
- Do NOT change formatting, add comments, or "improve" code beyond the agreed plan
- Do NOT rename variables or parameters that are part of public APIs without explicit approval

### 4. Verify Behavior Preserved

Confirm nothing broke.

**Constraints:**
- Run the existing test suite — all tests must still pass
- If tests fail, the refactoring introduced a bug — fix it before continuing
- Run type checking if the project uses a type system
- Run the linter if configured
- If no tests exist, explicitly tell the user that behavior preservation is unverified
- Report what was changed: files modified, functions moved/renamed, callers updated

## Examples

### Extract Function

```
User: "refactor the auth middleware, it's doing too much"
Agent: [reads middleware, finds callers, checks tests]

       "Refactoring plan for src/auth/middleware.ts:
       - Extract token validation (lines 45-78) → validateToken()
       - Extract rate limit check (lines 80-95) → checkRateLimit()  
       - Keep middleware as orchestrator calling both
       - Update tests to cover extracted functions directly
       
       This keeps the middleware readable while making the
       validation logic independently testable. Proceed?"

User: "yes"
Agent: [makes changes, runs tests]
       "Refactored. 2 functions extracted, all 12 tests passing."
```
