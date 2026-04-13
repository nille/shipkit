# Test

Generate tests for specified code. Use when user says "test this", "write tests", "add tests for", "generate tests", or "cover this with tests".

## Overview

Analyzes code and generates appropriate tests. Detects the project's test framework and conventions, then produces tests that follow existing patterns.

## Parameters

- **target** (required): What to test — file path, function name, or "recent changes"
- **type** (optional): Test type — "unit" (default), "integration", "e2e"
- **coverage** (optional): What to cover — "happy-path" (default), "edge-cases", "comprehensive"

## Workflow

### 1. Detect Test Setup

Understand the project's testing conventions.

**Constraints:**
- Identify the test framework (jest, pytest, go test, vitest, mocha, etc.) from config files and existing tests
- Find existing test files to understand naming conventions and patterns
- Check for test utilities, fixtures, mocks, or factories already in the project
- Identify assertion style (expect, assert, should, etc.)
- If no test setup exists, suggest one and ask before proceeding

### 2. Analyze Target Code

Understand what needs to be tested.

**Constraints:**
- You MUST read the target code completely
- Identify all public functions/methods and their signatures
- Identify input types, return types, and side effects
- Identify error conditions and edge cases
- Identify dependencies that may need mocking
- If target is "recent changes", run `git diff` to find changed code

### 3. Plan Test Cases

Design the test structure before writing.

**Constraints:**
- For happy-path: cover the main success scenarios for each function
- For edge-cases: add boundary values, empty inputs, null/undefined, error paths
- For comprehensive: all of the above plus concurrent access, large inputs, type coercion
- Group tests logically (by function, by scenario, by behavior)
- You MUST present the test plan to the user before writing:
  ```
  Tests for src/auth/login.ts:
  - login() — valid credentials → returns token
  - login() — invalid password → throws AuthError
  - login() — expired account → throws AccountExpiredError
  - login() — rate limited → throws RateLimitError
  ```
- Wait for user confirmation before generating

### 4. Generate Tests

Write the test code.

**Constraints:**
- Follow the project's existing test patterns exactly (describe/it, test(), func TestX, etc.)
- Use existing test utilities and fixtures from the project
- Mock only external dependencies (APIs, databases, file system) — not internal modules unless necessary
- Each test should be independent and self-contained
- Use descriptive test names that explain the expected behavior
- Include setup and teardown if needed
- Place test file according to project convention (co-located, `__tests__/`, `tests/`, etc.)

### 5. Verify Tests Run

Confirm the tests work.

**Constraints:**
- Run the test suite and verify all new tests pass
- If tests fail, diagnose and fix — do not present failing tests as complete
- Report test count and pass/fail status

## Examples

### Unit Tests

```
User: "write tests for src/utils/slug.ts"
Agent: [reads file, detects vitest, finds existing test patterns]

       "Test plan for slug.ts:
       - slugify() — basic string → kebab-case
       - slugify() — special characters stripped
       - slugify() — unicode transliterated
       - slugify() — empty string → empty string
       - slugify() — already a slug → unchanged
       
       Generate these?"

User: "yes"
Agent: [writes tests following project's vitest patterns]
       [runs tests — all pass]
       "5 tests written in src/utils/slug.test.ts, all passing."
```
