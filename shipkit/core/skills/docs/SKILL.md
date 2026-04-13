# Docs

Generate or update documentation. Use when user says "document", "write docs", "update readme", "add docstrings", "generate api docs", or "explain this in the readme".

## Overview

Creates or updates documentation from code — READMEs, API docs, inline docstrings, architecture docs, and usage guides. Reads the actual code to produce accurate documentation.

## Parameters

- **target** (required): What to document — file path, module name, "api", "readme", or "architecture"
- **type** (optional): Documentation type — "readme", "api", "inline", "guide", "architecture"
- **audience** (optional): Who the docs are for — "users" (default), "contributors", "internal"

## Workflow

### 1. Analyze What Exists

Understand current documentation state.

**Constraints:**
- Check for existing README, docs/, CONTRIBUTING.md, API docs
- Read the actual source code to understand what needs documenting
- Identify public APIs, exported functions, CLI commands
- Check for existing docstrings/JSDoc and their completeness
- For README updates: read the existing README first to understand its structure

### 2. Plan Documentation

Decide what to write and where.

**Constraints:**
- You MUST present the documentation plan before writing:
  ```
  Documentation plan:
  - Update README.md: add "Configuration" section, update CLI usage
  - Add docstrings to 5 exported functions in src/api/
  - Create docs/deployment.md (new)
  ```
- Don't duplicate information — link to existing docs where possible
- Match the existing documentation style (formal vs. casual, terse vs. detailed)
- Wait for user confirmation before writing

### 3. Generate Documentation

Write the documentation.

**Constraints:**
- You MUST read the source code to write accurate docs — never guess at behavior
- Include working code examples by testing them or extracting from existing tests
- For API docs: document parameters, return types, errors, and side effects
- For READMEs: include quick start, installation, basic usage, and configuration
- Do NOT add documentation for internal/private code unless asked
- Do NOT use placeholder text like "TODO: describe this" — if you can't determine the behavior, say so
- Keep docs concise — prefer examples over lengthy explanations

### 4. Verify Accuracy

Confirm documentation matches code.

**Constraints:**
- Cross-check every documented function signature against the actual code
- Verify code examples compile/run if possible
- Check that documented CLI flags and options match the actual implementation
- If you find discrepancies between existing docs and code, flag them to the user

## Examples

### Update README

```
User: "update the readme with the new CLI commands"
Agent: [reads README, reads CLI source code]

       "Documentation plan:
       - Add 3 new commands to the CLI Reference section:
         shipkit template create, shipkit doctor, shipkit run
       - Update the Quick Start to mention templates
       - Fix: README says --verbose flag exists but CLI doesn't have it
       
       Proceed?"

User: "yes"
Agent: [updates README sections]
       "README updated. Added 3 commands, updated Quick Start,
        removed reference to non-existent --verbose flag."
```
