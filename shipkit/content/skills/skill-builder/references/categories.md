# Skill Categories

Where skills live and how they're promoted between categories.

## Categories

### Package Core (`shipkit/content/skills/`)

Skills shipped with shipkit. Battle-tested, generic, maintained by the shipkit project.

**Criteria for core:**
- Generic — useful across projects and developers
- Well-tested — used in multiple real sessions
- No personal data — no project-specific paths, credentials, or preferences
- Follows SOP format — all constraints use RFC2119 keywords

**Examples:** commit, pr, review, test, debug, release

### User Global (`<home>/skills/`)

Personal skills available across all your projects. Created by the user or installed from plugins.

**Default category for new skills.** All user-created skills start here unless explicitly placed elsewhere.

**Criteria:**
- Useful across multiple projects
- May contain personal preferences (but no secrets)
- Overrides core skills of the same name

**Examples:** custom deploy skill, team-specific review checklist

### Project (`<home>/projects/<name>/skills/`)

Skills specific to one project. Override both core and user global skills.

**Criteria:**
- Only useful for this specific project
- May reference project-specific tools, APIs, or conventions
- Overrides core and user skills of the same name

**Examples:** project-specific migration skill, custom build skill

## Promotion Path

```
New skill → User Global (default)
         ↓ (after testing, PII review)
         → Package Core (via PR to shipkit repo)
```

### Promotion Checklist

Before promoting a user skill to core:

1. **PII scan** — no real names, paths, credentials, project-specific data
2. **Generic** — works for any developer, not just your setup
3. **Tested** — used successfully in 3+ real sessions
4. **Format compliant** — follows SOP format, RFC2119 keywords, examples included
5. **No trigger collisions** — trigger phrases don't overlap with existing core skills
6. **Size check** — SKILL.md under 300 lines, detailed material in references/
