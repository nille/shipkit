---
name: browser-test
description: Automated browser testing using Playwright MCP. Test web UIs interactively with your actual browser context (logged-in sessions, cookies). Requires Playwright MCP + Chrome Bridge extension.
requires:
  mcp: playwright
---

# Browser Test Skill

Interactive browser testing using Playwright MCP with Chrome Bridge extension.

**What makes this powerful:** Uses YOUR actual browser with YOUR logged-in sessions. No need to authenticate in headless browser or manage test accounts.

## Prerequisites

1. **Node.js** - `which node` (required by Playwright)
2. **Playwright MCP** - Should be in your mcp.json
3. **Chrome MCP Bridge Extension** - [Chrome Web Store](https://chromewebstore.google.com/detail/playwright-mcp-bridge/mmlmfjhmonkocbjadbfplnigmagldckm)

## Workflow

### Phase 1: Verify Setup

Check prerequisites:

```bash
# Check Node.js
node --version

# Check if Playwright MCP configured
cat ~/.claude/mcp.json | grep playwright

# Check Chrome extension
# Tell user to verify extension is installed and connected
```

If missing, guide through setup:
```
To use browser automation, you need:
1. Playwright MCP server
2. Chrome MCP Bridge extension

Would you like me to help set these up?
```

### Phase 2: Understand Test Goal

Ask user what they want to test:

```
What would you like to test?

Examples:
- "Test login flow on localhost:3000"
- "Verify checkout works on staging"
- "Check if search results are correct"
- "Test form validation on /signup"

URL and test goal:
```

### Phase 3: Write Test Plan

Based on user's goal, outline test steps:

```
Test Plan: Login flow on localhost:3000

Steps:
1. Navigate to localhost:3000
2. Click "Login" button
3. Fill email: test@example.com
4. Fill password: (use existing session or prompt)
5. Click "Submit"
6. Verify: Redirected to /dashboard
7. Verify: "Welcome" message visible

Ready to run? (This will use your real browser)
```

### Phase 4: Execute Test

Use Playwright MCP to:

1. **Connect to your Chrome browser** (via MCP Bridge extension)
2. **Navigate to URL**
3. **Perform actions** (click, type, wait)
4. **Take screenshots** at key points
5. **Verify expectations**

**Example Playwright commands via MCP:**

```typescript
// Navigate
await page.goto('http://localhost:3000');

// Interact
await page.click('text=Login');
await page.fill('input[name="email"]', 'test@example.com');
await page.fill('input[name="password"]', 'secretpass');
await page.click('button[type="submit"]');

// Verify
await page.waitForURL('/dashboard');
const welcome = await page.textContent('h1');
expect(welcome).toContain('Welcome');

// Screenshot
await page.screenshot({ path: 'test-result.png' });
```

### Phase 5: Report Results

Show test results with screenshots:

```
✅ Login Test Results

1. ✅ Navigation to localhost:3000 - Success
2. ✅ Clicked "Login" button - Success
3. ✅ Filled credentials - Success
4. ✅ Submitted form - Success
5. ✅ Redirected to /dashboard - Success
6. ❌ Welcome message - FAILED
   Expected: "Welcome back"
   Actual: "Hello"

Screenshot saved: test-result.png

Would you like me to:
- Debug the welcome message issue?
- Save this test as an automated test?
- Try again with different inputs?
```

## Advanced Features

### Record User Actions

```
Show me your browser, I'll watch and generate a test:

1. Open Chrome with MCP Bridge connected
2. Perform the actions you want to test
3. I'll record them and generate test code
```

### Generate Test Code

After successful test, offer to generate code:

```
Would you like me to generate a Playwright test file?

I'll create:
  tests/e2e/login.spec.ts

With the steps we just validated:
- Navigate, click, fill, submit, verify
- Includes assertions and error handling
- Uses Page Object pattern (optional)
```

### Debugging Failed Tests

When test fails, offer to:
- Take screenshot of failure state
- Inspect element causing failure
- Suggest fixes (wrong selector, timing issue, etc.)

## Best Practices

**Use real browser context:**
- Leverage your logged-in sessions (no test auth)
- Access cookies, localStorage, session state
- Test with real user data

**But be careful:**
- Don't run destructive tests on production
- Verify URL before running (localhost, staging, not prod)
- Use read-only operations when testing prod

**Screenshots:**
- Always take screenshot on failure
- Useful for debugging and documentation
- Store in `test-screenshots/` directory

## Limitations

**Requires Chrome:**
- Extension only works in Chrome/Chromium
- Firefox/Safari not supported

**Extension must be running:**
- Check extension is connected before tests
- Green icon in toolbar = ready

**Session state:**
- Tests use YOUR browser state
- If you're not logged in, test will fail
- Clear cookies → tests may fail

## Error Handling

**"Extension not connected"**
→ Open Chrome, click extension icon, verify connection

**"Page not found"**
→ Check URL, ensure dev server running

**"Element not found"**
→ Selector may be wrong, page may have changed

**"Timeout"**
→ Page taking too long to load, or element never appeared

## Key Principles

- **Interactive first** - Validate manually before automating
- **Screenshot everything** - Evidence of what happened
- **Explain failures** - Don't just say "test failed", show why
- **Offer to fix** - Suggest solutions, not just report problems
- **Preserve state** - Use existing browser session, don't disrupt user
