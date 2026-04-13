"""Template for generating tool-specific guideline discovery instructions.

Similar to skill discovery, but for guidelines - tells agents where to find
and how to cascade behavioral guidelines.
"""

def generate_guideline_discovery_instructions(tool_name: str, tool_project_path: str, tool_user_path: str) -> str:
    """Generate tool-specific guideline discovery instructions.

    Args:
        tool_name: Tool name (e.g., "Claude Code", "Kiro")
        tool_project_path: Project guidelines path (e.g., ".claude/guidelines")
        tool_user_path: User guidelines path (e.g., "~/.claude/guidelines")

    Returns:
        Complete guideline discovery instructions as markdown
    """

    return f"""# Guideline Discovery and Cascading ({tool_name})

**CRITICAL INSTRUCTION:** Guidelines (behavioral rules) are discovered dynamically from multiple locations. You MUST follow these discovery rules.

## What Are Guidelines?

Guidelines are behavioral rules that shape how you work:
- Execution style
- Verification standards
- Development principles
- Safety defaults

They're always active (unlike skills which are on-demand).

## Guideline Discovery Locations

Read guidelines from these locations **in this order** (highest precedence first):

### 1. Project Guidelines (Highest Precedence)
**Path:** `{tool_project_path}/*.md`

**Purpose:** Team-shared guidelines for this project. Committed to repo.

**Example:** `{tool_project_path}/api-conventions.md`

### 2. User Personal Guidelines
**Path:** `{tool_user_path}/*.md`

**Purpose:** Your personal behavioral preferences across all projects.

**Example:** `{tool_user_path}/my-conventions.md`

### 3. Plugin Guidelines
**Path:** `~/.config/shipkit/plugins/*/guidelines/*.md`

**Purpose:** Guidelines from marketplace plugins.

**Example:** `~/.config/shipkit/plugins/security-pack/guidelines/security-rules.md`

### 4. Package Core Guidelines (Lowest Precedence)
**Path:** `~/.config/shipkit/core/guidelines/*.md`

**Purpose:** Built-in guidelines shipped with shipkit.

**Example:** `~/.config/shipkit/core/guidelines/dev-principles.md`

## Discovery Process

At session start, load ALL guidelines:

1. **Glob each location** for `*.md` files
2. **Group by filename** (e.g., all `dev-principles.md` files together)
3. **Apply cascading** (see below)
4. **Load merged content** into your context

## Cascading Logic

When the same filename exists in multiple locations (e.g., `dev-principles.md`):

### Step 1: Parse Frontmatter

Each guideline may have YAML frontmatter:
```yaml
---
extends: true  # or false (defaults to true if missing)
---
```

### Step 2: Check Highest Layer

**If highest precedence layer has `extends: false`:**
- Use ONLY that layer
- Ignore all lower layers

**Otherwise (`extends: true` or missing):**
- Merge ALL layers from lowest to highest
- Add layer markers
- Concatenate with `---` separators

### Example: Cascading Enabled

```
Files found:
1. {tool_project_path}/dev-principles.md (extends: true)
2. {tool_user_path}/dev-principles.md (extends: true)
3. ~/.config/shipkit/core/guidelines/dev-principles.md (no frontmatter)

Result - All merged:
```

```markdown
<!-- Layer: package core -->
Ship small, test at boundaries, prefer simple.

---
<!-- Layer: user personal -->
Additionally: Always use TypeScript strict mode.

---
<!-- Layer: project -->
For this API: Follow REST conventions, use PostgreSQL.
```

### Example: Override

```
Files found:
1. {tool_project_path}/dev-principles.md (extends: false)
2. {tool_user_path}/dev-principles.md (exists)
3. ~/.config/shipkit/core/guidelines/dev-principles.md (exists)

Result - Only project layer:
```

```markdown
Custom dev principles for this project only.
[Lower layers ignored]
```

## Performance

**Load once at session start:**
- Glob all locations
- Parse and cascade all guidelines
- Cache in context
- Don't re-read during session

**Typical overhead:**
- ~8 core guidelines
- ~0-5 user guidelines
- ~0-10 plugin guidelines
- Total: <100ms at session start

## Error Handling

- **Directory missing:** Skip silently
- **File malformed:** Skip with warning
- **No frontmatter:** Default to `extends: true`
- **Permission denied:** Skip with warning

## Important Notes

- **Load all guidelines at session start** - don't wait for specific trigger
- **Respect extends field** - controls composition
- **Show layer markers** - helps debugging
- **Guidelines are always active** - unlike skills (on-demand)
"""
