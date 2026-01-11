---
allowed-tools: mcp__playwright__*, Bash(lsof:*), Bash(curl:*), Bash(sleep:*)
description: Execute manual test cases via Playwright browser automation and report pass/fail results
---

## Pre-computed Context

- Frontend port: !`grep -E "^PORT=" frontend/.env.local 2>/dev/null | cut -d= -f2 || echo "3000"`
- Backend port: !`grep -E "^PORT=" backend/.env 2>/dev/null | cut -d= -f2 || echo "8000"`
- Backend status: !`curl -s http://localhost:${PORT:-8000}/health 2>/dev/null && echo " running" || echo "not running"`
- Frontend status: !`curl -s -o /dev/null -w "%{http_code}" http://localhost:${FRONTEND_PORT:-3000} 2>/dev/null | grep -q "200" && echo "running" || echo "not running"`

## Command Arguments

$ARGUMENTS

## Your Task

You are executing manual browser test cases using Playwright MCP tools. Follow these steps:

### 1. Parse Test Cases

**If arguments were provided:** Parse the quoted test case descriptions from the arguments above.

**If no arguments:** Look through the conversation history for test cases. Look for:
- Phrases like "verify that...", "check that...", "test that...", "ensure that..."
- Numbered test steps or acceptance criteria
- Manual testing instructions mentioned earlier

If you cannot find any test cases, ask the user what they would like to test.

### 2. Check Server Status

Before testing, verify servers are running:
- If backend shows "not running", inform user: "Start backend with `make backend-dev`"
- If frontend shows "not running", inform user: "Start frontend with `make frontend-dev`"
- Wait for user to confirm servers are running before proceeding

### 3. Execute Each Test Case

For each test case, use Playwright MCP tools to:

1. **Navigate** to the relevant page using `mcp__playwright__browser_navigate`
2. **Wait** for page load using `mcp__playwright__browser_wait`
3. **Perform actions** (click, type, etc.) as needed for the test
4. **Verify** the expected outcome by checking element text, visibility, or state
5. **Screenshot** the result using `mcp__playwright__browser_screenshot`
6. **Record** PASS or FAIL with explanation

### 4. Output Results

After all tests complete, output a structured report:

```markdown
## Browser Test Results

| # | Test Case | Result | Screenshot |
|---|-----------|--------|------------|
| 1 | [test description] | PASS/FAIL | [filename] |
| 2 | [test description] | PASS/FAIL | [filename] |

### Test Details

#### Test 1: [test description]
- **Status:** PASS/FAIL
- **URL:** [page URL tested]
- **Steps Performed:**
  1. [action taken]
  2. [action taken]
- **Expected:** [what should happen]
- **Actual:** [what actually happened]
- **Screenshot:** [filename]

[Repeat for each test]

### Summary
- Total: X tests
- Passed: X
- Failed: X
```

## Important Notes

- Take a screenshot BEFORE and AFTER key interactions when debugging failures
- If a test fails, capture the current page state and any error messages visible
- Use descriptive screenshot filenames like `test-1-chat-page-loaded.png`
- If the application requires authentication, note that as a blocker
- Default to testing at `http://localhost:3000/chat` unless the test specifies otherwise
