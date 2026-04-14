# Pattern Learner Hook Demo

The pattern learner watches how you work and suggests automating repeated workflows into skills.

## How It Works

### 1. Detection (Session End)
After each session, analyzes your transcript to find:
- **Command sequences** - 3+ bash commands run together
- **File edit patterns** - Files edited together
- **Error → fix patterns** - Common bugs and your solutions

### 2. Storage (Cross-Session Tracking)
Patterns stored in `~/.config/shipkit/.state/patterns/`
- Tracks occurrence count
- Records which sessions
- Maintains confidence score

### 3. Suggestion (Threshold)
After seeing pattern 3+ times across sessions:
- Uses LLM to assess if worth automating
- Suggests skill name
- Offers to create the skill for you

## Example: Debug Service Pattern

### Session 1 (Monday)
```bash
You: "The payment service is down"
Claude: 
  → grep -r "ERROR" logs/
  → tail -100 logs/payment.log
  → systemctl restart payment-service
  → curl localhost:8080/health
```

**Pattern Learner:** Detects 4-command sequence, saves to patterns/abc123.json

---

### Session 2 (Tuesday)
```bash
You: "Payment service acting up again"
Claude:
  → grep -r "ERROR" logs/
  → tail -100 logs/payment.log
  → systemctl restart payment-service
  → curl localhost:8080/health
```

**Pattern Learner:** Same pattern detected, occurrence count: 2

---

### Session 3 (Wednesday)
```bash
You: "Need to restart payment service"
Claude:
  → grep -r "ERROR" logs/
  → tail -100 logs/payment.log  
  → systemctl restart payment-service
  → curl localhost:8080/health
```

**Pattern Learner:** Pattern seen 3 times → Threshold met!

**LLM Analysis:**
```json
{
  "automatable": true,
  "skill_name": "restart-payment-service",
  "confidence": 0.95,
  "reason": "Clear debugging workflow, highly reusable"
}
```

**Suggestion Shown:**
```
💡 I noticed a repeated workflow pattern:

You've run this sequence across multiple sessions:
  1. grep -r "ERROR" logs/
  2. tail -100 logs/payment.log
  3. systemctl restart payment-service
  4. curl localhost:8080/health

Seen 3 times across 3 sessions.

Would you like me to create a /restart-payment-service skill that automates this?

Say 'yes' to create it, or 'not now' to dismiss (I won't suggest this again).
```

---

## Example: API Endpoint Pattern

### Multiple Sessions
Every time you add a new API endpoint, you:
1. Edit `src/routes/api.ts`
2. Edit `src/controllers/handler.ts`
3. Edit `tests/api.test.ts`
4. Run `npm test`

**Pattern Learner:** Detects file co-editing pattern after 3 occurrences

**Suggestion:**
```
💡 I noticed a repeated file editing pattern:

You often edit these files together:
  - src/routes/api.ts
  - src/controllers/handler.ts
  - tests/api.test.ts

Seen 4 times across 4 sessions.

Would you like me to create a /add-api-endpoint skill that scaffolds all three files?

Say 'yes' to create it, or 'not now' to dismiss.
```

---

## What Gets Automated

### Command Sequences
**Automatable:**
- Service restart workflows
- Log analysis sequences
- Deploy + verify patterns
- Test + lint + format chains

**Not Automatable (LLM filters):**
- One-off debugging (too specific)
- Ad-hoc exploration
- Non-repeatable tasks

### File Edit Patterns
**Automatable:**
- Adding new features (routes + controller + tests)
- Creating new components (file + styles + test)
- Updating schemas (model + migration + types)

**Not Automatable:**
- Random refactoring
- Unrelated file edits
- Low co-occurrence (<70%)

## Configuration

### Enable Pattern Learning (Default)
Runs automatically at session end if ANTHROPIC_API_KEY is set.

### Disable Pattern Learning
```bash
export SHIPKIT_NO_PATTERN_LEARNING=1
```

### Adjust Threshold
Patterns suggested after N occurrences (default: 3)
- Configured in pattern_learner.py
- Lower = more suggestions (might be noisy)
- Higher = fewer suggestions (might miss patterns)

## Storage

Patterns stored at `~/.config/shipkit/.state/patterns/`

```
patterns/
├── abc123def.json          ← Command sequence pattern
├── fed456cba.json          ← File edit pattern
└── 789abc012.json          ← Error fix pattern
```

Each pattern tracks:
- Occurrence count
- Sessions where it appeared
- LLM assessment (automatable, suggested name)
- Confidence score

## Performance

- **Analysis:** ~2-3s at session end (LLM call)
- **Cost:** ~$0.0002 per session (Haiku)
- **Frequency:** Only runs on sessions with 5+ turns
- **Impact:** Zero during session (runs after you close)

## What Makes This Powerful

**Traditional approach:**
- You manually notice repetition (maybe)
- You remember to create a skill (rarely)
- You find time to build it (someday™)

**With Pattern Learner:**
- System notices for you (always)
- Suggests at the right time (after 3 occurrences)
- Offers to build it (just say yes)

**Result:** Your toolkit grows automatically from your actual workflows, not guesses about what you might need.

## Privacy

- All analysis local (patterns stored in ~/.config/shipkit/)
- Transcripts never sent to external services
- Only LLM call: "Is this pattern automatable?" (no sensitive data)
- Can be disabled entirely with env var

---

## Next: When You Say "Yes"

After the hook suggests a pattern and you say "yes", Claude will:
1. Create the skill definition
2. Save to `~/.claude/skills/<name>/SKILL.md`
3. Run `shipkit sync` to activate it
4. You can immediately use `/<name>`

Your workflow just automated itself. 🚀
