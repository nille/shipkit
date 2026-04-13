# Skill Discovery and Cascading

**CRITICAL INSTRUCTION:** Skills are discovered dynamically from multiple locations. You must follow these discovery rules to find and execute skills correctly.

## Skill Discovery Locations

When a user mentions a skill (e.g., `/commit`, `/deploy`), check these locations **in this specific order** (highest precedence first):

### 1. Project Skills (Highest Precedence)
```
.claude/skills/*/SKILL.md       (for Claude Code)
.kiro/skills/*/SKILL.md         (for Kiro)
.gemini/skills/*/SKILL.md       (for Gemini CLI)
.opencode/skills/*/SKILL.md     (for OpenCode)
```
**Purpose:** Team-shared skills committed to the project repo.

### 2. User Personal Skills
```
~/.claude/skills/*/SKILL.md     (for Claude Code)
~/.kiro/skills/*/SKILL.md       (for Kiro)
~/.gemini/skills/*/SKILL.md     (for Gemini CLI)
~/.opencode/skills/*/SKILL.md   (for OpenCode)
```
**Purpose:** Your personal skills across all projects.

### 3. Plugin Skills
```
~/.config/shipkit/plugins/*/skills/*/SKILL.md
```
**Purpose:** Skills from installed marketplace plugins.

### 4. Package Core Skills (Lowest Precedence)
```
~/.config/shipkit/core/skills/*/SKILL.md
```
**Purpose:** Built-in skills shipped with shipkit.

## Discovery Process

When user mentions `/skillname`:

1. **Glob for the skill** in all locations:
   ```
   Use Glob tool to search:
   - .claude/skills/skillname/SKILL.md
   - ~/.claude/skills/skillname/SKILL.md
   - ~/.config/shipkit/plugins/*/skills/skillname/SKILL.md
   - ~/.config/shipkit/core/skills/skillname/SKILL.md
   ```

2. **Read all found instances** (may be in multiple locations)

3. **Apply cascading logic** (see below)

4. **Execute the resulting merged content**

## Cascading Logic

Skills support composition via the `extends` field in YAML frontmatter.

### Parsing Frontmatter

Each SKILL.md may have YAML frontmatter:
```yaml
---
name: commit
description: Git commit workflow
extends: true  # or false
---

# Skill content below
```

### Cascading Rules

**If highest precedence layer has `extends: false`:**
- Use ONLY that layer
- Ignore all lower precedence layers
- No merging

**Otherwise (extends: true or missing):**
- Merge ALL layers from lowest to highest
- Add layer markers to show source
- Concatenate with `---` separators

### Cascading Example

```markdown
<!-- Layer: package core -->
Create conventional commits with semantic format.
Use imperative mood.

---
<!-- Layer: user personal -->
Additionally, always include ticket references in format PROJ-123.

---
<!-- Layer: project -->
For this API, also update CHANGELOG.md after each commit.
```

All three layers merged. User sees complete instructions.

### Override Example

If project layer has:
```yaml
---
name: commit
extends: false
---

Custom commit workflow - ignore all defaults.
```

Result: Only project layer content. Core and user layers ignored.

## Error Handling

- **Directory doesn't exist:** Skip silently (not an error)
- **SKILL.md malformed:** Report error, don't use it
- **No frontmatter:** Default to `extends: true`
- **Skill not found:** List available skills

## Performance Optimization

**Cache discovered skills per session:**
- Discover once at session start or first use
- Reuse cached list for rest of session
- Only re-discover if user explicitly requests

**Lazy discovery:**
- Don't glob all skills upfront
- Discover specific skill only when invoked
- Faster for large skill collections

## Important Notes

- **Always read SKILL.md files** - don't rely on cached content between sessions
- **Respect the `extends` field** - it controls composition behavior
- **Show layer markers** in merged content - helps user understand what's active
- **Check all locations** - don't stop at first match unless `extends: false`

## Skill Catalog

To show available skills to the user, glob all discovery locations and list found skills with their descriptions from frontmatter.
