# Architecture Principles

Decision gates and design principles for creating and modifying skills, guidelines, and references.

## Token Budget Awareness

Every piece of content has a context cost:

| Content type | Loaded when | Cost |
|-------------|-------------|------|
| Guidelines rules | Every conversation | HIGH — keep minimal, each rule uses budget every session |
| SKILL.md | On skill invocation | MEDIUM — loaded on demand, but bloated skills slow execution |
| References | When skill reads them | LOW — loaded only when needed |
| Knowledge | Search-triggered | ZERO — only loaded when explicitly searched |

**Decision heuristic:**
- Is this needed in EVERY conversation? → guidelines (be concise)
- Is this needed when running a specific skill? → SKILL.md or its references/
- Is this a detailed reference table, schema, or template? → references/ subdirectory
- Is this project-specific knowledge? → project knowledge

## Guidelines vs Skill vs Reference

### Guidelines (cross-cutting rules)
- Applies to ALL conversations and ALL skills
- Should be behavioral rules, not procedural steps
- Keep each guidelines file focused on one concern
- Total guidelines should be under 5000 tokens

### SKILL.md (procedural workflow)
- Step-by-step instructions for a specific task
- Must include: trigger description, parameters, workflow, examples
- Keep under 300 lines — move details to references/
- Use RFC2119 keywords in constraints (MUST, SHOULD, MAY)

### References (detailed material)
- Templates, schemas, format specifications, decision tables
- One file per topic (don't combine unrelated material)
- Referenced from SKILL.md with "See references/filename.md"
- Not loaded unless the skill explicitly reads them

## Placement Decision Gate

When creating new content, ask in order:

1. **Does it change behavior across all conversations?**
   - Yes → guidelines rule (add to existing file or create new)
   - No → continue

2. **Does it define a workflow for a specific task?**
   - Yes → skill (SKILL.md in skills/ directory)
   - No → continue

3. **Is it detailed reference material for a skill?**
   - Yes → reference (skills/<name>/references/)
   - No → continue

4. **Is it project-specific knowledge?**
   - Yes → project knowledge (<home>/projects/<name>/knowledge/)
   - No → user global knowledge (<home>/knowledge/)

## Trigger Phrase Hygiene

- Every skill MUST have unique trigger phrases
- Check existing skills before adding triggers to avoid collisions
- Trigger phrases should be natural language the user would actually say
- Include 3-5 variations (e.g., "commit", "commit changes", "save my changes")

## Negative Constraint Format

Every negative constraint (MUST NOT, SHOULD NOT) MUST include a "because" clause:

```markdown
- You MUST NOT amend the previous commit because the user's pre-commit
  hooks may have modified it, and amending would include those changes
```

The "because" clause enables judgment in edge cases — without it, the constraint
becomes a blind rule that can't be reasoned about.
