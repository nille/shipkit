# Explain

Explain code, architecture, or system behavior. Use when user says "explain this", "how does this work", "what does this do", "walk me through", or "why is it done this way".

## Overview

Reads code and produces clear explanations at the right level of detail. Can explain a single function, an entire module, the project architecture, or how pieces connect.

## Parameters

- **target** (required): What to explain — file path, function name, concept, or "architecture"
- **level** (optional, default: "standard"): Detail level — "brief" (1-2 paragraphs), "standard" (thorough), "deep" (implementation details and trade-offs)
- **audience** (optional): Who the explanation is for — affects terminology and assumptions

## Workflow

### 1. Identify What to Explain

Determine the scope of the explanation.

**Constraints:**
- If target is a file: read the entire file
- If target is a function: read the function and its callers/callees
- If target is "architecture": scan the project structure, entry points, and key modules
- If target is a concept within the codebase: find where it's implemented and how it's used
- If the target is ambiguous (e.g., "the auth system"), explore to understand scope before explaining

### 2. Understand Context

Build understanding before explaining.

**Constraints:**
- Read the code, don't just describe what you'd expect from the name
- Trace data flow through the relevant code paths
- Identify dependencies and integration points
- Check for comments, docstrings, or ADRs that explain intent
- Look at tests to understand expected behavior and edge cases
- Check git blame/log if "why" is part of the question — commit messages often explain design decisions

### 3. Explain

Produce a clear explanation.

**For brief level:**
- 1-2 paragraphs covering what it does and why
- No code examples unless essential

**For standard level:**
- Start with a one-sentence summary
- Explain the high-level flow or structure
- Walk through key code paths with inline code references
- Note important design decisions or patterns used
- Mention gotchas or non-obvious behavior

**For deep level:**
- Everything in standard, plus:
- Implementation details and algorithms used
- Trade-offs and why alternatives weren't chosen
- Performance characteristics
- How it connects to the broader system
- Historical context from git history if relevant

**Constraints:**
- You MUST read the actual code before explaining — never explain from the name alone
- Use the code's own terminology and naming
- Reference specific files and line numbers
- If something is unclear or seems buggy, say so — don't explain bugs as features
- Match the audience's level — if they're new to the codebase, don't assume deep familiarity
- Use diagrams (ASCII) for architecture explanations when they add clarity

### 4. Follow Up

Check if the explanation landed.

**Constraints:**
- After explaining, ask if there's a specific part they want to go deeper on
- If they ask a follow-up, continue in context — don't restart from scratch

## Examples

### Function Explanation

```
User: "explain the retry logic in src/http/client.ts"
Agent: [reads the file, traces the retry flow]

       "The retry logic in `httpClient.request()` (line 45-82) 
       implements exponential backoff with jitter:

       1. Makes the initial request
       2. If it fails with a retryable status (429, 502, 503, 504),
          waits `baseDelay * 2^attempt` ms plus random jitter
       3. Retries up to `maxRetries` times (default 3)
       4. If a `Retry-After` header is present, uses that instead
          of the calculated delay
       
       The jitter (line 67) prevents thundering herd — without it,
       all retrying clients would hit the server at the same time
       after an outage.
       
       Non-retryable errors (4xx except 429) fail immediately.
       
       Want me to go deeper on any part?"
```

### Architecture Explanation

```
User: "explain the architecture"
Agent: [scans project structure, entry points, key files]

       "This is a Next.js 14 app with three main layers:
       
       ┌─────────────────────────────────┐
       │  app/           — Routes (RSC)  │
       │  ├── api/       — API routes    │
       │  └── (dashboard)/ — App pages   │
       ├─────────────────────────────────┤
       │  lib/           — Business logic│
       │  ├── auth/      — NextAuth      │
       │  ├── db/        — Drizzle ORM   │
       │  └── services/  — Domain logic  │
       ├─────────────────────────────────┤
       │  components/    — React UI      │
       │  └── ui/        — shadcn/ui     │
       └─────────────────────────────────┘
       
       Data flows: Route → Service → DB (via Drizzle)
       Auth: NextAuth with JWT strategy, middleware in middleware.ts
       State: Server components by default, client only for interactivity
       
       Want me to go deeper on any layer?"
```
