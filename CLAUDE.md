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
make backend-dev          # Start backend server (port 8000)

# === Frontend ===
make frontend-install     # Install frontend dependencies (pnpm)
make frontend-dev         # Start frontend dev server (port 3000)
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

## Code Style

- Python: ruff for linting and formatting
- TypeScript: ESLint
- Type hints required (mypy strict mode for Python)
- Async/await for all agent interactions

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
- `ALLOWED_ORIGINS` - CORS origins (default: http://localhost:3000)

**Frontend (.env.local):**
- `NEXT_PUBLIC_API_URL` - Backend URL (default: http://localhost:8000)

## Testing

**Backend unit tests:**
```bash
make test
```

**E2E tests (requires both servers + API key):**
```bash
make e2e
```

Note: E2E tests make real API calls and incur costs (~$0.01-0.10 per test).
