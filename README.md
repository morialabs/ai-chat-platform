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

## License

MIT
