# CI

Set up or troubleshoot CI/CD pipelines. Use when user says "set up ci", "fix the pipeline", "add github action", "ci is failing", "add a workflow", or "deploy pipeline".

## Overview

Creates, modifies, and troubleshoots CI/CD pipelines. Supports GitHub Actions, GitLab CI, CircleCI, and other common CI systems. Can create new pipelines from project analysis or debug failing ones.

## Parameters

- **action** (required): What to do — "create" (new pipeline), "fix" (debug failures), "add" (add a step/job), "optimize" (speed up)
- **platform** (optional): CI platform — auto-detect from existing config, or "github-actions" (default), "gitlab-ci", "circleci"
- **target** (optional): Specific workflow or job to modify

## Workflow

### 1. Analyze Project

Understand what the CI pipeline needs to do.

**For "create":**
- Detect language, framework, package manager, and build system
- Identify test commands from package.json scripts, Makefile, pyproject.toml, etc.
- Check for linters, formatters, type checkers that should run in CI
- Identify deployment targets if any (Vercel, AWS, GCP, Docker, etc.)

**For "fix":**
- Read the failing workflow/job configuration
- Check recent CI run logs: `gh run list` and `gh run view <id> --log-failed`
- Identify the specific step that failed and why
- Check if the failure is in the pipeline config or in the code

**For "add" / "optimize":**
- Read the existing pipeline configuration completely
- Understand the current job structure and dependencies

**Constraints:**
- You MUST read existing CI config files before modifying them
- Check for existing .github/workflows/, .gitlab-ci.yml, .circleci/config.yml

### 2. Plan Changes

Design the pipeline changes.

**Constraints:**
- You MUST present the plan before making changes:
  ```
  CI pipeline plan (.github/workflows/ci.yml):
  Jobs:
  1. lint — run ruff check + ruff format --check
  2. typecheck — run mypy
  3. test — run pytest (matrix: py3.10, py3.11, py3.12)
  4. build — build wheel (depends on lint + test)
  
  Triggers: push to main, all PRs
  ```
- For new pipelines: start simple — lint, test, build. Don't over-engineer
- For fixes: explain the root cause before proposing the fix
- For optimization: show estimated time savings
- Wait for user confirmation before writing

### 3. Implement

Write or modify the pipeline configuration.

**Constraints:**
- Use the CI platform's latest stable action versions (e.g., actions/checkout@v4, actions/setup-node@v4)
- Pin action versions to major tags, not `@main` or `@latest`
- Cache dependencies (npm cache, pip cache, etc.) for faster runs
- Use matrix builds for multi-version testing only when the project actually supports multiple versions
- Set appropriate timeouts to prevent stuck jobs
- For secrets: use the platform's secret management — never hardcode credentials
- For GitHub Actions: use `permissions` to scope token access

### 4. Verify

Confirm the pipeline is valid.

**Constraints:**
- For GitHub Actions: validate YAML syntax and check for common mistakes (wrong indentation, missing `uses:`, typos in event names)
- If `actionlint` is available, run it
- If fixing a broken pipeline: confirm the fix addresses the specific error
- Suggest the user push and monitor the first run
- Report what was created/changed

## Examples

### Create Pipeline

```
User: "set up ci for this project"
Agent: [detects Python project with pytest, ruff, mypy]

       "CI pipeline plan (.github/workflows/ci.yml):
       Jobs:
       1. lint — ruff check + ruff format --check
       2. typecheck — mypy src/
       3. test — pytest (Python 3.11, 3.12)
       
       Triggers: push to main, pull requests
       Caching: uv cache for fast installs
       
       Create this?"

User: "yes"
Agent: [creates .github/workflows/ci.yml]
       "Pipeline created. Push to trigger the first run."
```

### Fix Failing Pipeline

```
User: "ci is failing, can you fix it?"
Agent: [runs gh run list, finds failing run, reads logs]

       "The 'test' job is failing in the 'Install dependencies' step:
       
         error: No matching version for package 'cryptography>=42.0'
         (Python 3.9 wheels not available)
       
       Root cause: cryptography 42.x dropped Python 3.9 support,
       but your CI matrix still includes 3.9.
       
       Options:
       1. Drop Python 3.9 from the matrix (it's EOL Oct 2025)
       2. Pin cryptography<42 for the 3.9 job
       
       Which approach?"
```
