# Common Skill Patterns

Reusable patterns for skill authors.

## Confirm Before Acting

When a skill will make changes, always present a plan and wait for confirmation:

```markdown
### N. Plan the Changes

**Constraints:**
- You MUST present the plan to the user before making changes:
  \```
  Plan:
  - Change A (file:line)
  - Change B (file:line)
  \```
- Wait for user confirmation before proceeding
```

## Progressive Disclosure

For skills that can operate at different detail levels:

```markdown
## Parameters

- **depth** (optional): "quick" (default), "standard", "thorough"
```

Quick shows only essential output. Standard adds context. Thorough shows everything.

## Iterative Drafting

For skills that produce content the user may want to refine:

```markdown
### N. Generate Draft

**Constraints:**
- Present the draft to the user
- Ask: "Looks good, or would you like changes?"
- Iterate until the user confirms
- Do NOT make changes beyond what the user requests
```

## Detect-Then-Act

For skills that need to adapt to project conventions:

```markdown
### 1. Detect Conventions

Understand the project's existing patterns.

**Constraints:**
- Check for config files (package.json, pyproject.toml, etc.)
- Find existing examples of what you're about to create
- Match naming conventions, style, and patterns
- If no examples exist, ask the user for guidance
```

## Batch Processing

For skills that process multiple items:

```markdown
### N. Process Items

**Constraints:**
- Process items one at a time
- Report progress: "Processing 3/10..."
- If one item fails, continue with the rest
- Report summary at the end: N succeeded, M failed
```

## Verification Step

Every skill that makes changes should verify the result:

```markdown
### N. Verify

**Constraints:**
- Run tests / type checking / linter as appropriate
- If verification fails, fix the issue before reporting success
- Report final state to the user
```
