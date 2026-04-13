# Retrospective

Review session learnings and capture improvements. Use when user says "retrospective", "retro", "what did we learn", "session review", "check retro", or at the end of a productive session.

## Overview

Two modes of operation:

1. **Interactive** (default) — analyze the current conversation, surface findings, apply improvements
2. **Triage pending** — review suggestions captured by the automated retro-analyzer hook from previous sessions

The retro-analyzer hook runs automatically after each session (via `SessionEnd` / stop hook) and saves transcript summaries to `<home>/.state/retro/pending/`. This skill processes those pending items alongside live session analysis.

Learnings are stored as skill improvements, steering updates, or knowledge entries.

## Parameters

- **scope** (optional): What to review — "session" (default, current conversation), "pending" (triage async suggestions), "all" (session + pending), "topic" (specific area)
- **depth** (optional): How thorough — "quick" (default, key takeaways only), "full" (structured analysis)

## Workflow

### 1. Check for Pending Suggestions

Look for pending retro analysis from previous sessions.

**Constraints:**
- Read all `.json` files from `<home>/.state/retro/pending/` — use `ls` or file read, NOT glob (the directory may be gitignored)
- If pending suggestions exist, report count: "Found N pending retro items from previous sessions"
- If scope is "pending", skip to step 2b (triage only). If scope is "session" or "all", continue to step 2a
- If no pending items and scope is "pending", state "No pending retro items" and stop

### 2a. Review the Session

Analyze the current conversation for learnings.

**Constraints:**
- Identify: mistakes made, repeated patterns, missing capabilities, things that worked well
- Categorize each finding:
  - **skill_improvement** — a workflow change, missing step, or better default for an existing skill
  - **new_skill** — an entirely new capability that was needed
  - **steering_update** — a behavioral rule that should apply across all conversations
  - **knowledge** — a factual finding, gotcha, or debugging insight worth preserving
- Apply severity:
  - **high** — user had to correct the agent, issue wasted significant time, or caused data loss risk
  - **medium** — repeated pattern (3+ occurrences), missing capability user worked around
  - **low** — agent self-noticed inefficiency, minor friction, documentation of correct behavior
- If no learnings found, state "No actionable learnings from this session"

### 2b. Triage Pending Items

Process suggestions from the retro-analyzer hook.

**Constraints:**
- Read each pending JSON file — it contains `session_id`, `timestamp`, `turn_count`, and `transcript_summary`
- Analyze the transcript summary to identify learnings (same categories and severity as step 2a)
- You MUST check recent git commits (`git log --oneline -20`) before triaging — a suggestion may already be addressed
- For each pending file, check whether its findings are already encoded in existing skills/steering (sweep for already-implemented items)
- Auto-clear pending files whose findings are all already implemented — move them to `<home>/.state/retro/processed/`
- Report swept items: "Cleared N already-addressed items from M sessions"

### 3. Present Dashboard

Show all findings — both live session and pending — in a unified view.

**Format:**
```markdown
## Retro Dashboard

### Live Session Findings
| # | Severity | Type | Finding |
|---|----------|------|---------|
| 1 | high | skill_improvement | Commit skill didn't handle monorepo |
| 2 | medium | knowledge | Project uses custom test runner |

### Pending (from previous sessions)
| # | Severity | Type | Finding | Session |
|---|----------|------|---------|---------|
| 3 | high | steering_update | Agent over-explains after fixes | 2d ago |
| 4 | medium | skill_improvement | Test skill missed edge case | 5d ago |
```

**Constraints:**
- You MUST present findings before taking any action
- You MUST include a concrete action for each finding
- Sort by severity (high first)
- Only surface high/medium findings by default — show low findings only if user asks
- For pending items, show relative age (e.g., "2d ago", "1w ago")
- Ask: "Act on which items? (numbers, 'all', or 'skip')"

### 4. Process Approved Actions

For each finding the user wants to act on:

**For skill_improvement:**
- Read the target skill's SKILL.md
- Propose a specific change (add a constraint, add a step, modify defaults)
- Apply if approved

**For new_skill:**
- Defer to the /skill-builder skill with the requirements gathered here

**For steering_update:**
- Identify the appropriate steering file (or propose a new one)
- Propose the rule addition
- Apply if approved

**For knowledge:**
- Write a markdown file to the knowledge directory:
  - Global: `<home>/knowledge/<topic>.md`
  - Project-specific: `<home>/projects/<name>/knowledge/<topic>.md`
- Use a descriptive filename (e.g., `custom-test-runner.md`, `api-rate-limits.md`)

**Constraints:**
- You MUST ask the user which findings to act on before making changes
- You MUST show the specific change (diff or new content) before applying
- For skill/steering changes, run `shipkit sync` after applying
- Applied findings: mark as resolved, move pending JSON to `<home>/.state/retro/processed/`
- Discarded findings: remove from pending
- Skipped findings: leave in pending for next triage

### 5. Commit Changes

After applying improvements, offer to commit.

**Constraints:**
- Ask: "Should I commit these changes?"
- If yes, use the /commit skill
- Group related changes into a single commit when they address the same finding

## Examples

### Quick Session Retro

```
User: "retro"
Agent: [checks pending: 2 items from previous sessions]
       [analyzes current conversation]

       "## Retro Dashboard

       Found 2 pending items from previous sessions.

       ### Live Session
       | # | Severity | Type | Finding |
       |---|----------|------|---------|
       | 1 | high | skill_improvement | Debug skill missed checking .env |

       ### Pending
       | # | Severity | Type | Finding | Session |
       |---|----------|------|---------|---------|
       | 2 | medium | knowledge | Staging DB requires VPN | 3d ago |
       | 3 | medium | steering_update | Prefers terse responses | 1w ago |

       Act on which? (1-3, all, or skip)"

User: "all"
Agent: [updates debug skill, saves VPN note, adds steering rule]
       [moves pending items to processed/]
       "Applied all 3. Commit?"
```

### Triage Pending Only

```
User: "check retro"
Agent: [reads ~/.config/shipkit/.state/retro/pending/]
       [sweeps for already-implemented suggestions]

       "Cleared 3 already-addressed items from 2 sessions.

       ## Pending Retro Items (2 remaining)
       | # | Severity | Type | Finding | Session |
       |---|----------|------|---------|---------|
       | 1 | high | skill_improvement | PR skill should detect draft PRs | 2d ago |
       | 2 | medium | knowledge | API rate limit is 100/min not 1000 | 5d ago |

       Act on which?"
```
