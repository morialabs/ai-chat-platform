# AI Chat Platform

## Project Goal

Build a domain-specific AI chat platform using Claude Agent SDK (Python) that provides:
- Conversational AI with tool use
- Custom MCP servers for domain-specific functionality
- Skills and commands for specialized behaviors
- CLI interface for testing and development

## Current Status

Backend CLI agent implementation complete. Ready for testing with API key.

### Implemented Features
- AgentRunner with streaming response support
- Custom tools via MCP (echo tool example)
- Hooks for tool validation (blocks dangerous bash commands)
- Subagent prompt templates (researcher, code-analyst, data-analyst)
- Configuration via environment variables
- Full test suite (21 tests passing)

## Directory Structure

```
ai-chat-platform/
├── backend/
│   ├── src/
│   │   ├── agent/          # Claude Agent SDK integration
│   │   │   ├── client.py   # AgentRunner class
│   │   │   ├── hooks.py    # PreToolUse/PostToolUse hooks
│   │   │   ├── options.py  # ClaudeCodeOptions config
│   │   │   └── subagents.py # Agent prompt templates
│   │   ├── tools/          # Custom MCP tools
│   │   │   ├── echo.py     # Echo tool example
│   │   │   └── server.py   # MCP server config
│   │   ├── cli.py          # CLI entry point
│   │   ├── config.py       # Settings management
│   │   └── main.py         # FastAPI app (placeholder)
│   └── tests/              # Test suite
├── docs/                   # Architecture documentation
├── CLAUDE.md              # This file
├── Makefile               # Development commands
└── README.md              # Project overview
```

## Development Commands

```bash
# Create virtual environment and install dependencies
make venv
make install

# Run linting
make lint

# Fix linting issues
make lint-fix

# Run tests
make test

# Run type checking
make type-check

# Run all checks
make all

# Run the CLI agent (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=your-api-key
cd backend && venv/bin/python -m src.cli "Your prompt here"
```

## Code Style

- Python: ruff for linting and formatting
- Type hints required (mypy strict mode)
- Async/await for all agent interactions

## Architecture

See `docs/01-architecture.md` for full architecture documentation.

## Key Files

| File | Description |
|------|-------------|
| `backend/src/cli.py` | CLI entry point for testing agent |
| `backend/src/agent/client.py` | AgentRunner with streaming |
| `backend/src/agent/hooks.py` | Tool validation and logging |
| `backend/src/agent/options.py` | Agent configuration |
| `backend/src/tools/echo.py` | Example custom MCP tool |
| `backend/src/config.py` | Environment-based settings |

## Environment Variables

Required:
- `ANTHROPIC_API_KEY` - Your Anthropic API key

Optional:
- `MODEL` - Claude model to use (default: claude-sonnet-4-20250514)
- `MAX_TOKENS` - Maximum tokens for response (default: 8192)
- `DEBUG` - Enable debug mode (default: false)

## Next Steps

1. Set `ANTHROPIC_API_KEY` and test CLI agent
2. Add more custom tools for your domain
3. Implement FastAPI routes for web interface
4. Build Next.js frontend with assistant-ui
