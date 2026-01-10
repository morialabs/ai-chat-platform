# AI Chat Platform Architecture

> Claude Agent SDK + Next.js Implementation

## Overview

This document describes the complete architecture for a domain-specific AI chat platform built on:

- **Backend**: Python + Claude Agent SDK + FastAPI
- **Frontend**: Next.js + React + assistant-ui
- **Protocol**: Server-Sent Events (SSE) for streaming
- **Extensibility**: MCP servers, skills, commands

---

## System Architecture

```
+------------------------------------------------------------------+
|                        FRONTEND (Next.js)                         |
|  +------------------------------------------------------------+  |
|  |                    assistant-ui Components                  |  |
|  |  +-------------+ +-------------+ +------------------------+ |  |
|  |  | ThreadList  | | MessageList | | ToolCallDisplay       | |  |
|  |  +-------------+ +-------------+ +------------------------+ |  |
|  |  +-------------+ +-------------+ +------------------------+ |  |
|  |  | ChatInput   | | MarkdownMsg | | UserQuestionModal     | |  |
|  |  +-------------+ +-------------+ +------------------------+ |  |
|  +------------------------------------------------------------+  |
|                              |                                    |
|                    useAssistant / useChat hooks                   |
|                              | SSE                                |
+------------------------------------------------------------------+
                               |
                          HTTPS/SSE
                               |
+------------------------------------------------------------------+
|                      BACKEND (FastAPI)                            |
|  +------------------------------------------------------------+  |
|  |                      API Layer                              |  |
|  |  /api/chat          - Main chat endpoint (SSE)             |  |
|  |  /api/chat/respond  - User input responses                 |  |
|  |  /api/sessions      - Session management                   |  |
|  |  /api/files         - File uploads                         |  |
|  +------------------------------------------------------------+  |
|                              |                                    |
|  +------------------------------------------------------------+  |
|  |                 Claude Agent SDK Layer                      |  |
|  |  +------------------+  +------------------+                 |  |
|  |  | ClaudeSDKClient  |  | Custom Tools     |                 |  |
|  |  | (sessions)       |  | (@tool decorator)|                 |  |
|  |  +------------------+  +------------------+                 |  |
|  |  +------------------+  +------------------+                 |  |
|  |  | Hooks            |  | Subagents        |                 |  |
|  |  | (Pre/Post Tool)  |  | (research, etc)  |                 |  |
|  |  +------------------+  +------------------+                 |  |
|  +------------------------------------------------------------+  |
|                              |                                    |
|  +------------------------------------------------------------+  |
|  |                    MCP Server Layer                         |  |
|  |  +------------+ +------------+ +------------+ +----------+  |  |
|  |  | Knowledge  | | Code Exec  | | Browser    | | Your     |  |  |
|  |  | Base       | | (Python)   | | (Playwright)| | APIs    |  |  |
|  |  +------------+ +------------+ +------------+ +----------+  |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+
                               |
              +----------------+----------------+
              |                |                |
        +-----v----+    +-----v----+    +------v-----+
        | Anthropic|    | Vector   |    | External   |
        | API      |    | DB       |    | Services   |
        +----------+    +----------+    +------------+
```

---

## Repository Layout

Following Claude Agent SDK conventions and best practices:

