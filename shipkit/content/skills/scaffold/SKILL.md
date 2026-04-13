# Scaffold

Generate project structure and boilerplate. Use when user says "scaffold", "create a new", "bootstrap", "init a", "set up a new", or "generate boilerplate".

## Overview

Creates new projects, modules, components, or services with appropriate boilerplate following the project's existing conventions. Detects patterns from the codebase and replicates them.

## Parameters

- **type** (required): What to scaffold — "project", "module", "component", "service", "endpoint", "model", or a custom type
- **name** (required): Name for the scaffolded item
- **template** (optional): Specific template or pattern to follow (e.g., "rest-api", "cli-tool", "react-component")

## Workflow

### 1. Detect Conventions

Understand the project's existing patterns.

**Constraints:**
- Identify the project's language, framework, and build system
- Find existing examples of the type being scaffolded (e.g., existing components, modules, services)
- Analyze naming conventions (PascalCase, kebab-case, snake_case for files and directories)
- Check for generator configs (plop, hygen, cookiecutter, etc.) already in the project
- Identify the test pattern — where tests live, naming convention, what's tested by default

### 2. Plan the Structure

Design what will be created.

**Constraints:**
- You MUST present the planned file structure before creating anything:
  ```
  Will create:
    src/services/payment/
    ├── payment.service.ts     (main service class)
    ├── payment.types.ts       (interfaces and types)
    ├── payment.repository.ts  (data access)
    ├── index.ts               (barrel export)
    └── __tests__/
        └── payment.service.test.ts
  ```
- Follow existing project structure exactly — don't introduce new patterns
- If the project has no existing examples of this type, ask the user for guidance
- Wait for user confirmation before creating files

### 3. Generate Files

Create the scaffolded code.

**Constraints:**
- Match the style of existing code in the project (imports, exports, error handling patterns)
- Include TODO comments for business logic the user needs to fill in
- Wire up the new code: add to barrel exports, register routes, update module imports
- Include a basic test file that imports the new code and has a placeholder test
- Do NOT add dependencies unless explicitly needed and approved by the user

### 4. Verify Integration

Confirm the scaffolded code integrates cleanly.

**Constraints:**
- Run type checking / compilation to confirm no import errors
- Run the test suite to confirm nothing broke and the new placeholder test passes
- Report what was created and what the user needs to do next

## Examples

### New Service Module

```
User: "scaffold a payment service"
Agent: [finds existing services, analyzes patterns]

       "Based on your existing services (user, order), I'll create:
         src/services/payment/
         ├── payment.service.ts
         ├── payment.types.ts
         ├── payment.repository.ts
         ├── index.ts
         └── __tests__/payment.service.test.ts
       
       Following the same pattern as src/services/order/. Proceed?"

User: "yes"
Agent: [creates files, wires up exports]
       "Payment service scaffolded. TODOs marked for business logic.
        Run `npm test` — placeholder test passing."
```
