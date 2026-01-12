# AI Chat Platform

## Project Goal

Build a domain-specific AI chat platform using Claude Agent SDK (Python) that provides:
- Conversational AI with tool use
- Custom MCP servers for domain-specific functionality
- Skills and commands for specialized behaviors
- Web interface with streaming responses

## Current Status

**Backend and Frontend implementation complete.** Ready for testing with API key.

### Implemented Features

**Backend:**
- AgentRunner with streaming response support
- FastAPI with SSE streaming `/api/chat` endpoint
- Custom tools via MCP (echo tool example)
- Hooks for tool validation (blocks dangerous bash commands)
- Subagent prompt templates (researcher, code-analyst, data-analyst)
- Configuration via environment variables
- CORS configured for frontend
- Full test suite (21 tests passing)

**Frontend:**
- Next.js 14+ with App Router
- assistant-ui for chat components
- SSE streaming adapter for real-time responses
- Tool call visualization
- User prompt modal for AskUserQuestion
- Tailwind CSS styling
- Playwright E2E tests configured

## Directory Structure

```
ai-chat-platform/
├── backend/
│   ├── src/
│   │   ├── api/              # FastAPI routes
│   │   │   └── routes/
│   │   │       └── chat.py   # SSE streaming endpoint
│   │   ├── agent/            # Claude Agent SDK integration
│   │   │   ├── client.py     # AgentRunner class
│   │   │   ├── hooks.py      # PreToolUse/PostToolUse hooks
│   │   │   ├── options.py    # ClaudeCodeOptions config
│   │   │   └── subagents.py  # Agent prompt templates
│   │   ├── tools/            # Custom MCP tools
│   │   │   ├── echo.py       # Echo tool example
│   │   │   └── server.py     # MCP server config
│   │   ├── cli.py            # CLI entry point
│   │   ├── config.py         # Settings management
│   │   └── main.py           # FastAPI app
│   └── tests/                # Test suite
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js App Router
│   │   │   ├── chat/         # Chat page
│   │   │   └── page.tsx      # Root redirect
│   │   ├── components/chat/  # Chat components
│   │   │   ├── ChatProvider.tsx    # assistant-ui adapter
│   │   │   ├── ChatInterface.tsx   # Main chat UI
│   │   │   ├── ToolCallDisplay.tsx # Tool visualization
│   │   │   └── UserPromptModal.tsx # User input modal
│   │   └── lib/
│   │       └── types.ts      # TypeScript types
│   ├── e2e/                  # Playwright E2E tests
│   │   └── chat.spec.ts
│   └── playwright.config.ts
├── docs/                     # Architecture documentation
├── CLAUDE.md                 # This file
├── Makefile                  # Development commands
└── README.md                 # Project overview
```

## Development Commands

```bash
# === Backend ===
make venv                 # Create Python virtual environment
make install              # Install backend dependencies
make lint                 # Run Python linting
make test                 # Run backend tests
make type-check           # Run mypy
make backend-dev          # Start backend server (uses PORT from .env, default 8000)

# === Frontend ===
make frontend-install     # Install frontend dependencies (pnpm)
make frontend-dev         # Start frontend dev server (uses PORT from .env.local, default 3000)
make frontend-build       # Build frontend for production
make frontend-lint        # Run ESLint

# === E2E Tests ===
make e2e                  # Run Playwright E2E tests
make e2e-ui               # Run Playwright with UI

# === CLI Agent ===
export ANTHROPIC_API_KEY=your-api-key
cd backend && venv/bin/python -m src.cli "Your prompt here"
```

## Running the Full Application

### Using /dev Command (Recommended)

The easiest way to start development servers is with the `/dev` command:

```bash
/dev start    # Start both backend and frontend servers
/dev stop     # Stop both servers
/dev restart  # Restart both servers
/dev          # Same as /dev start
```

The command automatically:
- Detects configured ports from `.env` files
- Skips servers that are already running
- Launches servers as background tasks
- Reports status with URLs

### Manual Method

1. **Set your API key:**
   ```bash
   cd backend
   echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
   ```

2. **Start the backend (Terminal 1):**
   ```bash
   make backend-dev
   ```

3. **Start the frontend (Terminal 2):**
   ```bash
   make frontend-dev
   ```

4. **Open the chat interface:**
   Navigate to http://localhost:3000/chat

### Running Multiple Instances (Git Worktrees)

To run multiple instances on the same machine (e.g., for different git worktrees):

1. **Configure custom ports in each worktree:**

   Backend (`backend/.env`):
   ```bash
   ANTHROPIC_API_KEY=sk-ant-...
   PORT=8001
   FRONTEND_PORT=3001
   ```

   Frontend (`frontend/.env.local`):
   ```bash
   PORT=3001
   BACKEND_URL=http://localhost:8001
   ```