```
ai-chat-platform/
|
+-- .claude/                          # Claude Code configuration
|   +-- settings.json                 # Project settings (version controlled)
|   +-- settings.local.json           # Local settings (gitignored)
|   +-- skills/                       # Custom skills
|   |   +-- research.md               # Research skill definition
|   |   +-- code-review.md            # Code review skill
|   |   +-- summarize.md              # Document summarization
|   |   +-- analyze-data.md           # Data analysis skill
|   +-- commands/                     # Slash commands
|       +-- search.md                 # /search command
|       +-- synthesize.md             # /synthesize command
|       +-- ask-expert.md             # /ask-expert command
|
+-- CLAUDE.md                         # Project context for Claude
|
+-- backend/                          # Python FastAPI backend
|   +-- pyproject.toml
|   +-- requirements.txt
|   +-- src/
|   |   +-- __init__.py
|   |   +-- main.py                   # FastAPI app entry
|   |   +-- config.py                 # Configuration
|   |   +-- api/
|   |   |   +-- __init__.py
|   |   |   +-- routes/
|   |   |   |   +-- chat.py           # Chat endpoints
|   |   |   |   +-- sessions.py       # Session management
|   |   |   |   +-- files.py          # File upload handling
|   |   |   +-- dependencies.py       # FastAPI dependencies
|   |   +-- agent/
|   |   |   +-- __init__.py
|   |   |   +-- client.py             # Claude SDK client wrapper
|   |   |   +-- options.py            # Agent configuration
|   |   |   +-- hooks.py              # Custom hooks
|   |   |   +-- subagents.py          # Subagent definitions
|   |   +-- tools/
|   |   |   +-- __init__.py
|   |   |   +-- knowledge.py          # Knowledge base tools
|   |   |   +-- code_exec.py          # Code execution tools
|   |   |   +-- custom.py             # Your domain tools
|   |   +-- mcp/
|   |   |   +-- __init__.py
|   |   |   +-- servers.py            # MCP server configurations
|   |   |   +-- knowledge_server.py   # Knowledge base MCP server
|   |   +-- services/
|   |   |   +-- __init__.py
|   |   |   +-- knowledge.py          # Knowledge base service
|   |   |   +-- vector_store.py       # Vector DB integration
|   |   |   +-- sessions.py           # Session persistence
|   |   +-- models/
|   |       +-- __init__.py
|   |       +-- messages.py           # Message schemas
|   |       +-- sessions.py           # Session schemas
|   +-- tests/
|       +-- __init__.py
|       +-- test_agent.py
|       +-- test_tools.py
|
+-- frontend/                         # Next.js frontend
|   +-- package.json
|   +-- next.config.js
|   +-- tailwind.config.js
|   +-- app/
|   |   +-- layout.tsx
|   |   +-- page.tsx                  # Main chat page
|   |   +-- api/
|   |   |   +-- chat/
|   |   |       +-- route.ts          # Proxy to backend (optional)
|   |   +-- chat/
|   |       +-- page.tsx              # Chat interface
|   |       +-- [sessionId]/
|   |           +-- page.tsx          # Specific session
|   +-- components/
|   |   +-- chat/
|   |   |   +-- ChatProvider.tsx      # assistant-ui provider
|   |   |   +-- ChatInterface.tsx     # Main chat component
|   |   |   +-- MessageList.tsx       # Message rendering
|   |   |   +-- ToolCallDisplay.tsx   # Tool visualization
|   |   |   +-- UserPromptModal.tsx   # User input requests
|   |   |   +-- MarkdownMessage.tsx   # Markdown rendering
|   |   +-- ui/                       # shadcn/ui components
|   +-- lib/
|   |   +-- api.ts                    # API client
|   |   +-- hooks/
|   |   |   +-- useAgent.ts           # Agent interaction hook
|   |   |   +-- useSession.ts         # Session management
|   |   +-- types.ts                  # TypeScript types
|   |   +-- utils.ts
|   +-- styles/
|       +-- globals.css
|
+-- mcp-servers/                      # External MCP servers (optional)
|   +-- knowledge-base/
|   |   +-- package.json
|   |   +-- src/
|   |       +-- index.ts
|   +-- custom-api/
|       +-- package.json
|       +-- src/
|           +-- index.ts
|
+-- docs/
|   +-- 00-research-findings.md
|   +-- 01-architecture.md            # This file
|   +-- 02-api-reference.md
|   +-- 03-deployment.md
|
+-- docker-compose.yml
+-- Dockerfile.backend
+-- Dockerfile.frontend
+-- .env.example
+-- .gitignore
+-- README.md
```

---

## Backend Implementation

### Main Application (`backend/src/main.py`)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.api.routes import chat, sessions, files
from src.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize services
    print("Starting AI Chat Platform...")
    yield
    # Shutdown: cleanup
    print("Shutting down...")

