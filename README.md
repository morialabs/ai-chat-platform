# AI Chat Platform

A domain-specific AI chat platform built with **Claude Agent SDK (Python)** and **Next.js**.

## Features

- **Conversational AI** with Claude's latest models
- **Streaming responses** via Server-Sent Events
- **Built-in tools**: File operations, code execution, web search
- **Custom tools** via MCP (Model Context Protocol)
- **Subagents** for specialized tasks (research, code analysis)
- **Skills & Commands** for domain-specific capabilities
- **User prompts** for interactive clarification
- **Session management** for continuous conversations

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.10+, FastAPI, Claude Agent SDK |
| Frontend | Next.js 14+, React, assistant-ui |
| Database | PostgreSQL + pgvector |
| Caching | Redis |
| Streaming | Server-Sent Events (SSE) |

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker (optional, for dependencies)
- Anthropic API key

### Installation

```bash
# Clone the repository
git clone <your-repo>
cd ai-chat-platform

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY=your-api-key

# Frontend setup
cd ../frontend
npm install

# Run development servers
# Terminal 1 (backend)
cd backend && uvicorn src.main:app --reload --port 8000

# Terminal 2 (frontend)
cd frontend && npm run dev
```

## Documentation

- [Research Findings](docs/00-research-findings.md) - Background research on AI agent patterns
- [Architecture](docs/01-architecture.md) - Complete system architecture and implementation
- [Original Plan](docs/02-original-research-plan.md) - Initial design patterns research

## Project Structure

```
ai-chat-platform/
├── .claude/                    # Claude Code configuration
│   ├── skills/                 # Custom skills (research, etc.)
│   └── commands/               # Slash commands (/search, etc.)
├── CLAUDE.md                   # Project context for Claude
├── backend/                    # Python FastAPI backend
│   └── src/
│       ├── agent/              # Claude SDK client
│       ├── tools/              # Custom MCP tools
│       └── api/                # FastAPI routes
├── frontend/                   # Next.js frontend
│   └── components/
│       └── chat/               # Chat UI components
├── mcp-servers/                # External MCP servers
└── docs/                       # Documentation
```

## Key Concepts

### Claude Agent SDK

The backend uses Claude Agent SDK's `ClaudeSDKClient` for:
- Session management (continuous conversations)
- Built-in tools (Read, Write, Bash, WebSearch, etc.)
- Custom tools via `@tool` decorator
- Hooks for logging and validation
- Subagents for specialized tasks

### MCP (Model Context Protocol)

Custom tools are implemented as MCP servers:
- **knowledge** - Search and retrieve from knowledge base
- **code** - Execute Python code in sandbox

### assistant-ui

The frontend uses assistant-ui for:
- Streaming message display
- Markdown rendering
- Tool call visualization
- User prompt modals

## Backend Development Roadmap

### Phase 1: API Layer (FastAPI Routes)
- [ ] Create `backend/src/api/` directory structure
- [ ] Implement `api/routes/chat.py` - Main chat endpoint with SSE streaming
- [ ] Implement `api/routes/sessions.py` - Session management (create, list, resume)
- [ ] Implement `api/routes/files.py` - File upload handling
- [ ] Add `api/dependencies.py` - FastAPI dependencies (auth, user context)
- [ ] Update `main.py` with CORS middleware and route registration
- [ ] Add Pydantic models for request/response schemas

### Phase 2: Session Management
- [ ] Create `services/sessions.py` - Session persistence service
- [ ] Implement session storage (in-memory initially, then Redis/PostgreSQL)
- [ ] Add session resumption with `ClaudeSDKClient`
- [ ] Implement session cleanup and TTL expiration

### Phase 3: Enhanced Agent Manager
- [ ] Upgrade `agent/client.py` to full `AgentManager` class
- [ ] Add session dictionary for multi-user support
- [ ] Implement `stream_response()` with proper SSE event formatting
- [ ] Add `respond_to_prompt()` for user input continuation
- [ ] Create `StreamEvent` class with `to_sse()` method

### Phase 4: Knowledge Base Integration
- [ ] Create `services/knowledge.py` - Knowledge base service
- [ ] Create `services/vector_store.py` - Vector DB integration (pgvector)
- [ ] Implement `tools/knowledge.py`:
  - [ ] `search` tool - Semantic search
  - [ ] `get_document` tool - Document retrieval
  - [ ] `synthesize` tool - Multi-source synthesis
- [ ] Create `create_knowledge_server()` MCP server

### Phase 5: Code Execution Tool
- [ ] Create `tools/code_exec.py` - Python code execution
- [ ] Implement sandboxed execution environment
- [ ] Add timeout and resource limits
- [ ] Create MCP server for code execution

### Phase 6: MCP Server Management
- [ ] Create `mcp/servers.py` - MCP server configurations
- [ ] Implement `create_mcp_servers()` factory function
- [ ] Add configuration for external MCP servers
- [ ] Test MCP tool integration end-to-end

### Phase 7: Skills & Commands System
- [ ] Create `.claude/skills/` directory
- [ ] Implement `research.md` skill definition
- [ ] Implement `code-review.md` skill definition
- [ ] Create `.claude/commands/` directory
- [ ] Implement `/search` command
- [ ] Create `.claude/settings.json` with permissions

### Phase 8: Configuration & Environment
- [ ] Create `.env.example` with all required variables
- [ ] Expand `config.py` with:
  - [ ] Database URL settings
  - [ ] Redis URL settings
  - [ ] CORS allowed origins
  - [ ] Workspace directory configuration
- [ ] Add settings validation on startup

### Phase 9: Database Integration
- [ ] Add PostgreSQL + pgvector dependencies to `pyproject.toml`
- [ ] Create database models (`models/messages.py`, `models/sessions.py`)
- [ ] Implement database migrations (Alembic)
- [ ] Add connection pooling

### Phase 10: Testing & Quality
- [ ] Add integration tests for API routes
- [ ] Add tests for knowledge base tools
- [ ] Add tests for session management
- [ ] Add E2E test for full chat flow
- [ ] Set up test fixtures with mock data

### Phase 11: Docker & Deployment
- [ ] Create `Dockerfile.backend`
- [ ] Create `docker-compose.yml` with all services
- [ ] Add health check endpoints
- [ ] Configure production logging
- [ ] Add rate limiting middleware

## License

MIT
