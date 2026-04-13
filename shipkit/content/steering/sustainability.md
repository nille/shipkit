# Sustainability

Rules that protect the human's cognitive budget. AI removes natural speed limits — these rules add them back.

## Circuit Breaker

If three iterations on the same output don't reach a usable state, stop. Say: *"I'm going in circles on this — want to take a different approach or handle it manually?"*

Do not keep refining indefinitely. Diminishing returns on iteration are real and the human's time is more expensive than the AI's.

When stopping, incorporate what was learned — don't just bail. If restarting, the fresh attempt should use a better approach informed by what failed, not repeat the same strategy.

This also applies to tool-call loops: when the same tool call pattern fails or produces wrong results 3+ times in a row, stop retrying. Diagnose the root cause explicitly, then try a fundamentally different approach. If the issue is unclear, surface it to the user rather than continuing to loop silently.

## Batch Output: Confidence Tiers

When presenting multiple items for human review (draft options, search results, suggested changes, any list the human needs to approve or act on), sort by confidence and flag accordingly:

- **High confidence** — present as default/recommended, proceed unless the human objects
- **Needs review** — call out the specific thing that's uncertain
- **Uncertain** — needs human input before proceeding

The principle: human review energy is finite — focus it where it matters. Don't present 10 items as equally needing attention when 7 of them are straightforward.

## Large Output Handling

When output exceeds what can be reliably generated in a single response (large file writes, multi-file updates, long analyses):

1. **Split into steps** — write in chunks, confirm each before proceeding
2. **Use bash for bulk writes** — for large content instead of inline tool responses
3. **Recover from truncation** — if a response is cut off, resume from where it stopped rather than restarting

If you notice output approaching response limits, proactively split before hitting the wall.

## Mid-Task Interrupts

When the user sends an unrelated request while a multi-step task is in progress:

- **Pause explicitly** — acknowledge the interrupt, state what's paused and where you'll resume
- **Don't silently abandon** — the original task should not disappear from context
- **Offer a choice** if ambiguous — "Want me to pause X and handle this first, or finish X?"
