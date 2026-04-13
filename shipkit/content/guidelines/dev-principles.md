# Development Principles

Core principles for software development work. These guide decision-making when multiple approaches are viable.

## Ship Small

Prefer small, focused changes over large sweeping ones. A 50-line PR that does one thing well is better than a 500-line PR that does five things. Small changes are easier to review, easier to revert, and less likely to introduce regressions.

When a task is large, break it into independently shippable increments. Each increment should leave the codebase in a working state.

## Test at Boundaries

Write tests at system boundaries — where your code meets external systems, user input, or other modules' contracts. Unit test complex logic; integration test the glue. Don't test implementation details that could change without affecting behavior.

If you can't decide whether to test something, ask: "Would I notice if this broke?" If yes, test it.

## Prefer Simple

Choose the simplest solution that correctly solves the problem. Don't add abstraction layers, configuration options, or extension points for hypothetical future requirements. Three similar lines of code are better than a premature abstraction.

Complexity should be earned by real requirements, not anticipated ones.

## Document Decisions

When making a non-obvious technical decision, record the context and reasoning. Future you (or your teammates) will see *what* was done from the code but won't know *why* without a record. ADRs, commit messages, and inline comments (for genuinely surprising code) are all valid.

Don't document *what* the code does — the code says that. Document *why* it does it this way.

## Fix the Root Cause

When debugging, fix the actual cause, not the symptom. A retry loop around a flaky operation is not a fix — understanding why it's flaky is. Quick fixes that mask problems accumulate into systemic fragility.

If the proper fix is too large for the current scope, document the root cause and create a tracked issue.

## Respect Existing Patterns

Before introducing a new pattern, library, or approach, check what the project already uses. Consistency within a codebase is more valuable than theoretical superiority of an alternative. If you want to introduce something new, do it as a deliberate migration, not a one-off deviation.
