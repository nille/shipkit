# Deps

Audit and update project dependencies. Use when user says "check dependencies", "update deps", "audit packages", "outdated", "security audit", or "upgrade".

## Overview

Analyzes project dependencies for updates, security vulnerabilities, and unused packages. Supports npm/yarn/pnpm, pip/uv, cargo, go modules, and other common package managers.

## Parameters

- **action** (required): What to do — "audit" (default), "update", "outdated", "unused", "security"
- **scope** (optional): Which dependencies — "all" (default), "production", "dev", a specific package name
- **strategy** (optional): For updates — "minor" (default, safe), "major" (includes breaking), "security-only"

## Workflow

### 1. Detect Package Manager

Identify the project's dependency management.

**Constraints:**
- Check for: package.json, pyproject.toml, Cargo.toml, go.mod, Gemfile, build.gradle, pom.xml
- Identify the package manager: npm/yarn/pnpm, pip/uv/poetry, cargo, go, bundler, gradle/maven
- Check for lockfiles (package-lock.json, uv.lock, Cargo.lock, go.sum, etc.)
- Identify the project's minimum supported language version if relevant

### 2. Analyze Dependencies

Run the appropriate analysis based on the action.

**For "audit" / "security":**
- Run the package manager's audit command (npm audit, pip-audit, cargo audit, govulncheck)
- If no built-in audit exists, check dependencies against known vulnerability databases
- Report severity levels: critical, high, medium, low

**For "outdated":**
- Run the package manager's outdated command
- Group results: patch updates, minor updates, major updates
- Note which major updates have breaking changes

**For "unused":**
- Identify dependencies that are declared but not imported in source code
- Check for dependencies only used in config files (babel plugins, eslint plugins, etc.)
- Be conservative — flag as "likely unused" rather than "definitely unused"

**Constraints:**
- You MUST run actual commands, not guess at versions
- Present findings in a clear table format
- For security issues: include CVE IDs and affected version ranges when available

### 3. Recommend Actions

Present a clear action plan.

**Constraints:**
- You MUST present recommendations before making changes:
  ```
  Recommended updates:
    Safe (minor/patch):
    - express: 4.18.2 → 4.19.1 (security fix)
    - lodash: 4.17.20 → 4.17.21 (patch)
    
    Breaking (major):
    - typescript: 4.9.5 → 5.4.2 (major — strict checks added)
    
    Likely unused:
    - moment (no imports found — replaced by date-fns?)
  ```
- Separate safe updates from potentially breaking ones
- For security issues: recommend immediate action with specific fix commands
- Wait for user to select which updates to apply

### 4. Apply Updates

Execute the approved changes.

**Constraints:**
- Apply one update at a time for major version bumps
- Run tests after each major update to catch breakage early
- Update lockfile appropriately
- If tests fail after an update, revert that specific update and report the failure
- Report final state: what was updated, what was skipped, test results

## Examples

### Security Audit

```
User: "check for security issues in our deps"
Agent: [detects npm, runs npm audit]

       "Security audit for package.json:
       
       | Package   | Severity | CVE            | Fix Available |
       |-----------|----------|----------------|---------------|
       | express   | high     | CVE-2024-1234  | 4.19.1        |
       | tar       | medium   | CVE-2024-5678  | 6.2.1         |
       
       Both have fixes available. Apply them?"

User: "yes"
Agent: [runs npm audit fix, runs tests]
       "2 vulnerabilities fixed. All tests passing."
```
