# Pre-Commit Safety Hook Demo

This demonstrates the hybrid regex + LLM pre-commit safety scanner.

## How It Works

### Phase 1: Fast Regex Scan (~10ms)
Catches obvious issues with pattern matching.

### Phase 2: LLM Verification (~1-2s)
Context-aware analysis filters false positives.

## Example Scenarios

### Scenario 1: Real Secret (BLOCKED)

```python
# config/production.py
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
```

**Regex:** Detects AWS keys ⚠️  
**LLM:** Confirms real production credentials 🚨  
**Result:** BLOCKED

---

### Scenario 2: Test Fixture (ALLOWED)

```python
# tests/test_auth.py
TEST_AWS_KEY = "AKIAIOSFODNN7EXAMPLE"  # Mock for testing
MOCK_CREDENTIALS = {
    "access_key": "test-key-not-real"
}
```

**Regex:** Detects AWS pattern ⚠️  
**LLM:** "This is in test file with TEST_ prefix, clearly a fixture" ✅  
**Result:** ALLOWED

---

### Scenario 3: Debug Code in Production (BLOCKED)

```javascript
// src/api/handler.ts
export async function handleRequest(req) {
    console.log("User data:", req.user);  // Forgot to remove
    debugger;  // Left in by mistake
    return processRequest(req);
}
```

**Regex:** Detects console.log + debugger ⚠️  
**LLM:** "Production API handler with debug code" 🚨  
**Result:** BLOCKED

---

### Scenario 4: Intentional Debug Module (ALLOWED)

```python
# src/debug/inspector.py
def inspect_state():
    """Debug utility for development."""
    print(f"Current state: {get_state()}")
    return state
```

**Regex:** Detects print() ⚠️  
**LLM:** "debug/inspector.py module - print() is the feature" ✅  
**Result:** ALLOWED (or WARNING)

---

### Scenario 5: TODO Comments (WARNING)

```python
# src/auth.py
def validate_token(token):
    # TODO: Add rate limiting
    return verify_jwt(token)
```

**Regex:** Detects TODO ⚠️  
**LLM:** "Legitimate TODO for future work" ℹ️  
**Result:** WARNING (doesn't block, just notifies)

---

## Configuration

### Enable LLM Verification
Set ANTHROPIC_API_KEY in ~/.claude/settings.json:
```json
{
  "env": {
    "ANTHROPIC_API_KEY": "sk-ant-..."
  }
}
```

### Disable LLM (Regex Only)
```bash
export SHIPKIT_NO_LLM=1
```

### Bypass Hook Entirely
```bash
git commit --no-verify
```

## Performance

**Clean commit:** ~10ms (regex only, no LLM call)  
**Issues found:** ~1-2s (regex + LLM verification)  
**Cost:** ~$0.0001 per commit with issues (Haiku is cheap)

The LLM only runs when regex finds potential issues, so most commits are fast.