app = FastAPI(
    title="AI Chat Platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(files.router, prefix="/api/files", tags=["files"])

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### Agent Client Wrapper (`backend/src/agent/client.py`)

```python
import asyncio
from typing import AsyncIterator, Optional, Dict, Any
from dataclasses import dataclass
import json

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    UserMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
    HookMatcher,
    AgentDefinition
)

from src.agent.hooks import create_hooks
from src.agent.subagents import SUBAGENTS
from src.tools import create_mcp_servers
from src.config import settings


@dataclass
class StreamEvent:
    """Unified event type for SSE streaming."""
    type: str
    data: Dict[str, Any]

    def to_sse(self) -> str:
        return f"data: {json.dumps({'type': self.type, **self.data})}\n\n"


class AgentManager:
    """Manages Claude Agent SDK sessions."""

    def __init__(self):
        self.sessions: Dict[str, ClaudeSDKClient] = {}

    def get_options(self, user_id: str) -> ClaudeAgentOptions:
        """Create agent options with all configurations."""
        return ClaudeAgentOptions(
            # Built-in tools
            allowed_tools=[
                "Read", "Write", "Edit", "Bash",
                "Glob", "Grep",
                "WebSearch", "WebFetch",
                "AskUserQuestion",
                "Task",  # For subagents
                # MCP tools (prefixed with mcp__<server>__)
                "mcp__knowledge__search",
                "mcp__knowledge__get_document",
                "mcp__code__execute_python",
            ],

            # Custom subagents
            agents=SUBAGENTS,

            # MCP servers (custom tools)
            mcp_servers=create_mcp_servers(),

            # Hooks for logging, validation, etc.
            hooks=create_hooks(user_id),

            # Permission mode
            permission_mode="acceptEdits",

            # Load project settings (CLAUDE.md, skills, etc.)
            setting_sources=["project"],

            # System prompt
            system_prompt={
                "type": "preset",
                "preset": "claude_code",
                "append": f"""
You are an AI assistant for {settings.APP_NAME}.
You have access to the knowledge base and can search documentation.
Always cite sources when providing information from the knowledge base.

Current user: {user_id}
"""
            },

            # Working directory
            cwd=settings.WORKSPACE_DIR,
        )

    async def create_session(self, user_id: str) -> str:
        """Create a new agent session."""
        options = self.get_options(user_id)
        client = ClaudeSDKClient(options=options)
        await client.connect()

        # Get session ID from init message
        session_id = None
        # The SDK will provide session_id in the init message

        self.sessions[session_id] = client
        return session_id

    async def get_or_create_session(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ) -> ClaudeSDKClient:
        """Get existing session or create new one."""
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]

        # Create new session
        options = self.get_options(user_id)
        if session_id:
            options.resume = session_id

        client = ClaudeSDKClient(options=options)
        await client.connect()
        return client

    async def stream_response(
        self,
        user_id: str,
        prompt: str,
        session_id: Optional[str] = None
    ) -> AsyncIterator[StreamEvent]:
        """Stream agent response as events."""
        client = await self.get_or_create_session(user_id, session_id)

        try:
            await client.query(prompt)

            async for message in client.receive_response():
                # Handle different message types
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            yield StreamEvent(
                                type="text",
                                data={"text": block.text}
                            )
                        elif isinstance(block, ToolUseBlock):
                            yield StreamEvent(
                                type="tool_start",
                                data={
                                    "tool_id": block.id,
                                    "tool_name": block.name,
                                    "input": block.input
                                }
                            )

                elif isinstance(message, UserMessage):
                    # Tool results
                    if isinstance(message.content, list):
                        for block in message.content:
                            if isinstance(block, dict) and block.get("type") == "tool_result":
                                yield StreamEvent(
                                    type="tool_result",
                                    data={
                                        "tool_id": block.get("tool_use_id"),
                                        "content": block.get("content"),
                                        "is_error": block.get("is_error", False)
                                    }
                                )

                elif isinstance(message, ResultMessage):
                    # Check for user input required
                    if hasattr(message, 'data') and message.data.get('requires_input'):
                        yield StreamEvent(
                            type="user_input_required",
                            data=message.data
                        )
                    else:
                        yield StreamEvent(
                            type="done",
                            data={
                                "session_id": message.session_id,
                                "result": message.result,
                                "usage": message.usage,
                                "cost": message.total_cost_usd
                            }
                        )

        except Exception as e:
            yield StreamEvent(
                type="error",
                data={"error": str(e)}
            )

    async def respond_to_prompt(
        self,
        session_id: str,
        response: str
    ) -> AsyncIterator[StreamEvent]:
        """Continue session with user's response."""
        if session_id not in self.sessions:
            yield StreamEvent(
                type="error",
                data={"error": "Session not found"}
            )
            return

        client = self.sessions[session_id]
        await client.query(response)

        async for event in self._process_response(client):
            yield event


# Global instance
agent_manager = AgentManager()
```

### Chat Routes (`backend/src/api/routes/chat.py`)

```python
from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from src.agent.client import agent_manager, StreamEvent
from src.api.dependencies import get_current_user

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class UserResponse(BaseModel):
    session_id: str
    response: str


async def event_generator(user_id: str, message: str, session_id: Optional[str]):
    """Generate SSE events from agent response."""
    async for event in agent_manager.stream_response(user_id, message, session_id):
        yield event.to_sse()
    yield "data: [DONE]\n\n"


@router.post("")
async def chat(
    request: ChatRequest,
    user_id: str = Depends(get_current_user)
):
    """Main chat endpoint with SSE streaming."""
    return StreamingResponse(
        event_generator(user_id, request.message, request.session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/respond")
async def respond(
    request: UserResponse,
    user_id: str = Depends(get_current_user)
):
    """Continue conversation with user's response to a prompt."""
    async def generate():
        async for event in agent_manager.respond_to_prompt(
            request.session_id,
            request.response
        ):
            yield event.to_sse()
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

### Custom Tools (`backend/src/tools/knowledge.py`)

```python
from claude_agent_sdk import tool, create_sdk_mcp_server
from typing import Any, Dict, List
import json

from src.services.knowledge import KnowledgeService
from src.services.vector_store import VectorStore


# Initialize services
knowledge_service = KnowledgeService()
vector_store = VectorStore()


@tool(
    "search",
    "Search the knowledge base for relevant documents and information",
    {
        "query": str,
        "category": str,  # Optional: docs, api, tutorials
        "limit": int      # Optional: max results (default 5)
    }
)
async def search_knowledge(args: Dict[str, Any]) -> Dict[str, Any]:
    """Search knowledge base using semantic search."""
    query = args["query"]
    category = args.get("category")
    limit = args.get("limit", 5)

    # Perform semantic search
    results = await vector_store.search(
        query=query,
        filter={"category": category} if category else None,
        limit=limit
    )

    # Format results
    formatted = []
    for result in results:
        formatted.append({
            "title": result.metadata.get("title", "Untitled"),
            "content": result.content[:500] + "..." if len(result.content) > 500 else result.content,
            "source": result.metadata.get("source"),
            "score": result.score
        })

    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "query": query,
                "results": formatted,
                "total": len(formatted)
            }, indent=2)
        }]
    }


