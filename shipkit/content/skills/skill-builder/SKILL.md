# Skill Builder

Create, improve, or analyze skills for shipkit. Use when user says "create skill", "new skill", "improve skill", "update skill", "review skill", "analyze skill", or wants to extend shipkit capabilities.

## Overview

Helps create or update skills for shipkit. Skills follow the SKILL.md format and are placed in the shipkit home directory for personal/project use or in the package for core distribution.

## Prerequisites

**Constraints:**
- You MUST read `references/sop-format.md` before any skill creation or update
- You MUST read `references/architecture-principles.md` before creating new skills or steering
- You SHOULD read `references/skill-format.md` for the compilation and discovery spec
- You SHOULD read `references/categories.md` to determine correct skill placement
- You SHOULD read `references/patterns.md` when the skill produces output or iterates on drafts

## Parameters

- **operation_mode** (required): "create", "update", or "analyze"
- **name** (optional for create, required for update/analyze): Skill name in kebab-case
- **scope** (optional): Where to create the skill — "personal" (default), "project"

## Workflow: Create Skill

### 1. Understand Requirements

Gather information about the skill's purpose and design.

**Constraints:**
- You MUST ask about the skill's purpose and when it will be used
- You MUST confirm name follows kebab-case (e.g., "sync-data", "deploy-app")
- You MUST understand the workflow steps before starting
- You SHOULD check existing skills to avoid overlap

### 2. Determine Location

Decide where the skill should live.

**Locations:**
- `<home>/skills/<name>/` — personal skills, available across all projects
- `<home>/projects/<project>/skills/<name>/` — project-specific skills
- `shipkit/content/skills/<name>/` — core package skills (for shipkit contributors only)

**Constraints:**
- You MUST default to personal skills unless the user explicitly requests project-specific
- You MUST check for name collisions with existing core and personal skills
- Project-specific skills override personal skills which override core skills (by directory name)

### 3. Create SKILL.md

Write the skill definition following the standard format.

**Constraints:**
- You MUST follow the established SKILL.md format (see existing skills for reference)
- You MUST include: title line, trigger description, Overview, Parameters, Workflow steps, Examples
- You MUST use RFC2119 keywords (MUST, SHOULD, MAY) in all constraints
- You MUST provide "because [reason]" for negative constraints
- You MUST include at least one realistic example
- You SHOULD keep SKILL.md under 300 lines — move detailed reference material to a `references/` subdirectory
- You MUST NOT include real personal data, credentials, or project-specific secrets in examples

### 4. Create Reference Files (if needed)

Move detailed reference material to separate files.

**Location:** `<skill-dir>/references/`

**Constraints:**
- You SHOULD move detailed templates, schemas, or reference tables to separate files
- You MUST keep individual reference files focused on one topic
- You MUST reference from SKILL.md using: "See references/filename.md"

### 5. Test and Verify

Confirm the skill works correctly.

**Constraints:**
- Run `shipkit sync` to compile the new skill into tool-native config
- Verify the skill appears in `.claude/commands/` (or equivalent for other tools)
- You MUST review the skill with the user before considering it complete
- You SHOULD suggest testing the skill with a real scenario

---

## Workflow: Update Skill

### 1. Identify Skill and Changes

Understand what needs to be changed.

**Constraints:**
- You MUST ask which skill to update if not specified
- You MUST read the existing SKILL.md completely before making changes
- You MUST ask what changes are needed if not specified

### 2. Apply Updates

Make the requested changes while maintaining format standards.

**Constraints:**
- You MUST maintain the SKILL.md format standards
- You MUST preserve existing functionality unless explicitly changing it
- You MUST NOT remove constraints without explicit user approval because they may be there for important reasons
- You MUST iterate with user until confirmed

### 3. Re-sync

**Constraints:**
- Run `shipkit sync` to update the compiled output
- Verify the changes appear correctly in the tool-native config

---

## Workflow: Analyze Skill

### 1. Read and Understand Skill

Load the skill and its references.

**Constraints:**
- You MUST read the SKILL.md file completely
- You MUST read any files in references/ folder

### 2. Check Format Compliance

Verify the skill follows the standard format.

**Constraints:**
- You MUST check for: title line, trigger description, Overview, Parameters, Workflow, Examples
- You MUST check for RFC2119 keywords in all constraints
- You MUST check that negative constraints have "because [reason]"
- You MUST check Parameters section has (required)/(optional) annotations

### 3. Identify Improvements

Analyze for potential improvements.

**Constraints:**
- You MUST report any format violations
- You SHOULD identify missing error handling or edge cases
- You SHOULD identify unclear or ambiguous constraints
- You SHOULD suggest missing workflow steps
- You MUST present findings to user and ask which to implement

## Examples

### Create Skill

```
User: "create a skill for database migrations"
Agent: "I'll create a 'migrate' skill. Questions:
        1. Which migration tools? (e.g., alembic, prisma, goose)
        2. Should it handle both up and down migrations?
        3. Any safety checks before running in production?"

User: "alembic, yes to both, and always show the SQL first"
Agent: [creates <home>/skills/migrate/SKILL.md]
       [runs shipkit sync]
       "Skill created at <home>/skills/migrate/SKILL.md
        and compiled to .claude/commands/migrate.md.
        Try it: /migrate"
```

### Analyze Skill

```
User: "analyze the commit skill"
Agent: [reads SKILL.md and references]

       "Analysis of /commit:
       
       Format compliance: 
       + All constraints use RFC2119 keywords
       + Parameters have required/optional annotations
       - Missing 'because' on line 45: 'MUST NOT amend'
       
       Improvement opportunities:
       - Could detect monorepo and scope commits per package
       - No guidance for merge commits
       
       Implement any of these?"
```
