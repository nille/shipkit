# Retro Templates

Schemas, file locations, and format templates for the retrospective system.

## File Locations

```
<home>/
├── guidelines/
│   ├── ...                   # User guidelines rules
│   └── auto-learned.md       # Cross-cutting auto-learned preferences
├── skills/
│   ├── commit/
│   │   ├── SKILL.md
│   │   └── learned.md        # Per-skill auto-learned rules
│   └── ...
└── .state/                   # Hidden — machine-managed ephemeral data
    ├── sessions/             # Session records for memory/context
    │   └── <session_id>.json
    ├── retro/
    │   ├── observations.jsonl  # Low-severity patterns (append-only)
    │   ├── pending/            # High/medium suggestions awaiting review
    │   │   └── <session_id>.json
    │   └── processed/          # Applied/discarded suggestions (archive)
    │       └── <session_id>.json
    └── debounce/             # Hook debounce state files
```

## Pending Suggestion File

**Path:** `<home>/.state/retro/pending/<session_id>.json`

```json
{
  "session_id": "abc123",
  "timestamp": "2026-04-12T20:00:00Z",
  "cwd": "/path/to/project",
  "project": "my-project",
  "title": "First user message (truncated)",
  "turn_count": 24,
  "user_turn_count": 12,
  "status": "pending_analysis",
  "transcript_summary": "[user] message\n\n[assistant] response\n\n...",
  "suggestions": [
    {
      "type": "skill_improvement",
      "severity": "high",
      "target": "shipkit/content/skills/commit/SKILL.md",
      "title": "Commit skill misses monorepo scope",
      "suggestion": "Add a step to detect monorepo structure and offer per-package commits",
      "evidence": "User: 'no, scope it to the api package'\nAssistant: 'I'll redo the commit...'"
    }
  ]
}
```

**Lifecycle:**
1. Created by `retro_analyze.py` hook with `status: "pending_analysis"`
2. Analyzed by retro skill or retro-auto → suggestions populated
3. Processed (applied/discarded) → moved to `processed/`
4. Skipped → stays in `pending/` for next triage

## Observation File

**Path:** `<home>/.state/retro/observations.jsonl`

One JSON object per line (append-only):

```json
{"timestamp": "2026-04-12T20:00:00Z", "session_id": "abc123", "title": "Agent over-explains", "type": "guidelines_update", "target": null}
```

## Session Record File

**Path:** `<home>/.state/sessions/<session_id>.json`

```json
{
  "session_id": "abc123",
  "timestamp": "2026-04-12T20:00:00Z",
  "project": "my-project",
  "cwd": "/path/to/project",
  "title": "Fix auth middleware token refresh",
  "summary": "Fix auth middleware; Add token refresh; Run tests; Deploy",
  "turn_count": 24,
  "user_turn_count": 12
}
```

## Auto-Learned Guidelines File

**Path:** `<home>/guidelines/auto-learned.md`

```markdown
---
description: "Cross-cutting behavioral preferences. Customizations + auto-learned."
---

# Auto-Learned Preferences

## Customizations
<!-- User-maintained. Retro-auto does NOT touch this section. -->

- Always use conventional commit format
- Default to TypeScript strict mode in new projects

## Auto-Learned
<!-- Auto-maintained by retro-auto. Token budget: 3000. -->

- Prefer brief responses, skip trailing summaries (3x)
- Use ruff instead of black for Python formatting (2x)
```

## Skill Learned File

**Path:** `<home>/skills/<skill-name>/learned.md`

```markdown
---
description: "Learned rules for the commit skill."
---

# Learned: commit

## Customizations
<!-- User-maintained. Retro-auto does NOT touch this section. -->

## Auto-Learned
<!-- Auto-maintained by retro-auto. Token budget: 1000. -->

- Scope commits per package in monorepo (2x)
- Include ticket number from branch name in commit message (1x)
```
