# Available Subagents

Subagents are specialized agents that run headless for background tasks. They are spawned by hooks, not invoked directly by the user.

## retro-analyzer

**Purpose:** Analyze conversations for skill and steering improvement opportunities.

**When it runs:** Automatically after each session ends (via `session_end` hook, debounced). Not called directly.

**How it works:** Reads conversation transcript, compares against current skills and steering rules, writes suggestion files to `<home>/.state/retro/pending/`. Results are surfaced by the `/retro` skill or the `context-inject` hook at next session start.

**Output:** Single JSON file per conversation at `<home>/.state/retro/pending/<session_id>.json`

## retro-auto

**Purpose:** Autonomous learning loop — promotes learnable rules from observations and pending suggestions to user content.

**When it runs:** Automatically at session start (via `session_start` hook, debounced) when observations exist. Not called directly.

**How it works:** Classifies suggestions as learnable (behavioral rules that can be applied by reading them) vs structural (workflow changes requiring manual review). Promotes learnable rules to `<home>/steering/auto-learned.md` (cross-cutting) or `<home>/skills/<name>/learned.md` (skill-specific). Structural changes stay in pending for human review via `/retro`.

## session-summarizer

**Purpose:** Summarize session transcripts into concise metadata (title, summary).

**When it runs:** Automatically after each session ends (via `session_end` hook). Not called directly.

**How it works:** Reads the session record, generates a title and summary from the transcript, updates the session JSON at `<home>/.state/sessions/<session_id>.json`. Uses a lightweight model for speed and cost.
