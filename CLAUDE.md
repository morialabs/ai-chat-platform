# AI Chat Platform

## Project Goal

Build a domain-specific AI chat platform using Claude Agent SDK (Python) that provides:
- Conversational AI with tool use
- Custom MCP servers for domain-specific functionality
- Skills and commands for specialized behaviors
- CLI interface for testing and development

## Current Status

Backend implementation in progress. No frontend yet.

## Directory Structure

- `backend/` - Python FastAPI application with Claude Agent SDK
- `docs/` - Architecture and research documentation
- `.claude/` - Skills, commands, and settings (to be added)

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

# Run the CLI agent
cd backend && venv/bin/python -m src.cli "Your prompt here"
```

## Code Style

- Python: ruff for linting and formatting
- Type hints required (mypy strict mode)
- Async/await for all agent interactions

## Architecture

See `docs/01-architecture.md` for full architecture documentation.

## Key Files

- `backend/src/cli.py` - CLI entry point for testing agent
- `backend/src/agent/client.py` - Claude Agent SDK wrapper
- `backend/src/config.py` - Configuration management

## Environment Variables

Required:
- `ANTHROPIC_API_KEY` - Your Anthropic API key

Optional:
- `MODEL` - Claude model to use (default: claude-sonnet-4-20250514)
- `MAX_TOKENS` - Maximum tokens for response (default: 8192)
- `DEBUG` - Enable debug mode (default: false)
