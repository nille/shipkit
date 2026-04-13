"""Template for generating tool-specific skill discovery guidelines.

Each tool gets customized discovery instructions with the correct paths
for that tool, plus complete cascading logic.
"""

def generate_discovery_instructions(tool_name: str, tool_project_path: str, tool_user_path: str) -> str:
    """Generate tool-specific skill discovery guideline.

    Args:
        tool_name: Tool name (e.g., "Claude Code", "Kiro")
        tool_project_path: Project skills path (e.g., ".claude/skills")
        tool_user_path: User skills path (e.g., "~/.claude/skills")

    Returns:
        Complete discovery guideline as markdown
    """

    return f"""# Skill Discovery and Cascading ({tool_name})

**CRITICAL INSTRUCTION:** Skills are discovered dynamically from multiple locations. You MUST follow these discovery rules to find and execute skills correctly.

## Skill Discovery Locations

When a user mentions a skill (e.g., `/commit`, `/deploy`), check these locations **in this exact order** (highest precedence first):

### 1. Project Skills (Highest Precedence)
**Path:** `{tool_project_path}/*/SKILL.md`

**Purpose:** Team-shared skills committed to the project repository. These apply only to this project and are shared via git.

**Example:** `{tool_project_path}/deploy/SKILL.md`

### 2. User Personal Skills
**Path:** `{tool_user_path}/*/SKILL.md`

**Purpose:** Your personal skills that apply across all projects. These represent your individual workflow preferences.

**Example:** `{tool_user_path}/commit/SKILL.md`

### 3. Plugin Skills
**Path:** `~/.config/shipkit/plugins/*/skills/*/SKILL.md`

**Purpose:** Skills from marketplace plugins you've installed. These are tool-agnostic and work across all AI coding CLIs.

**Example:** `~/.config/shipkit/plugins/deploy-wizard/skills/deploy/SKILL.md`

### 4. Package Core Skills (Lowest Precedence)
**Path:** `~/.config/shipkit/core/skills/*/SKILL.md`

**Purpose:** Built-in skills shipped with shipkit. These provide baseline functionality.

**Example:** `~/.config/shipkit/core/skills/commit/SKILL.md`

## Discovery Algorithm

When user invokes a skill (e.g., `/commit`):

### Step 1: Search All Locations

Use the Glob tool to search each location:

```
1. Glob("{tool_project_path}/commit/SKILL.md")
2. Glob("{tool_user_path}/commit/SKILL.md")
3. Glob("~/.config/shipkit/plugins/*/skills/commit/SKILL.md")
4. Glob("~/.config/shipkit/core/skills/commit/SKILL.md")
```

Collect ALL found instances (may be 0, 1, or multiple).

### Step 2: Handle Not Found

If NO instances found:
- Report: "Skill `/commit` not found"
- Suggest: Use `/help` to see available skills
- Stop

### Step 3: Parse Frontmatter

For EACH found SKILL.md file, extract YAML frontmatter:

```yaml
---
name: commit
description: Git commit workflow
extends: true  # or false, or missing (defaults to true)
---
```

**Important:**
- Frontmatter is optional
- If missing, default to `extends: true`
- The `extends` field controls cascading behavior

### Step 4: Apply Cascading Logic

**Check the highest precedence layer** (the first location where skill was found):

#### Case A: Highest Layer Has `extends: false`
```yaml
---
extends: false
---
```

**Result:** Use ONLY that layer. Ignore all lower layers completely.

**Example:**
```
Found in:
1. {tool_project_path}/commit/SKILL.md (extends: false)
2. {tool_user_path}/commit/SKILL.md (exists but ignored)
3. ~/.config/shipkit/core/skills/commit/SKILL.md (exists but ignored)

Use ONLY layer 1.
```

#### Case B: Cascading Enabled (`extends: true` or missing)

**Result:** Merge ALL layers from lowest to highest precedence.

**Algorithm:**
1. Start with empty result
2. Process layers from lowest (4) to highest (1)
3. For each layer:
   - If layer has `extends: false` → clear previous content, use only this
   - Otherwise → append to result with separator

**Example:**
```
Found in:
1. {tool_project_path}/commit/SKILL.md (extends: true)
2. {tool_user_path}/commit/SKILL.md (extends: true)
3. ~/.config/shipkit/core/skills/commit/SKILL.md (no frontmatter)

Result - All three merged:
```

```markdown
<!-- Layer: package core (~/.config/shipkit/core/skills/commit/) -->
Create conventional commits using semantic format.
Use present tense: "Add feature" not "Added feature".
Include ticket references where applicable.

---
<!-- Layer: user personal ({tool_user_path}/commit/) -->
Additionally, always use this commit message template:

[TYPE] Brief description

Detailed explanation...

Refs: PROJ-123

---
<!-- Layer: project ({tool_project_path}/commit/) -->
For this API project, also:
- Update CHANGELOG.md with user-facing changes
- Run tests before committing
- Tag commits with API version if public API changed
```

### Step 5: Execute Merged Content

Use the resulting merged content as the skill instructions. The agent now has:
- Core instructions (from package)
- Your personal preferences (from user)
- Project-specific requirements (from repo)

All layered together with clear markers showing where each piece came from.

## Layer Markers

Always include layer markers when merging so the user can see skill composition:

```markdown
<!-- Layer: package core -->
[content]

---
<!-- Layer: user personal -->
[content]

---
<!-- Layer: project -->
[content]
```

These help users understand:
- What's coming from where
- Why certain instructions are present
- What they can override

## Override vs Extend: When to Use Each

### Use `extends: true` (default) when:
- Adding project-specific rules to core behavior
- Layering personal preferences on top of defaults
- Want to keep core instructions and add extras
- Building on what's already there

**Example:** Core commit skill works fine, you just want to add your ticket reference format.

### Use `extends: false` when:
- Completely different workflow for this project
- Core skill is broken or incompatible
- Want to start fresh without inherited behavior
- Your approach conflicts with lower layers

**Example:** Project uses custom deployment system that conflicts with core deploy skill. Override completely.

## Performance Optimization

**Cache discovered skills per session:**
- Discover all skills once at session start or first invocation
- Cache the catalog in memory
- Reuse for rest of session
- Only re-discover if explicitly requested

**Lazy discovery:**
- Don't glob all skills upfront
- Discover specific skill only when invoked
- Faster for large skill collections

## Error Handling

### Directory Doesn't Exist
- **Behavior:** Skip silently
- **Not an error:** User may not have skills in all locations
- **Continue:** Check remaining locations

### SKILL.md Malformed
- **Behavior:** Skip with warning
- **Log:** "Warning: Malformed SKILL.md at [path]"
- **Continue:** Check other layers

### No Frontmatter
- **Behavior:** Default to `extends: true`
- **Rationale:** Most skills should cascade
- **Continue:** Normal processing

### Permission Denied
- **Behavior:** Skip with warning
- **Log:** "Warning: Cannot read [path] (permission denied)"
- **Continue:** Check remaining locations

## Example Scenarios

### Scenario 1: Pure Core Skill
```
Found only in: ~/.config/shipkit/core/skills/commit/SKILL.md
Result: Use as-is (no other layers exist)
```

### Scenario 2: User Extends Core
```
Found in:
- {tool_user_path}/commit/SKILL.md (extends: true)
- ~/.config/shipkit/core/skills/commit/SKILL.md

Result: Merge both layers
```

### Scenario 3: Project Overrides Everything
```
Found in:
- {tool_project_path}/commit/SKILL.md (extends: false)
- {tool_user_path}/commit/SKILL.md (exists)
- ~/.config/shipkit/core/skills/commit/SKILL.md (exists)

Result: Use ONLY project layer
```

### Scenario 4: Plugin Adds Capability
```
Found in:
- ~/.config/shipkit/plugins/enhanced-commit/skills/commit/SKILL.md (extends: true)
- ~/.config/shipkit/core/skills/commit/SKILL.md

Result: Merge plugin + core
```

### Scenario 5: Full Stack
```
Found in all 4 locations, all with extends: true

Result: Merge all 4 layers:
package core → user → plugins → project
```

## Debugging Discovery

If a skill isn't working as expected, you can debug by:

1. **List all locations:** Glob all 4 paths to see where skill exists
2. **Read frontmatter:** Check extends field in each location
3. **Show cascade:** Display how layers are being merged
4. **Check precedence:** Verify highest layer is what you expect

When user asks "why is /commit doing X?", you can show:
```
/commit skill is composed from:
- Layer 1 (project): {tool_project_path}/commit/SKILL.md (extends: true)
- Layer 2 (user): {tool_user_path}/commit/SKILL.md (extends: true)
- Layer 3 (core): ~/.config/shipkit/core/skills/commit/SKILL.md

Behavior X comes from Layer 2 (your personal preferences).
To change: Edit {tool_user_path}/commit/SKILL.md
```

This transparency is a key advantage of instruction-driven discovery over opaque compilation.
"""
