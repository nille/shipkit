# Retro Analyzer Rules

Rules for the retro-analyzer hook and for inline retro analysis.

## Suggestion Categories

| Category | When to use | Loaded when |
|----------|-------------|-------------|
| `skill_improvement` | Workflow changes, missing steps, better defaults for existing skills | On demand (skill invocation) |
| `new_skill` | Entirely new capability needed | On demand |
| `guidelines_update` | Cross-cutting behavioral rules that apply to ALL conversations | Every conversation |
| `new_guidelines` | New cross-cutting rule file needed | Every conversation |
| `knowledge` | Facts, gotchas, debugging findings worth preserving | Search only |

**Decision criteria:**
- "Would this improve EVERY conversation?" → guidelines
- "Only useful for a specific workflow?" → skill_improvement
- "Only useful for a specific topic/project?" → knowledge
- "Entirely new capability?" → new_skill

## Severity Classification

Apply severity using this decision heuristic — stop at first "yes":

1. Did the user correct the agent? → **high**
2. Did it cause a retry loop (3+ attempts) or user intervention? → **high**
   - Self-corrected in 1-2 attempts without user involvement → **low**
3. Could it cause data loss? → **high**
4. Has this pattern appeared 3+ times? → **medium**
5. Did the user work around a missing feature? → **medium**
6. None of the above → **low**

## Emission Rules

- Only emit **high** and **medium** suggestions to `.state/retro/pending/`
- Log **low** findings to `.state/retro/observations.jsonl` (one line per observation)
- Auto-promote low → medium when the same title appears 3+ times in observations
- Quality over quantity — generalize before emitting
- Don't emit suggestions about hook-injected context itself

## Suggestion Schema

```json
{
  "type": "skill_improvement|new_skill|guidelines_update|new_guidelines|knowledge",
  "severity": "high|medium",
  "target": "file path or null for new items",
  "title": "short description (max 60 chars)",
  "suggestion": "detailed change description",
  "evidence": "2-4 verbatim quoted turns from the transcript"
}
```

## Observation Schema (JSONL)

```json
{"timestamp": "ISO 8601", "session_id": "uuid", "title": "short description", "type": "category", "target": "file path or null"}
```
