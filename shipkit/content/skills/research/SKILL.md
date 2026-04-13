# Research

Research technical questions using documentation, web search, and project context. Use when user says "research", "find out", "look up", "how does X work", or has a technical question to investigate.

## Overview

Performs multi-source research on technical questions, producing well-sourced answers with citations. Searches official docs, web resources, and project context to build a comprehensive answer.

## Parameters

- **question** (required): The question or topic to research
- **depth** (optional, default: "standard"): How deep to go — "quick" (1-2 sources), "standard" (3-5 sources), "deep" (exhaustive)
- **save** (optional, default: false): Save the research to the project's knowledge directory

## Workflow

### 1. Clarify the Question

Ensure the question is specific enough to research effectively.

**Constraints:**
- If the question is vague ("how does caching work?"), ask for specifics: which technology, what context, what problem they're solving
- If the question references project-specific code, read the relevant files first to understand context
- State your understanding of the question before researching

### 2. Plan Research

Determine which sources to check and in what order.

**Source priority:**
1. **Official documentation** — language/framework/library docs (most authoritative)
2. **Source code** — if the question is about project internals or library behavior
3. **Web search** — blog posts, Stack Overflow, GitHub issues/discussions
4. **Project context** — existing code, tests, config files that demonstrate usage

**Constraints:**
- For quick depth: hit 1-2 sources, give a concise answer
- For standard depth: hit 3-5 sources, synthesize and cross-reference
- For deep depth: be exhaustive, check edge cases, find conflicting information

### 3. Conduct Research

Search and read sources.

**Constraints:**
- You MUST collect source URLs for every piece of information
- You MUST read actual documentation, not just search snippets
- You MUST cross-reference claims across sources when information conflicts
- You MUST check version-specific docs when the answer depends on the version
- You MUST NOT present LLM training data as research — if you can't find a source, say so
- If 2-3 sources come up empty, stop and tell the user rather than guessing

### 4. Synthesize Answer

Produce a clear, sourced answer.

**Format:**
```markdown
## Research: <question summary>

### Answer
<Clear, direct answer to the question>

### Details
<Supporting explanation with code examples if relevant>

### Sources
- [Source title](url) — what it confirmed
- [Source title](url) — what it confirmed

### Caveats
<Any limitations, version dependencies, or conflicting information>
```

**Constraints:**
- Lead with the direct answer, then provide details
- Include code examples when they clarify the answer
- Flag any version-specific behavior
- If sources conflict, present both perspectives and your assessment of which is more authoritative
- If you couldn't find a definitive answer, say so clearly

### 5. Save (if requested)

Save research to the knowledge directory for future reference.

**Constraints:**
- If save is true or user asks to save, write to `<home>/projects/<project>/knowledge/`
- Use kebab-case filename derived from the question
- Include the date in YAML frontmatter

## Examples

### Quick Research

```
User: "does fetch support timeout in Node.js?"
Agent: [checks Node.js docs, MDN]

       "## Research: fetch timeout in Node.js

       ### Answer
       Yes, since Node.js 18. Use `AbortSignal.timeout()`:

       ```js
       const res = await fetch(url, {
         signal: AbortSignal.timeout(5000)
       });
       ```

       ### Sources
       - [Node.js fetch docs](https://nodejs.org/api/globals.html#fetch) — confirms AbortSignal support
       - [MDN AbortSignal.timeout()](https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal/timeout_static) — API reference"
```

### Deep Research

```
User: "research connection pooling strategies for PostgreSQL with Node.js, go deep"
Agent: [searches pg docs, node-pg docs, pgbouncer docs, blog posts, GitHub issues]

       "## Research: PostgreSQL connection pooling with Node.js
       ... (comprehensive multi-source analysis) ..."
```