2. **Start servers normally** - they will use the configured ports:
   ```bash
   make backend-dev   # Uses PORT from .env
   make frontend-dev  # Uses PORT from .env.local
   ```

## Git Workflow

- **Never push directly to main.** Always create a feature branch and open a PR.
- Branch naming: `feat/description`, `fix/description`, `docs/description`, `refactor/description`
- All changes to main must go through a pull request.

## Code Style

- Python: ruff for linting and formatting
- TypeScript: ESLint
- Type hints required (mypy strict mode for Python)
- Async/await for all agent interactions

## Code Quality

After editing code files (.py, .ts, .tsx, .js, .jsx, etc.), always run the code-simplifier agent on the modified files before completing the task. Use the Task tool with `subagent_type: "code-simplifier:code-simplifier"` to ensure clarity and maintainability.

## Architecture

See `docs/01-architecture.md` for full architecture documentation.

## Key Files

| File | Description |
|------|-------------|
| `backend/src/api/routes/chat.py` | SSE streaming endpoint |
| `backend/src/agent/client.py` | AgentRunner with streaming |
| `backend/src/main.py` | FastAPI app with CORS |
| `frontend/src/components/chat/ChatProvider.tsx` | assistant-ui SSE adapter |
| `frontend/src/components/chat/ChatInterface.tsx` | Main chat UI |
| `frontend/playwright.config.ts` | E2E test configuration |

## Environment Variables

**Backend (.env):**
- `ANTHROPIC_API_KEY` - Your Anthropic API key (required)
- `MODEL` - Claude model (default: claude-opus-4-5-20251101)
- `MAX_TOKENS` - Maximum tokens (default: 8192)
- `PORT` - Backend server port (default: 8000)
- `FRONTEND_PORT` - Frontend port for CORS (default: 3000)

**Frontend (.env.local):**
- `PORT` - Frontend dev server port (default: 3000)
- `BACKEND_URL` - Backend API URL (default: http://localhost:8000)

## Testing

**Backend unit tests:**
```bash
make test
```

### E2E Tests

**Canonical command to run E2E tests:**
```bash
make e2e
```

This is the standard way to run E2E tests both locally and in CI. The same command is used in the GitHub Actions workflow.

**How it works:**
- Playwright automatically starts both backend and frontend servers
- No need to manually start servers before running tests
- Servers are stopped automatically when tests complete
- Port configuration respects `PORT` and `BACKEND_PORT` env vars (defaults: 3000, 8000)

**Prerequisites:**
1. `ANTHROPIC_API_KEY` set in `backend/.env`
2. Backend dependencies installed (`make install`)
3. Frontend dependencies installed (`make frontend-install`)

**Interactive mode (for debugging):**
```bash
make e2e-ui
```

**Notes:**
- E2E tests make real API calls and incur costs (~$0.01-0.10 per test)
- Tests run sequentially with extended timeouts (up to 90s) for API responses
- Test file: `frontend/e2e/chat.spec.ts`

## Browser Verification Tools

This project has Playwright browser automation configured for Claude to perform manual verification of UI changes.

### Available Tools

**Playwright MCP Server** (`.mcp.json`):
- Configured via `@playwright/mcp@latest`
- Provides browser control tools: navigate, click, type, screenshot, wait
- Uses accessibility tree (no vision models needed)

**Playwright Skill** (`.claude/skills/playwright-skill/`):
- For complex multi-step automation scenarios
- Claude writes and executes custom Playwright scripts
- Use for form flows, multi-page tests, custom assertions

### Using /browser-test Command

Execute manual test cases and get pass/fail results:

```bash
# With inline test cases
/browser-test "chat page loads with welcome message" "input field accepts text"

# From conversation context (extracts test cases mentioned earlier)
/browser-test
```

**Output:** Structured report with pass/fail for each test case, screenshots as evidence.

### Manual Browser Verification

For ad-hoc verification, ask Claude directly:
- "Navigate to the chat page and verify the welcome message is visible"
- "Test the form submission flow and take screenshots"
- "Check if the error message appears when submitting empty form"

### When to Use Which Tool

| Scenario | Tool |
|----------|------|
| Quick visual verification | Playwright MCP tools directly |
| Multiple test cases with pass/fail | `/browser-test` command |
| Complex multi-step scenarios | Playwright Skill |
| Form flows, authentication tests | Playwright Skill |

### Setup for New Team Members

Browser tools should work automatically. If not:

1. **Verify MCP server:** `claude mcp list` should show `playwright`
2. **Check skill installation:** `.claude/skills/playwright-skill/` should exist
3. **Re-run skill setup if needed:**
   ```bash
   cd .claude/skills/playwright-skill && npm run setup
   ```
