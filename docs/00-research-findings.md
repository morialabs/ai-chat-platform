# AI Chat Platform Research Findings

> Research compiled January 2026

## Executive Summary

This document captures research on building a domain-specific AI chat platform with tools, MCP servers, skills, and agent capabilities.

---

## Table of Contents

1. [Design Patterns Overview](#design-patterns-overview)
2. [Framework Comparison](#framework-comparison)
3. [MCP vs Function Calling](#mcp-vs-function-calling)
4. [Provider Comparison](#provider-comparison)
5. [Frontend Libraries](#frontend-libraries)
6. [Claude Agent SDK Details](#claude-agent-sdk-details)

---

## Design Patterns Overview

### Agent Architecture Patterns

#### 1. Single Agent + Tools (Simplest)
```
User -> Agent -> [Tool1, Tool2, Tool3] -> Response
```
Best for: MVPs, straightforward tasks

#### 2. Sequential Orchestration
```
User -> Agent1 -> Agent2 -> Agent3 -> Response
```
Best for: Pipelines (research -> write -> review)

#### 3. Parallel/Concurrent
```
User -> [Agent1, Agent2, Agent3] -> Merge -> Response
```
Best for: Independent analyses, fan-out tasks

#### 4. Supervisor Pattern
```
User -> Supervisor Agent
           |-> Worker Agent 1
           |-> Worker Agent 2
           |-> Worker Agent 3
```
Best for: Multi-agent coordination, routing

#### 5. Hierarchical (Enterprise)
```
User -> Manager -> Team Lead -> Workers
```
Best for: Complex enterprise workflows

### MCP Architecture

MCP (Model Context Protocol) follows a **client-server architecture**:

- **MCP Host**: The AI application (Claude Code, your app)
- **MCP Client**: Maintains connection to MCP server (1:1 relationship)
- **MCP Server**: Provides tools, resources, prompts

```
+-------------------------------------+
|     MCP Host (AI Application)       |
+--------+----------------------------+
         |
    +----+-----+----------+----------+
    |          |          |          |
+---v--+   +---v--+  +---v--+  +---v--+
|Client|   |Client|  |Client|  |Client|
|  #1  |   |  #2  |  |  #3  |  |  #4  |
+---+--+   +---+--+  +---+--+  +---+--+
    |          |         |         |
+---v------+ +-v------+ +-v--+   +-v--+
| Server A | |Server B| |Srv |   |Srv |
| (Local)  | |(Local) | | C  |   | D  |
|Filesystem| |Database| |(Remote) |(Remote)
+----------+ +--------+ +----+   +----+
    STDIO      STDIO      HTTP      HTTP
```

---

## Framework Comparison

### Orchestration Frameworks

| Framework | Best For | Key Strength |
|-----------|----------|--------------|
| **LangGraph** | Complex stateful workflows | Graph-based control, lowest latency, best debugging |
| **CrewAI** | Multi-agent collaboration | Role-based teams ("Researcher", "Writer", etc.) |
| **Agno** (ex-Phidata) | High-performance apps | 10,000x faster instantiation, multimodal support |
| **mcp-agent** | MCP-native workflows | Implements all Anthropic agent patterns composably |

### Provider SDKs

| Platform | Philosophy | Best For |
|----------|-----------|----------|
| **OpenAI Responses API** | Managed, tool-rich | Fast deployment, voice/realtime |
| **Claude Agent SDK** | Autonomous local execution | Full agent capabilities as library |
| **Google ADK** | Enterprise orchestration | Scalable multi-agent, 5k+ concurrent users |
| **AWS Bedrock Agents** | AWS-native | Existing AWS infrastructure |

---

## MCP vs Function Calling

### Use Function Calling When:
- Building a simple/internal tool
- Single provider, no migration plans
- Trusted environment, simple security needs

### Use MCP When:
- You want **provider-agnostic** tool definitions
- Building a **tool ecosystem** that others can extend
- Need **persistent context** across interactions
- Want to tap into the **existing MCP server library**

### Scaling Consideration
MCP tool definitions consume tokens. Solutions:
- **Tool Search Tool**: Deferred loading, discover tools on-demand
- **Code Execution Pattern**: Agent writes code to call tools

---

## Provider Comparison

### OpenAI Responses API
- Built-in code interpreter, file search, web search
- Function calling with structured outputs (strict mode)
- Realtime API for voice agents
- SSE streaming with event types

### Claude API + MCP
- Native tool use / function calling
- MCP support for extensibility
- Tool Search Tool for dynamic discovery
- Computer use capability
- 200K token context window

### Claude Agent SDK
- Same tools as Claude Code (Read, Write, Edit, Bash, Glob, Grep, etc.)
- Built-in MCP support
- Hooks for custom behavior
- Session management
- Subagent support

---

## Frontend Libraries

### Recommended Stack

1. **assistant-ui** (Primary recommendation)
   - 8k GitHub stars, 400k+ monthly npm downloads
   - Handles streaming, auto-scroll, retries, attachments
   - Markdown and code highlighting built-in
   - Tool calls with inline human approval
   - Works with any backend

2. **Vercel AI Elements**
   - 20+ production-ready React components
   - Tightly integrated with AI SDK hooks (useChat)
   - Optimized for streaming markdown
   - Built on shadcn/ui

3. **Vercel AI Chatbot Template**
   - Full-featured Next.js template
   - Open source, hackable
   - streamText + useChat pattern

### Installation

```bash
# assistant-ui
npx assistant-ui create    # new project
npx assistant-ui init      # add to existing project

# Vercel AI SDK
npm install ai @ai-sdk/anthropic
```

---

## Claude Agent SDK Details

### Python SDK Overview

```bash
pip install claude-agent-sdk
```

### Two APIs

| Feature | `query()` | `ClaudeSDKClient` |
|---------|-----------|-------------------|
| Session | New each time | Reuses same session |
| Conversation | Single exchange | Multiple exchanges |
| Hooks | Not supported | Supported |
| Custom Tools | Not supported | Supported |
| Best For | One-off tasks | Continuous conversations |

### Built-in Tools

| Tool | What it does |
|------|--------------|
| **Read** | Read any file |
| **Write** | Create new files |
| **Edit** | Make precise edits |
| **Bash** | Run terminal commands |
| **Glob** | Find files by pattern |
| **Grep** | Search file contents |
| **WebSearch** | Search the web |
| **WebFetch** | Fetch and parse URLs |
| **AskUserQuestion** | Ask clarifying questions |
| **Task** | Spawn subagents |

### Custom Tools (MCP)

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("search_docs", "Search documentation", {"query": str})
async def search_docs(args):
    results = await your_search(args["query"])
    return {"content": [{"type": "text", "text": json.dumps(results)}]}

server = create_sdk_mcp_server(
    name="my-tools",
    tools=[search_docs]
)

options = ClaudeAgentOptions(
    mcp_servers={"tools": server},
    allowed_tools=["mcp__tools__search_docs"]
)
```

### Hooks

```python
async def pre_tool_hook(input_data, tool_use_id, context):
    if input_data['tool_name'] == 'Bash':
        command = input_data['tool_input'].get('command', '')
        if 'rm -rf' in command:
            return {
                'hookSpecificOutput': {
                    'permissionDecision': 'deny',
                    'permissionDecisionReason': 'Dangerous command'
                }
            }
    return {}

options = ClaudeAgentOptions(
    hooks={
        'PreToolUse': [HookMatcher(hooks=[pre_tool_hook])]
    }
)
```

### Subagents

```python
options = ClaudeAgentOptions(
    agents={
        "researcher": AgentDefinition(
            description="Research specialist",
            prompt="Find and synthesize information",
            tools=["WebSearch", "WebFetch", "Read"]
        )
    },
    allowed_tools=["Task"]  # Required for subagents
)
```

---

## Sources

### Official Documentation
- [Claude Agent SDK Overview](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Claude Agent SDK Python Reference](https://platform.claude.com/docs/en/agent-sdk/python)
- [MCP Architecture](https://modelcontextprotocol.io/docs/learn/architecture)
- [Claude Tool Use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use)

### Frontend Libraries
- [assistant-ui](https://github.com/assistant-ui/assistant-ui)
- [Vercel AI Elements](https://vercel.com/academy/ai-sdk/ai-elements)
- [Vercel AI Chatbot](https://github.com/vercel/ai-chatbot)

### Framework Comparisons
- [LangWatch: Best AI Agent Frameworks 2025](https://langwatch.ai/blog/best-ai-agent-frameworks-in-2025)
- [Anthropic: Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)
- [a16z: Deep dive into MCP](https://a16z.com/a-deep-dive-into-mcp-and-the-future-of-ai-tooling/)

### Articles & Guides
- [Claude Agent SDK Best Practices](https://skywork.ai/blog/claude-agent-sdk-best-practices-ai-agents-2025/)
- [MCP Design Patterns](https://www.klavis.ai/blog/less-is-more-mcp-design-patterns-for-ai-agents)
