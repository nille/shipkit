# Retro-Auto Rules

Classification and promotion logic for the autonomous learning loop.

## Classification: Learnable vs Structural

### Learnable Rule (auto-promote to user content)

A rule is learnable if ALL of these are true:
- Single-sentence behavioral constraint
- Changes a default, output format, or decision heuristic
- The agent can apply it just by reading it at load time
- No code changes or workflow step modifications needed

**Examples:**
- "Always use conventional commit format" → learnable
- "Prefer tabs over spaces in this project" → learnable
- "Default to brief responses, skip trailing summaries" → learnable

### Structural Change (stays in pending for manual triage)

A change is structural if ANY of these are true:
- Requires adding/modifying workflow steps in a SKILL.md
- Involves new error handling or safety gates
- Changes tool invocation patterns or command sequences
- Requires reading additional context (files, APIs) to apply

**Examples:**
- "Add a step to check for monorepo before committing" → structural
- "Handle the case where gh CLI is not installed" → structural

## Promotion Thresholds

| Severity | Required occurrences | Rationale |
|----------|---------------------|-----------|
| high | 1x | Critical issues — user corrections, data loss risk |
| medium | 2x | Recurring patterns — needs confirmation it's persistent |
| low | 3x | Nice-to-haves — only promote if clearly persistent |

## Promotion Destinations

### Cross-cutting rules → `<home>/steering/auto-learned.md`

For rules that apply across all skills and conversations:
- Response style preferences
- General behavioral rules
- Default tool/framework choices

### Skill-specific rules → `<home>/skills/<skill-name>/learned.md`

For rules that only apply when using a specific skill:
- Commit message format preferences
- Test framework choices
- Review focus areas

## File Format

Both file types use the same structure:

```markdown
---
description: "Brief description of what this file contains"
---

# [Title]

## Customizations
<!-- User-maintained. Retro-auto does NOT touch this section. -->

[User's manually added rules go here]

## Auto-Learned
<!-- Auto-maintained by retro-auto. Token budget: [limit]. -->

- Rule text (Nx — where N is occurrence count)
- Another rule (Mx)
```

**Section contract:**
- `## Customizations` — user-owned, retro-auto NEVER modifies
- `## Auto-Learned` — retro-auto-owned, subject to consolidation

## Consolidation

Consolidation runs periodically (every 7 days, tracked by `<home>/.state/retro/.last-consolidated`).

During consolidation:
1. Group related rules in Auto-Learned sections
2. Merge duplicates (combine occurrence counts)
3. Remove rules that conflict with Customizations (user's intent takes precedence)
4. Enforce token budgets:
   - `steering/auto-learned.md` Auto-Learned: 3000 tokens max
   - `skills/*/learned.md` Auto-Learned: 1000 tokens max
5. If over budget: drop lowest-occurrence rules first
6. Verify no rules were accidentally dropped (count before and after)
