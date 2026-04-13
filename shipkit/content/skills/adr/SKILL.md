# ADR

Create Architectural Decision Records. Use when user says "record decision", "adr", "document why", "architecture decision", or "decision record".

## Overview

Creates structured ADRs that capture the context, decision, and consequences of significant architectural choices. Stores them in the project's knowledge directory or a conventional docs/adr/ location.

## Parameters

- **title** (required): Short title for the decision (e.g., "Use PostgreSQL for user data")
- **status** (optional): Decision status — "proposed" (default), "accepted", "deprecated", "superseded"

## Workflow

### 1. Determine Storage Location

Find or create the ADR directory.

**Constraints:**
- Check for existing ADR directories: docs/adr/, docs/decisions/, adr/, doc/architecture/decisions/
- If this is a shipkit project, also check the project knowledge directory
- If no ADR directory exists, suggest creating one and ask the user to confirm the location
- Determine the next ADR number by looking at existing ADRs (e.g., 0001, 0002, ...)
- Use the naming convention matching existing ADRs, or default to: `NNNN-kebab-case-title.md`

### 2. Gather Context

Understand the decision being made.

**Constraints:**
- Ask the user about the decision context if not already clear:
  - What problem are we solving?
  - What options were considered?
  - What was chosen and why?
  - What are the tradeoffs?
- Read relevant code to understand the technical context
- Check for related ADRs that this might supersede or reference

### 3. Write the ADR

Create the record following the standard format.

**Format:**
```markdown
# N. Title

Date: YYYY-MM-DD

## Status

Proposed | Accepted | Deprecated | Superseded by [ADR-NNNN](NNNN-title.md)

## Context

What is the issue that we're seeing that is motivating this decision or change?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

What becomes easier or more difficult to do because of this change?
```

**Constraints:**
- Context section should explain the problem, not the solution
- Decision section should be clear and specific
- Consequences should include both positive and negative impacts
- Reference specific code, systems, or prior ADRs where relevant
- Keep the language factual and concise — ADRs are reference documents, not persuasive essays
- If superseding an existing ADR, update the old ADR's status to link to the new one

### 4. Confirm and Save

**Constraints:**
- Present the draft ADR to the user for review before saving
- Save to the determined location
- If superseding, update the previous ADR's status
- Report the file path of the new ADR

## Examples

### New Architecture Decision

```
User: "let's record why we chose event sourcing for the order system"
Agent: "I'll create ADR-0004. Let me gather context:
        - What alternatives did you consider?
        - What drove the final decision?"

User: "we considered traditional CRUD but needed full audit trail
       and the ability to replay events for debugging production issues"
Agent: [drafts ADR]

       "Draft ADR-0004:
       
       # 4. Use Event Sourcing for Order System
       
       Date: 2026-04-12
       Status: Accepted
       
       ## Context
       The order system requires a complete audit trail for
       compliance and the ability to replay events to debug
       production issues. Traditional CRUD only stores current
       state, making these requirements difficult to satisfy.
       
       ## Decision
       Use event sourcing for the order aggregate. All state
       changes are stored as an immutable sequence of events.
       Current state is derived by replaying the event stream.
       
       ## Consequences
       + Full audit trail by design
       + Event replay enables production debugging
       + Enables future event-driven integrations
       - Higher complexity for simple queries (need projections)
       - Team needs to learn event sourcing patterns
       - Storage grows over time (snapshotting needed later)
       
       Save this?"
```
