# Skill Format Specification

Technical specification for how skills are discovered, loaded, and executed.

## File Structure

```
<skills-dir>/<skill-name>/
├── SKILL.md           # Main skill definition (required)
├── references/        # Detailed reference material (optional)
│   ├── templates.md
│   ├── schemas.md
│   └── ...
└── scripts/           # Executable scripts (optional, rare)
```

## Discovery

Skills are discovered by directory name in three layers (lowest → highest precedence):

1. **Package core:** `shipkit/content/skills/<name>/SKILL.md`
2. **User global:** `<home>/skills/<name>/SKILL.md`
3. **Project:** `<home>/projects/<project>/skills/<name>/SKILL.md`

Higher layers override lower layers by directory name. A user skill named "commit" replaces the package's commit skill entirely.

## Compilation

When `shipkit sync` runs:

- **Claude Code:** SKILL.md copied to `.claude/commands/<name>.md` (becomes a `/name` slash command)
- **Kiro:** SKILL.md copied to `.kiro/skills/<name>/SKILL.md`
- **References:** Copied alongside the skill (`.claude/commands/<name>-references/` or `.kiro/skills/<name>/references/`)

## Skill Catalog

The CLAUDE.md managed section includes a skill catalog generated from the first line of each SKILL.md:

```markdown
## Available Skills
- **/commit** — Git Commit
- **/review** — Code Review
```

The title is extracted from the `# Title` line of SKILL.md.

## Naming Conventions

- **Directory name:** kebab-case (e.g., `skill-builder`, `git-commit`)
- **Slash command:** matches directory name (e.g., `/skill-builder`)
- **SKILL.md title:** Title Case (e.g., `# Skill Builder`)
- **References:** kebab-case filenames (e.g., `sop-format.md`)