@tool(
    "get_document",
    "Retrieve a specific document from the knowledge base by ID or path",
    {"document_id": str}
)
async def get_document(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get full document content."""
    doc_id = args["document_id"]

    document = await knowledge_service.get_document(doc_id)

    if not document:
        return {
            "content": [{"type": "text", "text": f"Document not found: {doc_id}"}],
            "is_error": True
        }

    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "id": document.id,
                "title": document.title,
                "content": document.content,
                "metadata": document.metadata
            }, indent=2)
        }]
    }


@tool(
    "synthesize",
    "Synthesize information from multiple sources into a coherent summary",
    {
        "query": str,
        "sources": List[str],  # Document IDs to synthesize
        "format": str          # Optional: summary, bullet_points, detailed
    }
)
async def synthesize_knowledge(args: Dict[str, Any]) -> Dict[str, Any]:
    """Synthesize multiple documents."""
    query = args["query"]
    source_ids = args.get("sources", [])
    output_format = args.get("format", "summary")

    # Get all source documents
    documents = []
    for doc_id in source_ids:
        doc = await knowledge_service.get_document(doc_id)
        if doc:
            documents.append(doc)

    # Create synthesis context
    context = "\n\n---\n\n".join([
        f"Source: {doc.title}\n{doc.content}"
        for doc in documents
    ])

    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "query": query,
                "source_count": len(documents),
                "sources": [{"id": d.id, "title": d.title} for d in documents],
                "context_for_synthesis": context,
                "requested_format": output_format
            }, indent=2)
        }]
    }


def create_knowledge_server():
    """Create the knowledge base MCP server."""
    return create_sdk_mcp_server(
        name="knowledge",
        version="1.0.0",
        tools=[search_knowledge, get_document, synthesize_knowledge]
    )
```

### Subagents (`backend/src/agent/subagents.py`)

```python
from claude_agent_sdk import AgentDefinition

SUBAGENTS = {
    "researcher": AgentDefinition(
        description="Research specialist that searches knowledge bases and synthesizes information from multiple sources",
        prompt="""You are a research specialist. Your job is to:
1. Search the knowledge base for relevant information
2. Gather information from multiple sources
3. Synthesize findings into coherent summaries
4. Always cite your sources

When researching:
- Start with broad searches, then narrow down
- Cross-reference multiple sources
- Highlight any conflicting information
- Provide confidence levels for your findings
""",
        tools=[
            "mcp__knowledge__search",
            "mcp__knowledge__get_document",
            "mcp__knowledge__synthesize",
            "WebSearch",
            "WebFetch"
        ],
        model="sonnet"
    ),

    "code-analyst": AgentDefinition(
        description="Code analysis expert that reviews code for quality, security, and best practices",
        prompt="""You are a code analysis expert. Your job is to:
1. Review code for quality and best practices
2. Identify potential bugs and security issues
3. Suggest improvements and optimizations
4. Explain complex code patterns

Always be thorough but constructive in your feedback.
""",
        tools=["Read", "Glob", "Grep"],
        model="sonnet"
    ),

    "data-analyst": AgentDefinition(
        description="Data analysis specialist that processes and visualizes data",
        prompt="""You are a data analysis expert. Your job is to:
1. Analyze datasets and identify patterns
2. Create visualizations and charts
3. Perform statistical analysis
4. Generate insights and recommendations

Use Python for data processing and visualization.
""",
        tools=[
            "Read",
            "mcp__code__execute_python",
            "Write"
        ],
        model="sonnet"
    ),
}
```

### Hooks (`backend/src/agent/hooks.py`)

```python
from claude_agent_sdk import HookMatcher, HookContext
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


async def log_tool_usage(
    input_data: Dict[str, Any],
    tool_use_id: str | None,
    context: HookContext
) -> Dict[str, Any]:
    """Log all tool usage for analytics."""
    tool_name = input_data.get('tool_name', 'unknown')
    logger.info(f"Tool used: {tool_name}, ID: {tool_use_id}")
    return {}


async def validate_bash_commands(
    input_data: Dict[str, Any],
    tool_use_id: str | None,
    context: HookContext
) -> Dict[str, Any]:
    """Validate bash commands for safety."""
    if input_data.get('tool_name') != 'Bash':
        return {}

    command = input_data.get('tool_input', {}).get('command', '')

    # Block dangerous patterns
    dangerous_patterns = [
        'rm -rf /',
        'rm -rf ~',
        'sudo rm',
        '> /dev/sda',
        'mkfs.',
        'dd if=',
    ]

    for pattern in dangerous_patterns:
        if pattern in command:
            return {
                'hookSpecificOutput': {
                    'hookEventName': 'PreToolUse',
                    'permissionDecision': 'deny',
                    'permissionDecisionReason': f'Dangerous command pattern blocked: {pattern}'
                }
            }

    return {}


async def track_file_changes(
    input_data: Dict[str, Any],
    tool_use_id: str | None,
    context: HookContext
) -> Dict[str, Any]:
    """Track file modifications for audit."""
    tool_name = input_data.get('tool_name')

    if tool_name in ['Write', 'Edit']:
        file_path = input_data.get('tool_input', {}).get('file_path', '')
        logger.info(f"File modified: {file_path}")
        # Could save to audit log here

    return {}


def create_hooks(user_id: str) -> Dict[str, list]:
    """Create hooks configuration for a user session."""
    return {
        'PreToolUse': [
            HookMatcher(hooks=[log_tool_usage]),
            HookMatcher(matcher='Bash', hooks=[validate_bash_commands]),
        ],
        'PostToolUse': [
            HookMatcher(matcher='Write|Edit', hooks=[track_file_changes]),
        ],
    }
```

---

## Frontend Implementation

### Chat Provider (`frontend/components/chat/ChatProvider.tsx`)

```tsx
'use client';

import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
} from '@assistant-ui/react';
import { ReactNode, useCallback } from 'react';

interface StreamEvent {
  type: 'text' | 'tool_start' | 'tool_result' | 'user_input_required' | 'done' | 'error';
  text?: string;
  tool_id?: string;
  tool_name?: string;
  input?: Record<string, any>;
  content?: string;
  is_error?: boolean;
  session_id?: string;
  result?: string;
  error?: string;
}

const createChatAdapter = (
  sessionId: string | null,
  onSessionId: (id: string) => void,
  onUserInputRequired: (data: any) => void
): ChatModelAdapter => {
  return {
    async *run({ messages, abortSignal }) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.role !== 'user') return;

      const userContent = lastMessage.content
        .filter((c) => c.type === 'text')
        .map((c) => c.text)
        .join('\n');

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userContent,
          session_id: sessionId,
        }),
        signal: abortSignal,
      });

      if (!response.ok) {
        throw new Error(`Chat failed: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') continue;

            try {
              const event: StreamEvent = JSON.parse(data);

              switch (event.type) {
                case 'text':
                  yield {
                    type: 'text-delta' as const,
                    textDelta: event.text || '',
                  };
                  break;

                case 'tool_start':
                  yield {
                    type: 'tool-call-begin' as const,
                    toolCallId: event.tool_id!,
                    toolName: event.tool_name!,
                  };
                  break;

                case 'tool_result':
                  yield {
                    type: 'tool-result' as const,
                    toolCallId: event.tool_id!,
                    result: event.content,
                  };
                  break;

                case 'user_input_required':
                  onUserInputRequired(event);
                  break;

                case 'done':
                  if (event.session_id) {
                    onSessionId(event.session_id);
                  }
                  break;

                case 'error':
                  throw new Error(event.error);
              }
            } catch (e) {
              console.error('Parse error:', e);
            }
          }
        }
      }

      yield { type: 'finish' as const, finishReason: 'stop' as const };
    },
  };
};

interface ChatProviderProps {
  children: ReactNode;
  sessionId?: string | null;
  onSessionIdChange?: (id: string) => void;
  onUserInputRequired?: (data: any) => void;
}

export function ChatProvider({
  children,
  sessionId = null,
  onSessionIdChange = () => {},
  onUserInputRequired = () => {},
}: ChatProviderProps) {
  const adapter = useCallback(
    () => createChatAdapter(sessionId, onSessionIdChange, onUserInputRequired),
    [sessionId, onSessionIdChange, onUserInputRequired]
  );

  const runtime = useLocalRuntime(adapter());

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {children}
    </AssistantRuntimeProvider>
  );
}
```

### Chat Interface (`frontend/components/chat/ChatInterface.tsx`)

```tsx
'use client';

import { useState, useCallback } from 'react';
import {
  Thread,
  ThreadWelcome,
  Composer,
  ComposerInput,
  ComposerSend,
  ThreadMessages,
  ThreadScrollToBottom,
  Message,
  MessageContent,
} from '@assistant-ui/react';

import { ChatProvider } from './ChatProvider';
import { UserPromptModal } from './UserPromptModal';
import { ToolCallDisplay } from './ToolCallDisplay';

interface UserPrompt {
  questions: Array<{
    question: string;
    header: string;
    options: Array<{ label: string; description: string }>;
    multiSelect: boolean;
  }>;
}

export function ChatInterface() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [pendingPrompt, setPendingPrompt] = useState<UserPrompt | null>(null);

  const handleUserInputRequired = useCallback((data: any) => {
    setPendingPrompt(data);
  }, []);

  const handlePromptResponse = useCallback(async (answers: Record<string, string>) => {
    if (!sessionId) return;

    // Send response back to continue the conversation
    await fetch('/api/chat/respond', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        response: JSON.stringify(answers),
      }),
    });

    setPendingPrompt(null);
  }, [sessionId]);

  return (
    <ChatProvider
      sessionId={sessionId}
      onSessionIdChange={setSessionId}
      onUserInputRequired={handleUserInputRequired}
    >
      <div className="flex flex-col h-screen">
        <Thread className="flex-1">
          <ThreadWelcome>
            <div className="text-center p-8">
              <h1 className="text-2xl font-bold mb-2">AI Assistant</h1>
              <p className="text-gray-500">
                Ask me anything. I can search documentation, analyze code, and help with research.
              </p>
            </div>
          </ThreadWelcome>

          <ThreadMessages
            components={{
              Message: ({ message }) => (
                <Message className="py-4">
                  <MessageContent
                    components={{
                      ToolCall: ({ toolCall }) => (
                        <ToolCallDisplay toolCall={toolCall} />
                      ),
                    }}
                  />
                </Message>
              ),
            }}
          />

          <ThreadScrollToBottom />

          <Composer className="p-4 border-t">
            <div className="flex gap-2 max-w-4xl mx-auto">
              <ComposerInput
                placeholder="Ask a question..."
                className="flex-1 p-3 border rounded-lg"
              />
              <ComposerSend className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
                Send
              </ComposerSend>
            </div>
          </Composer>
        </Thread>

        {pendingPrompt && (
          <UserPromptModal
            prompt={pendingPrompt}
            onRespond={handlePromptResponse}
            onCancel={() => setPendingPrompt(null)}
          />
        )}
      </div>
    </ChatProvider>
  );
}
```

### Tool Call Display (`frontend/components/chat/ToolCallDisplay.tsx`)

```tsx
'use client';

import { useState } from 'react';
import { ChevronDown, ChevronRight, Loader2, Check, X } from 'lucide-react';

interface ToolCallProps {
  toolCall: {
    toolCallId: string;
    toolName: string;
    args?: Record<string, any>;
    result?: string;
    status: 'pending' | 'running' | 'complete' | 'error';
  };
}

const TOOL_ICONS: Record<string, string> = {
  'mcp__knowledge__search': '🔍',
  'mcp__knowledge__get_document': '📄',
  'WebSearch': '🌐',
  'WebFetch': '📥',
  'Read': '📖',
  'Write': '✍️',
  'Edit': '✏️',
  'Bash': '💻',
  'Glob': '📁',
  'Grep': '🔎',
  'Task': '🤖',
};

export function ToolCallDisplay({ toolCall }: ToolCallProps) {
  const [expanded, setExpanded] = useState(false);
  const icon = TOOL_ICONS[toolCall.toolName] || '🔧';

  const statusIcon = {
    pending: <Loader2 className="w-4 h-4 animate-spin text-gray-400" />,
    running: <Loader2 className="w-4 h-4 animate-spin text-blue-500" />,
    complete: <Check className="w-4 h-4 text-green-500" />,
    error: <X className="w-4 h-4 text-red-500" />,
  }[toolCall.status];

  return (
    <div className="my-2 border rounded-lg overflow-hidden bg-gray-50">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-3 flex items-center gap-2 hover:bg-gray-100 transition-colors"
      >
        {expanded ? (
          <ChevronDown className="w-4 h-4" />
        ) : (
          <ChevronRight className="w-4 h-4" />
        )}
        <span className="text-lg">{icon}</span>
        <span className="font-mono text-sm">{toolCall.toolName}</span>
        <span className="flex-1" />
        {statusIcon}
      </button>

      {expanded && (
        <div className="p-3 border-t bg-white">
          {toolCall.args && (
            <div className="mb-3">
              <h4 className="text-xs font-semibold text-gray-500 mb-1">Input</h4>
              <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                {JSON.stringify(toolCall.args, null, 2)}
              </pre>
            </div>
          )}

          {toolCall.result && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 mb-1">Result</h4>
              <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto max-h-48 overflow-y-auto">
                {typeof toolCall.result === 'string'
                  ? toolCall.result
                  : JSON.stringify(toolCall.result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

### User Prompt Modal (`frontend/components/chat/UserPromptModal.tsx`)

```tsx
'use client';

import { useState } from 'react';

interface Question {
  question: string;
  header: string;
  options: Array<{ label: string; description: string }>;
  multiSelect: boolean;
}

interface UserPromptModalProps {
  prompt: {
    questions: Question[];
  };
  onRespond: (answers: Record<string, string>) => void;
  onCancel: () => void;
}

export function UserPromptModal({ prompt, onRespond, onCancel }: UserPromptModalProps) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [multiAnswers, setMultiAnswers] = useState<Record<string, string[]>>({});

  const handleSingleSelect = (question: string, value: string) => {
    setAnswers(prev => ({ ...prev, [question]: value }));
  };

  const handleMultiSelect = (question: string, value: string) => {
    setMultiAnswers(prev => {
      const current = prev[question] || [];
      const updated = current.includes(value)
        ? current.filter(v => v !== value)
        : [...current, value];
      return { ...prev, [question]: updated };
    });
  };

  const handleSubmit = () => {
    // Combine single and multi answers
    const finalAnswers: Record<string, string> = { ...answers };
    for (const [q, values] of Object.entries(multiAnswers)) {
      finalAnswers[q] = values.join(', ');
    }
    onRespond(finalAnswers);
  };

  const allAnswered = prompt.questions.every(q => {
    if (q.multiSelect) {
      return (multiAnswers[q.question]?.length || 0) > 0;
    }
    return !!answers[q.question];
  });

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-lg font-semibold mb-4">Input Required</h2>

          {prompt.questions.map((q, i) => (
            <div key={i} className="mb-6">
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2 py-1 bg-gray-100 rounded text-xs font-medium">
                  {q.header}
                </span>
              </div>
              <p className="text-gray-700 mb-3">{q.question}</p>

              <div className="space-y-2">
                {q.options.map((opt, j) => (
                  <button
                    key={j}
                    onClick={() =>
                      q.multiSelect
                        ? handleMultiSelect(q.question, opt.label)
                        : handleSingleSelect(q.question, opt.label)
                    }
                    className={`w-full p-3 text-left border rounded-lg transition-colors ${
                      q.multiSelect
                        ? multiAnswers[q.question]?.includes(opt.label)
                          ? 'border-blue-500 bg-blue-50'
                          : 'hover:bg-gray-50'
                        : answers[q.question] === opt.label
                        ? 'border-blue-500 bg-blue-50'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    <div className="font-medium">{opt.label}</div>
                    <div className="text-sm text-gray-500">{opt.description}</div>
                  </button>
                ))}
              </div>
            </div>
          ))}

          <div className="flex gap-3 mt-6">
            <button
              onClick={onCancel}
              className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={!allAnswered}
              className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Submit
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## Skills & Commands

### Example Skill: Research (`/.claude/skills/research.md`)

```markdown
---
name: research
description: Deep research and synthesis on any topic
triggers:
  - "research"
  - "find information about"
  - "what do we know about"
---

# Research Skill

You are a research specialist. When activated, you will:

## Process

1. **Understand the Query**
   - Parse the user's research question
   - Identify key concepts and entities
   - Determine the scope (broad overview vs. specific detail)

2. **Search Phase**
   - Search the knowledge base using `mcp__knowledge__search`
   - Perform web searches for current information using `WebSearch`
   - Gather 3-5 relevant sources minimum

3. **Analysis Phase**
   - Read each source thoroughly
   - Extract key facts and insights
   - Note any conflicting information
   - Identify gaps in available information

4. **Synthesis Phase**
   - Combine findings into a coherent narrative
   - Organize by theme or chronology as appropriate
   - Highlight confidence levels

5. **Output**
   - Provide a structured summary
   - Include citations for all claims
   - Suggest follow-up questions

## Output Format

```
## Research Summary: [Topic]

### Key Findings
- Finding 1 [Source]
- Finding 2 [Source]

### Detailed Analysis
[Narrative synthesis]

### Sources
1. [Title](link) - Brief description
2. [Title](link) - Brief description

### Gaps & Limitations
- What we couldn't find
- Areas needing more research

### Follow-up Questions
- Question 1
- Question 2
```

## Tools Available
- `mcp__knowledge__search` - Search internal knowledge base
- `mcp__knowledge__get_document` - Get full document
- `WebSearch` - Search the web
- `WebFetch` - Fetch and analyze web pages
- `Task` with `researcher` subagent - Delegate sub-research tasks
```

### Example Command: `/search` (`.claude/commands/search.md`)

```markdown
---
name: search
description: Quick search across knowledge base and web
usage: /search <query>
---

# Search Command

Quick search that returns results from both the knowledge base and web.

## Execution

1. Parse the search query from user input
2. Run parallel searches:
   - `mcp__knowledge__search` with the query
   - `WebSearch` with the query
3. Combine and deduplicate results
4. Present top 10 results with source indicators

## Output Format

### Results for: "{query}"

**From Knowledge Base:**
1. [Title] - Brief excerpt... [KB]
2. [Title] - Brief excerpt... [KB]

**From Web:**
3. [Title](url) - Brief excerpt... [Web]
4. [Title](url) - Brief excerpt... [Web]

---
*{total} results found. Use `/search --detailed` for full content.*
```

---

## Configuration Files

### CLAUDE.md (Project root)

```markdown
# AI Chat Platform

## Project Overview
This is a domain-specific AI chat platform built with Claude Agent SDK and Next.js.

## Architecture
- Backend: Python FastAPI + Claude Agent SDK
- Frontend: Next.js + assistant-ui
- Database: PostgreSQL + pgvector

## Directory Structure
- `backend/` - Python FastAPI application
- `frontend/` - Next.js application
- `mcp-servers/` - Custom MCP servers
- `.claude/` - Skills and commands

## Development Commands
- `make dev` - Start development servers
- `make test` - Run tests
- `make lint` - Run linters

## Code Style
- Python: Black + isort + ruff
- TypeScript: Prettier + ESLint
- Commit messages: Conventional commits

## Important Patterns
- All API responses use SSE for streaming
- Tool results include source citations
- User prompts use AskUserQuestion tool
```

### .claude/settings.json

```json
{
  "permissions": {
    "allow": [
      "Read(**)",
      "Glob(**)",
      "Grep(**)",
      "WebSearch",
      "WebFetch(*)",
      "mcp__knowledge__*"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Write(/etc/**)",
      "Edit(/etc/**)"
    ]
  },
  "mcpServers": {
    "knowledge": {
      "type": "sdk"
    },
    "code": {
      "command": "python",
      "args": ["-m", "mcp_code_server"]
    }
  }
}
```

---

## Deployment

### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_URL=postgresql://user:pass@db:5432/aiplatform
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./workspace:/app/workspace

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend

  db:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=aiplatform
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## Testing Strategy

1. **Unit Tests**
   - Tool implementations
   - Hook logic
   - API route handlers

2. **Integration Tests**
   - Agent SDK interactions
   - MCP server communication
   - SSE streaming

3. **E2E Tests**
   - Full chat flows
   - Tool execution
   - User prompt handling

```python
# Example test
import pytest
from src.agent.client import AgentManager

@pytest.mark.asyncio
async def test_knowledge_search():
    manager = AgentManager()
    events = []

    async for event in manager.stream_response(
        user_id="test",
        prompt="Search for authentication docs"
    ):
        events.append(event)

    # Verify tool was called
    tool_events = [e for e in events if e.type == "tool_start"]
    assert any(e.data["tool_name"] == "mcp__knowledge__search" for e in tool_events)

    # Verify completion
    assert events[-1].type == "done"
```

---

## Next Steps

1. Set up repository structure
2. Install dependencies
3. Configure Claude Agent SDK
4. Build knowledge base integration
5. Implement frontend components
6. Add authentication
7. Deploy to staging
