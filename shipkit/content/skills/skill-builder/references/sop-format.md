# SOP Format

Standard Operating Procedure format for SKILL.md files.

## Structure

```markdown
# Skill Title

One-line description with trigger phrases. Use when user says "X", "Y", or "Z".

## Overview

2-3 sentences explaining what this skill does and when to use it.

## Parameters

- **param_name** (required|optional): Description and allowed values

## Workflow

### 1. Step Name

Natural language description of what this step does.

**Constraints:**
- You MUST do X
- You SHOULD do Y
- You MAY do Z
- You MUST NOT do W because [reason]

### 2. Next Step

...

## Examples

### Example Title

\```
User: "trigger phrase with context"
Agent: [actions taken]
       "response to user"
\```
```

## Rules

### Required Sections

Every SKILL.md MUST include:
1. **Title line** (`# Skill Name`) — used as display name in skill catalog
2. **Trigger description** — first paragraph, includes trigger phrases
3. **Overview** — brief explanation
4. **Parameters** — inputs with (required)/(optional) annotations
5. **Workflow** — numbered steps with constraints
6. **Examples** — at least one realistic example

### Constraint Keywords

Use RFC2119 keywords consistently:

| Keyword | Meaning |
|---------|---------|
| MUST | Absolute requirement — violation is a bug |
| MUST NOT | Absolute prohibition — always include "because [reason]" |
| SHOULD | Strong recommendation — can be overridden with good reason |
| SHOULD NOT | Discouraged — explain why |
| MAY | Optional behavior — document when it's useful |

### Step Format

Each workflow step has:
1. **Heading** — `### N. Step Name` (imperative verb, e.g., "Gather Changes")
2. **Description** — 1-3 sentences explaining the goal
3. **Constraints block** — `**Constraints:**` followed by bulleted rules

### Example Format

Examples should be realistic conversations:
- Show the user's trigger phrase with enough context
- Show the agent's key actions in brackets
- Show the agent's response in quotes
- Keep examples concise — show the flow, not every detail
