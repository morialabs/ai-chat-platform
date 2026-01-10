# Building a Domain-Specific AI Chat Platform: Design Patterns & Approaches

## Your Core Question

You want to build a chat experience with:
- Conversational UI (like Grok, OpenAI, etc.)
- Tools, MCP servers, and skills
- Remote code execution
- Domain-specific capabilities

**Two approaches exist:** (1) Model API + Orchestration Layer, or (2) Hosted/Out-of-Box Solutions

---

## Approach 1: Model API + Orchestration Framework

Use a foundation model (Claude, GPT, Gemini, Llama) and add an orchestration layer on top.

### Popular Orchestration Frameworks

| Framework | Best For | Key Strength |
|-----------|----------|--------------|
| **LangGraph** | Complex stateful workflows | Graph-based control, lowest latency, best debugging |
| **CrewAI** | Multi-agent collaboration | Role-based teams ("Researcher", "Writer", etc.) |
| **Agno** (ex-Phidata) | High-performance apps | 10,000x faster instantiation, multimodal support |
| **mcp-agent** | MCP-native workflows | Implements all Anthropic agent patterns composably |

### When to Use This Approach

- You need **multi-model flexibility** (swap Claude for GPT, use local models)
- You want **fine-grained control** over agent logic
- You need **air-gapped/on-premise deployment**
- You're building **complex multi-step workflows**
- You want to avoid vendor lock-in

### Architecture Pattern

```
┌─────────────────────────────────────────────────┐
│              Your Application                    │
├─────────────────────────────────────────────────┤
│         Orchestration Layer                      │
│    (LangGraph / CrewAI / Agno / custom)         │
├─────────────────────────────────────────────────┤
│                 MCP Layer                        │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│   │FS Server│ │Code Exec│ │Your APIs│          │
│   └─────────┘ └─────────┘ └─────────┘          │
├─────────────────────────────────────────────────┤
│              Model Provider API                  │
│        (Claude / GPT / Gemini / Local)          │
└─────────────────────────────────────────────────┘
```

---

## Approach 2: Hosted/Out-of-Box Solutions

Use a provider's complete agent platform that handles orchestration for you.

### Provider Comparison

| Platform | Philosophy | Best For |
|----------|-----------|----------|
| **OpenAI Responses API** | Managed, tool-rich | Fast deployment, voice/realtime, support copilots |
| **Claude Agent SDK** | Autonomous local execution | Computer control, deep task solving |
| **Google ADK** | Enterprise orchestration | Scalable multi-agent, 5k+ concurrent users |
| **AWS Bedrock Agents** | AWS-native | Existing AWS infrastructure |

### When to Use This Approach

- You want **speed to market** (days, not weeks)
- You're okay with **model lock-in** (mostly)
- Built-in tools (code execution, file search, web search) meet your needs
- Simpler architecture is a priority

### Key Features by Provider

**OpenAI Responses API:**
- Built-in code interpreter, file search, web search
- Function calling with structured outputs
- Realtime API for voice agents
- Note: Assistants API being phased out

**Claude (Anthropic):**
- Native tool use / function calling
- MCP support for extensibility
- Tool Search Tool for dynamic discovery (deferred loading)
- Computer use capability

**Google ADK:**
- Multi-agent collaboration patterns
- Model-agnostic (supports Claude, Llama via Vertex AI)
- Enterprise IAM, audit logging, state management

---

## MCP vs Function Calling: When to Use Each

### Use Function Calling When:
- Building a simple/internal tool
- Single provider, no migration plans
- Trusted environment, simple security needs

### Use MCP When:
- You want **provider-agnostic** tool definitions (build once, use anywhere)
- You're building a **tool ecosystem** that others can extend
- You need **persistent context** across interactions
- You want to tap into the **existing MCP server library**

### MCP Scaling Consideration
MCP tool definitions consume tokens. 5+ servers can use 55K-100K+ tokens before conversation starts. Solutions:
- **Tool Search Tool**: Deferred loading, discover tools on-demand
- **Code Execution Pattern**: Agent writes code to call tools instead of direct invocation

---

## Common Agent Architecture Patterns

### 1. Single Agent + Tools (Simplest)
```
User → Agent → [Tool1, Tool2, Tool3] → Response
```
Best for: MVPs, straightforward tasks

### 2. Sequential Orchestration
```
User → Agent1 → Agent2 → Agent3 → Response
```
Best for: Pipelines (research → write → review)

### 3. Parallel/Concurrent
```
User → [Agent1, Agent2, Agent3] → Merge → Response
```
Best for: Independent analyses, fan-out tasks

### 4. Supervisor Pattern
```
User → Supervisor Agent
           ├→ Worker Agent 1
           ├→ Worker Agent 2
           └→ Worker Agent 3
```
Best for: Multi-agent coordination, routing

### 5. Hierarchical (Enterprise)
```
User → Manager → Team Lead → Workers
```
Best for: Complex enterprise workflows

---

## Remote Code Execution Options

1. **OpenAI Code Interpreter** - Built-in, sandboxed Python
2. **MCP Code Execution Servers** - Playwright (browser), Python sandbox, shell
3. **Self-hosted** - E2B, Modal, custom Docker sandboxes
4. **Anthropic's approach** - Agent writes code to call MCP servers efficiently

---

## Decision Framework

```
Do you need multi-model support?
├─ YES → Approach 1 (Orchestration layer)
└─ NO → Continue...

Do you need fine-grained workflow control?
├─ YES → Approach 1 (LangGraph recommended)
└─ NO → Continue...

Is speed-to-market critical?
├─ YES → Approach 2 (Hosted solution)
└─ NO → Approach 1 (More flexibility)

Which hosted solution?
├─ Need voice/realtime → OpenAI Responses API
├─ Need computer control → Claude Agent SDK
├─ Need enterprise scale (5k+ users) → Google ADK
└─ AWS ecosystem → Bedrock Agents
```

---

## Recommended Starting Point

For a **domain-specific AI platform with tools, MCP, and skills**:

### Option A: Hybrid (Recommended for Flexibility)
- **Model**: Claude API or OpenAI API
- **Orchestration**: LangGraph or Agno
- **Tools**: MCP servers for extensibility
- **Code Exec**: E2B or Modal (sandboxed)

### Option B: Fast Path (Speed to Market)
- **OpenAI Responses API** with built-in tools
- Add custom functions for domain-specific features
- Migrate to orchestration layer if you hit limits

### Option C: Enterprise Scale
- **Google ADK** for orchestration
- Multiple model backends via Vertex AI
- MCP for tool ecosystem

---

---

# IMPLEMENTATION GUIDE 1: OpenAI + React Frontend

Complete implementation with tools, user prompts, streaming, and code execution.

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                     React Frontend                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │ Chat UI     │  │ Tool Results│  │ Code Output Display │   │
│  │ Component   │  │ Component   │  │ Component           │   │
│  └─────────────┘  └─────────────┘  └─────────────────────┘   │
│                          │                                    │
│                    useChat hook                               │
│                 (SSE streaming)                               │
└──────────────────────────────────────────────────────────────┘
                           │
                     HTTPS/SSE
                           │
┌──────────────────────────────────────────────────────────────┐
│                   Backend API (Node.js)                       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              OpenAI Responses API                        │ │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────────────────┐   │ │
│  │  │ Function │ │ Code     │ │ Your Domain Tools      │   │ │
│  │  │ Calling  │ │Interpreter│ │ (execute on backend)   │   │ │
│  │  └──────────┘ └──────────┘ └────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

## Step 1: Backend Setup (Node.js/Express)

### Install dependencies
```bash
npm install openai express cors dotenv
```

### Backend: `server.ts`

```typescript
import express from 'express';
import OpenAI from 'openai';
import cors from 'cors';

const app = express();
app.use(cors());
app.use(express.json());

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

// Define your domain-specific tools
const tools: OpenAI.Responses.Tool[] = [
  // Built-in code interpreter
  { type: "code_interpreter" },

  // Custom function: example domain tool
  {
    type: "function",
    function: {
      name: "search_knowledge_base",
      description: "Search your product's knowledge base for relevant documentation",
      parameters: {
        type: "object",
        properties: {
          query: { type: "string", description: "Search query" },
          category: {
            type: "string",
            enum: ["docs", "api", "tutorials"],
            description: "Category to search"
          }
        },
        required: ["query"]
      },
      strict: true  // Guarantees schema compliance
    }
  },

  // Custom function: user data lookup
  {
    type: "function",
    function: {
      name: "get_user_data",
      description: "Retrieve user account information",
      parameters: {
        type: "object",
        properties: {
          user_id: { type: "string" },
          fields: {
            type: "array",
            items: { type: "string" },
            description: "Fields to retrieve: name, email, plan, usage"
          }
        },
        required: ["user_id"]
      },
      strict: true
    }
  }
];

// Execute your custom tools
async function executeCustomTool(name: string, args: any): Promise<string> {
  switch (name) {
    case "search_knowledge_base":
      // Your implementation
      const results = await yourKnowledgeBaseSearch(args.query, args.category);
      return JSON.stringify(results);

    case "get_user_data":
      // Your implementation
      const userData = await yourUserDataService(args.user_id, args.fields);
      return JSON.stringify(userData);

    default:
      return JSON.stringify({ error: `Unknown tool: ${name}` });
  }
}

// Main chat endpoint with streaming
app.post('/api/chat', async (req, res) => {
  const { messages, conversationId } = req.body;

  // Set up SSE
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  try {
    // Create response with streaming
    const response = await openai.responses.create({
      model: "gpt-4o",
      input: messages,
      tools,
      stream: true,
      // Enable code interpreter to use files if needed
      tool_resources: {
        code_interpreter: {
          file_ids: [] // Add file IDs if user uploaded files
        }
      }
    });

    // Process the stream
    for await (const event of response) {
      // Send each event to the client
      res.write(`data: ${JSON.stringify(event)}\n\n`);

      // Handle function calls that need execution
      if (event.type === 'response.output_item.done') {
        const item = event.item;
        if (item.type === 'function_call') {
          // Execute the function
          const result = await executeCustomTool(
            item.name,
            JSON.parse(item.arguments)
          );

          // Send result back to continue the conversation
          // (OpenAI handles this automatically for built-in tools)
          res.write(`data: ${JSON.stringify({
            type: 'tool_result',
            tool_call_id: item.call_id,
            result
          })}\n\n`);
        }
      }
    }

    res.write('data: [DONE]\n\n');
    res.end();

  } catch (error) {
    res.write(`data: ${JSON.stringify({ error: error.message })}\n\n`);
    res.end();
  }
});

// Endpoint for when agent needs user input
app.post('/api/chat/user-input', async (req, res) => {
  const { conversationId, toolCallId, userResponse } = req.body;

  // Continue the conversation with user's input
  // This handles the "ask user for clarification" pattern
  res.json({ status: 'continued' });
});

app.listen(3001);
```

## Step 2: React Frontend

### Types: `types.ts`

```typescript
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'tool';
  content: string;
  toolCalls?: ToolCall[];
  toolResults?: ToolResult[];
  isStreaming?: boolean;
}

export interface ToolCall {
  id: string;
  name: string;
  arguments: Record<string, any>;
  status: 'pending' | 'running' | 'complete' | 'error';
}

export interface ToolResult {
  toolCallId: string;
  result: any;
  error?: string;
}

export interface UserPrompt {
  id: string;
  question: string;
  options?: string[];
  type: 'text' | 'choice' | 'confirm';
}
```

### Custom Hook: `useChat.ts`

```typescript
import { useState, useCallback, useRef } from 'react';
import { Message, ToolCall, UserPrompt } from './types';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [pendingPrompt, setPendingPrompt] = useState<UserPrompt | null>(null);
  const [activeToolCalls, setActiveToolCalls] = useState<ToolCall[]>([]);
  const abortController = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    // Add user message
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    // Prepare messages for API
    const apiMessages = [...messages, userMessage].map(m => ({
      role: m.role,
      content: m.content
    }));

    try {
      abortController.current = new AbortController();

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: apiMessages }),
        signal: abortController.current.signal
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      let assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: '',
        isStreaming: true,
        toolCalls: []
      };

      setMessages(prev => [...prev, assistantMessage]);

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') continue;

            try {
              const event = JSON.parse(data);

              // Handle different event types
              switch (event.type) {
                case 'response.text.delta':
                  // Streaming text
                  assistantMessage = {
                    ...assistantMessage,
                    content: assistantMessage.content + event.delta
                  };
                  setMessages(prev =>
                    prev.map(m => m.id === assistantMessage.id ? assistantMessage : m)
                  );
                  break;

                case 'response.function_call_arguments.delta':
                  // Tool is being called - show in UI
                  setActiveToolCalls(prev => {
                    const existing = prev.find(t => t.id === event.call_id);
                    if (existing) {
                      return prev.map(t =>
                        t.id === event.call_id
                          ? { ...t, status: 'running' as const }
                          : t
                      );
                    }
                    return [...prev, {
                      id: event.call_id,
                      name: event.name,
                      arguments: {},
                      status: 'running' as const
                    }];
                  });
                  break;

                case 'tool_result':
                  // Tool completed
                  setActiveToolCalls(prev =>
                    prev.map(t =>
                      t.id === event.tool_call_id
                        ? { ...t, status: 'complete' as const }
                        : t
                    )
                  );
                  break;

                case 'user_input_required':
                  // Agent needs user input
                  setPendingPrompt({
                    id: event.prompt_id,
                    question: event.question,
                    options: event.options,
                    type: event.options ? 'choice' : 'text'
                  });
                  break;

                case 'code_interpreter.output':
                  // Code execution result
                  assistantMessage = {
                    ...assistantMessage,
                    content: assistantMessage.content +
                      `\n\`\`\`\n${event.output}\n\`\`\`\n`
                  };
                  setMessages(prev =>
                    prev.map(m => m.id === assistantMessage.id ? assistantMessage : m)
                  );
                  break;
              }
            } catch (e) {
              console.error('Parse error:', e);
            }
          }
        }
      }

      // Mark as done streaming
      setMessages(prev =>
        prev.map(m =>
          m.id === assistantMessage.id
            ? { ...m, isStreaming: false }
            : m
        )
      );

    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('Chat error:', error);
      }
    } finally {
      setIsLoading(false);
      setActiveToolCalls([]);
    }
  }, [messages]);

  const respondToPrompt = useCallback(async (response: string) => {
    if (!pendingPrompt) return;

    await fetch('/api/chat/user-input', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        promptId: pendingPrompt.id,
        response
      })
    });

    setPendingPrompt(null);
  }, [pendingPrompt]);

  const stopGeneration = useCallback(() => {
    abortController.current?.abort();
    setIsLoading(false);
  }, []);

  return {
    messages,
    isLoading,
    sendMessage,
    stopGeneration,
    pendingPrompt,
    respondToPrompt,
    activeToolCalls
  };
}
```

### Main Chat Component: `Chat.tsx`

```tsx
import React, { useState, useRef, useEffect } from 'react';
import { useChat } from './useChat';
import { ToolCallIndicator } from './ToolCallIndicator';
import { UserPromptModal } from './UserPromptModal';
import { MessageBubble } from './MessageBubble';

export function Chat() {
  const {
    messages,
    isLoading,
    sendMessage,
    stopGeneration,
    pendingPrompt,
    respondToPrompt,
    activeToolCalls
  } = useChat();

  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    sendMessage(input);
    setInput('');
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(message => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {/* Active tool calls indicator */}
        {activeToolCalls.length > 0 && (
          <div className="space-y-2">
            {activeToolCalls.map(tool => (
              <ToolCallIndicator key={tool.id} tool={tool} />
            ))}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* User prompt modal (when agent asks for input) */}
      {pendingPrompt && (
        <UserPromptModal
          prompt={pendingPrompt}
          onRespond={respondToPrompt}
        />
      )}

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Ask anything..."
            className="flex-1 p-3 border rounded-lg"
            disabled={isLoading}
          />
          {isLoading ? (
            <button
              type="button"
              onClick={stopGeneration}
              className="px-4 py-2 bg-red-500 text-white rounded-lg"
            >
              Stop
            </button>
          ) : (
            <button
              type="submit"
              className="px-4 py-2 bg-blue-500 text-white rounded-lg"
            >
              Send
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
```

### Tool Call Indicator: `ToolCallIndicator.tsx`

```tsx
import React from 'react';
import { ToolCall } from './types';

export function ToolCallIndicator({ tool }: { tool: ToolCall }) {
  const statusColors = {
    pending: 'bg-gray-200',
    running: 'bg-yellow-200 animate-pulse',
    complete: 'bg-green-200',
    error: 'bg-red-200'
  };

  return (
    <div className={`p-3 rounded-lg ${statusColors[tool.status]}`}>
      <div className="flex items-center gap-2">
        <span className="font-mono text-sm">{tool.name}</span>
        <span className="text-xs text-gray-600">
          {tool.status === 'running' ? 'Running...' : tool.status}
        </span>
      </div>
    </div>
  );
}
```

### User Prompt Modal: `UserPromptModal.tsx`

```tsx
import React, { useState } from 'react';
import { UserPrompt } from './types';

interface Props {
  prompt: UserPrompt;
  onRespond: (response: string) => void;
}

export function UserPromptModal({ prompt, onRespond }: Props) {
  const [input, setInput] = useState('');

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl p-6 max-w-md w-full">
        <h3 className="text-lg font-semibold mb-4">{prompt.question}</h3>

        {prompt.type === 'choice' && prompt.options ? (
          <div className="space-y-2">
            {prompt.options.map(option => (
              <button
                key={option}
                onClick={() => onRespond(option)}
                className="w-full p-3 text-left border rounded-lg hover:bg-gray-50"
              >
                {option}
              </button>
            ))}
          </div>
        ) : (
          <form onSubmit={e => { e.preventDefault(); onRespond(input); }}>
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              className="w-full p-3 border rounded-lg mb-4"
              autoFocus
            />
            <button
              type="submit"
              className="w-full p-3 bg-blue-500 text-white rounded-lg"
            >
              Submit
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
```

## Key Features Implemented

1. **Streaming responses** - Real-time text display
2. **Function calling** - Custom domain tools
3. **Code interpreter** - Built-in code execution
4. **Tool status UI** - Shows when tools are running
5. **User prompts** - Agent can ask for clarification
6. **Stop generation** - Abort in-progress requests

---

# IMPLEMENTATION GUIDE 2: Claude API + MCP + Claude Agent SDK

Two approaches: (A) Direct Claude API with tool use, (B) Claude Agent SDK for autonomous agents.

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                     React Frontend                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │ Chat UI     │  │ Tool Results│  │ Agent Status        │   │
│  │ Component   │  │ Component   │  │ Component           │   │
│  └─────────────┘  └─────────────┘  └─────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                           │
                     HTTPS/SSE
                           │
┌──────────────────────────────────────────────────────────────┐
│              Backend API (Node.js/Python)                     │
│                                                               │
│  Option A: Claude API + Tool Use                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Messages API → Tool Loop → Execute → Return Result      │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  Option B: Claude Agent SDK (autonomous)                      │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Agent SDK → Built-in tools + MCP → Autonomous execution │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  MCP Servers (extensible tools)                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │Filesystem│ │ Python   │ │Playwright│ │Your APIs │        │
│  │  Server  │ │ Sandbox  │ │ Browser  │ │  Server  │        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
└──────────────────────────────────────────────────────────────┘
```

## Option A: Claude API with Tool Use (Direct Control)

### Backend: `server.ts`

```typescript
import express from 'express';
import Anthropic from '@anthropic-ai/sdk';

const app = express();
app.use(express.json());

const anthropic = new Anthropic();

// Define tools (same format works with MCP)
const tools: Anthropic.Tool[] = [
  {
    name: "search_knowledge_base",
    description: "Search your product's knowledge base for documentation. Returns relevant articles and code examples.",
    input_schema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "Search query"
        },
        category: {
          type: "string",
          enum: ["docs", "api", "tutorials"],
          description: "Category to search"
        }
      },
      required: ["query"]
    }
  },
  {
    name: "run_code",
    description: "Execute Python code in a sandboxed environment. Returns stdout, stderr, and any generated files.",
    input_schema: {
      type: "object",
      properties: {
        code: { type: "string", description: "Python code to execute" },
        timeout: { type: "number", description: "Max execution time in seconds" }
      },
      required: ["code"]
    }
  },
  {
    name: "ask_user",
    description: "Ask the user a clarifying question when you need more information to proceed.",
    input_schema: {
      type: "object",
      properties: {
        question: { type: "string" },
        options: {
          type: "array",
          items: { type: "string" },
          description: "Optional: multiple choice options"
        }
      },
      required: ["question"]
    }
  }
];

// Tool execution
async function executeTool(name: string, input: any): Promise<string> {
  switch (name) {
    case "search_knowledge_base":
      return JSON.stringify(await yourKnowledgeBaseSearch(input.query, input.category));

    case "run_code":
      return JSON.stringify(await yourPythonSandbox(input.code, input.timeout));

    case "ask_user":
      // This is handled specially - we return it to the frontend
      return JSON.stringify({ type: "user_input_required", ...input });

    default:
      return JSON.stringify({ error: `Unknown tool: ${name}` });
  }
}

// The agentic loop
async function* agentLoop(
  messages: Anthropic.MessageParam[],
  onToolCall: (name: string, input: any) => void
): AsyncGenerator<any> {
  let continueLoop = true;

  while (continueLoop) {
    // Create message with streaming
    const stream = anthropic.messages.stream({
      model: "claude-sonnet-4-5-20250514",
      max_tokens: 4096,
      tools,
      messages
    });

    let response: Anthropic.Message | null = null;

    // Stream text deltas to the client
    for await (const event of stream) {
      if (event.type === 'content_block_delta') {
        if (event.delta.type === 'text_delta') {
          yield { type: 'text_delta', text: event.delta.text };
        }
      }
    }

    // Get the final message
    response = await stream.finalMessage();

    // Check if we need to execute tools
    if (response.stop_reason === 'tool_use') {
      const toolUseBlocks = response.content.filter(
        block => block.type === 'tool_use'
      );

      // Process each tool call
      const toolResults: Anthropic.ToolResultBlockParam[] = [];

      for (const toolUse of toolUseBlocks) {
        onToolCall(toolUse.name, toolUse.input);
        yield { type: 'tool_start', name: toolUse.name, id: toolUse.id };

        // Check if this is an "ask_user" tool
        if (toolUse.name === 'ask_user') {
          // Pause and wait for user input
          yield {
            type: 'user_input_required',
            toolUseId: toolUse.id,
            question: (toolUse.input as any).question,
            options: (toolUse.input as any).options
          };
          // The caller will resume with user input
          return;
        }

        const result = await executeTool(toolUse.name, toolUse.input);
        yield { type: 'tool_complete', id: toolUse.id, result };

        toolResults.push({
          type: 'tool_result',
          tool_use_id: toolUse.id,
          content: result
        });
      }

      // Add assistant message and tool results to continue
      messages.push({ role: 'assistant', content: response.content });
      messages.push({ role: 'user', content: toolResults });

    } else {
      // No more tool calls, we're done
      continueLoop = false;
      yield { type: 'done', content: response.content };
    }
  }
}

// API endpoint
app.post('/api/chat', async (req, res) => {
  const { messages } = req.body;

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');

  const anthropicMessages: Anthropic.MessageParam[] = messages.map(m => ({
    role: m.role,
    content: m.content
  }));

  try {
    for await (const event of agentLoop(anthropicMessages, () => {})) {
      res.write(`data: ${JSON.stringify(event)}\n\n`);

      // If user input is required, stop and wait
      if (event.type === 'user_input_required') {
        return;
      }
    }
    res.write('data: [DONE]\n\n');
  } catch (error) {
    res.write(`data: ${JSON.stringify({ type: 'error', error: error.message })}\n\n`);
  }
  res.end();
});

// Continue after user provides input
app.post('/api/chat/continue', async (req, res) => {
  const { messages, toolUseId, userResponse } = req.body;

  res.setHeader('Content-Type', 'text/event-stream');

  // Add the tool result with user's response
  const anthropicMessages: Anthropic.MessageParam[] = [
    ...messages,
    {
      role: 'user',
      content: [{
        type: 'tool_result',
        tool_use_id: toolUseId,
        content: JSON.stringify({ user_response: userResponse })
      }]
    }
  ];

  try {
    for await (const event of agentLoop(anthropicMessages, () => {})) {
      res.write(`data: ${JSON.stringify(event)}\n\n`);
    }
    res.write('data: [DONE]\n\n');
  } catch (error) {
    res.write(`data: ${JSON.stringify({ type: 'error', error: error.message })}\n\n`);
  }
  res.end();
});

app.listen(3001);
```

## Option B: Claude Agent SDK (Autonomous Agents)

The Agent SDK gives you Claude Code's capabilities as a library - autonomous file reading, code execution, web search, and MCP support built-in.

### Install

```bash
# Install Claude Code (runtime requirement)
curl -fsSL https://claude.ai/install.sh | bash

# Install SDK
npm install @anthropic-ai/claude-agent-sdk
```

### Backend: `agent-server.ts`

```typescript
import express from 'express';
import { query, ClaudeAgentOptions } from '@anthropic-ai/claude-agent-sdk';

const app = express();
app.use(express.json());

// Define custom agents (subagents)
const agents = {
  "code-reviewer": {
    description: "Expert code reviewer for security and quality analysis",
    prompt: "Analyze code for bugs, security issues, and best practices.",
    tools: ["Read", "Glob", "Grep"]
  },
  "data-analyst": {
    description: "Data analysis specialist with Python execution",
    prompt: "Analyze data, create visualizations, and provide insights.",
    tools: ["Read", "Bash", "Write"]
  }
};

// MCP server configurations
const mcpServers = {
  // Browser automation
  playwright: {
    command: "npx",
    args: ["@playwright/mcp@latest"]
  },
  // Your custom MCP server
  "your-api": {
    command: "node",
    args: ["./mcp-servers/your-api-server.js"]
  },
  // Python code execution
  python: {
    command: "npx",
    args: ["@anthropic/mcp-server-python"]
  }
};

app.post('/api/agent', async (req, res) => {
  const { prompt, sessionId } = req.body;

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');

  try {
    const options: ClaudeAgentOptions = {
      // Built-in tools
      allowedTools: [
        "Read",      // Read files
        "Write",     // Write files
        "Edit",      // Edit files
        "Bash",      // Run commands
        "Glob",      // Find files
        "Grep",      // Search content
        "WebSearch", // Search the web
        "WebFetch",  // Fetch URLs
        "Task",      // Spawn subagents
        "AskUserQuestion"  // Ask user for input
      ],

      // Custom subagents
      agents,

      // MCP servers for extended capabilities
      mcpServers,

      // Resume previous session if provided
      resume: sessionId || undefined,

      // Permission mode
      permissionMode: "acceptEdits", // or "bypassPermissions" for fully autonomous

      // Hooks for customization
      hooks: {
        // Log all tool uses
        PostToolUse: [{
          matcher: ".*",
          hooks: [async (input, toolUseId) => {
            console.log(`Tool used: ${input.tool_name}`);
            return {};
          }]
        }],
        // Validate before dangerous operations
        PreToolUse: [{
          matcher: "Bash|Write",
          hooks: [async (input) => {
            // Add your validation logic
            return {}; // Return { block: true } to prevent
          }]
        }]
      }
    };

    // Run the agent
    for await (const message of query({ prompt, options })) {
      // Handle different message types
      if (message.type === 'system' && message.subtype === 'init') {
        res.write(`data: ${JSON.stringify({
          type: 'session_start',
          sessionId: message.session_id
        })}\n\n`);
      }

      else if (message.type === 'assistant') {
        // Text from Claude
        if (message.message?.content) {
          for (const block of message.message.content) {
            if (block.type === 'text') {
              res.write(`data: ${JSON.stringify({
                type: 'text',
                text: block.text
              })}\n\n`);
            }
            else if (block.type === 'tool_use') {
              res.write(`data: ${JSON.stringify({
                type: 'tool_call',
                name: block.name,
                id: block.id
              })}\n\n`);
            }
          }
        }
      }

      else if (message.type === 'user' && message.message?.content) {
        // Tool results
        for (const block of message.message.content) {
          if (block.type === 'tool_result') {
            res.write(`data: ${JSON.stringify({
              type: 'tool_result',
              toolUseId: block.tool_use_id,
              content: block.content
            })}\n\n`);
          }
        }
      }

      else if ('result' in message) {
        // Final result
        res.write(`data: ${JSON.stringify({
          type: 'done',
          result: message.result
        })}\n\n`);
      }
    }

    res.write('data: [DONE]\n\n');
  } catch (error) {
    res.write(`data: ${JSON.stringify({ type: 'error', error: error.message })}\n\n`);
  }
  res.end();
});

// Handle user input when agent asks
app.post('/api/agent/respond', async (req, res) => {
  const { sessionId, response } = req.body;

  // Resume the session with user's response
  for await (const message of query({
    prompt: response,
    options: { resume: sessionId }
  })) {
    // Stream the continuation...
  }

  res.json({ status: 'continued' });
});

app.listen(3001);
```

### Creating a Custom MCP Server

```typescript
// mcp-servers/your-api-server.ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new Server({
  name: "your-api-server",
  version: "1.0.0"
}, {
  capabilities: {
    tools: {}
  }
});

// Define your tools
server.setRequestHandler("tools/list", async () => ({
  tools: [
    {
      name: "get_customer",
      description: "Retrieve customer information by ID",
      inputSchema: {
        type: "object",
        properties: {
          customerId: { type: "string" }
        },
        required: ["customerId"]
      }
    },
    {
      name: "create_ticket",
      description: "Create a support ticket",
      inputSchema: {
        type: "object",
        properties: {
          title: { type: "string" },
          description: { type: "string" },
          priority: { type: "string", enum: ["low", "medium", "high"] }
        },
        required: ["title", "description"]
      }
    }
  ]
}));

// Handle tool execution
server.setRequestHandler("tools/call", async (request) => {
  const { name, arguments: args } = request.params;

  switch (name) {
    case "get_customer":
      const customer = await yourDatabase.getCustomer(args.customerId);
      return { content: [{ type: "text", text: JSON.stringify(customer) }] };

    case "create_ticket":
      const ticket = await yourTicketSystem.create(args);
      return { content: [{ type: "text", text: JSON.stringify(ticket) }] };

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
});

// Start the server
const transport = new StdioServerTransport();
await server.connect(transport);
```

## React Frontend for Claude Agent SDK

```typescript
// useClaudeAgent.ts
import { useState, useCallback } from 'react';

interface AgentMessage {
  type: 'text' | 'tool_call' | 'tool_result' | 'user_input' | 'done';
  content?: string;
  toolName?: string;
  toolId?: string;
}

export function useClaudeAgent() {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [pendingInput, setPendingInput] = useState<any>(null);

  const runAgent = useCallback(async (prompt: string) => {
    setIsRunning(true);
    setMessages([]);

    const response = await fetch('/api/agent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, sessionId })
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    while (reader) {
      const { done, value } = await reader.read();
      if (done) break;

      const lines = decoder.decode(value).split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ') && line !== 'data: [DONE]') {
          const event = JSON.parse(line.slice(6));

          switch (event.type) {
            case 'session_start':
              setSessionId(event.sessionId);
              break;
            case 'text':
              setMessages(prev => [...prev, { type: 'text', content: event.text }]);
              break;
            case 'tool_call':
              setMessages(prev => [...prev, {
                type: 'tool_call',
                toolName: event.name,
                toolId: event.id
              }]);
              break;
            case 'tool_result':
              setMessages(prev => [...prev, {
                type: 'tool_result',
                toolId: event.toolUseId,
                content: event.content
              }]);
              break;
            case 'user_input_required':
              setPendingInput(event);
              break;
          }
        }
      }
    }

    setIsRunning(false);
  }, [sessionId]);

  const respondToAgent = useCallback(async (response: string) => {
    if (!pendingInput || !sessionId) return;

    await fetch('/api/agent/respond', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sessionId, response })
    });

    setPendingInput(null);
  }, [pendingInput, sessionId]);

  return {
    messages,
    isRunning,
    runAgent,
    pendingInput,
    respondToAgent,
    sessionId
  };
}
```

## Key Differences: OpenAI vs Claude

| Feature | OpenAI Responses API | Claude API + MCP |
|---------|---------------------|------------------|
| Code Execution | Built-in (code_interpreter) | MCP server (setup required) |
| Tool Format | JSON Schema | JSON Schema (same) |
| Streaming | SSE with event types | SSE with content blocks |
| User Prompts | Custom implementation | AskUserQuestion tool (Agent SDK) |
| Extensibility | Functions only | MCP ecosystem |
| Autonomous Agent | Manual loop | Agent SDK handles it |

## Claude Agent SDK vs Direct API

| Aspect | Direct Claude API | Claude Agent SDK |
|--------|------------------|------------------|
| Control | Full control over loop | SDK manages loop |
| Built-in Tools | None (you implement) | Read, Write, Bash, Grep, etc. |
| MCP | Manual integration | Built-in support |
| Sessions | Manual state management | Automatic persistence |
| Subagents | Build yourself | Declarative config |
| Best For | Custom behavior | Rapid development |

---

## Recommendation for Your Use Case

Based on your requirements:
- **Priority**: Speed to market
- **Model**: Single provider OK
- **Scale**: 100-1000 concurrent users
- **Must-haves**: Remote code execution, tool/API integrations

### Primary Recommendation: OpenAI Responses API

**Why:**
1. **Built-in code interpreter** - No need to set up E2B/Modal/sandboxes
2. **Function calling** - Easy tool/API integrations with JSON schemas
3. **Managed infrastructure** - Handles your scale without ops overhead
4. **Speed** - You can have a working prototype in days

**Implementation path:**
```
Week 1: OpenAI Responses API + built-in code interpreter
Week 2: Add custom functions for your domain-specific tools
Week 3: Build conversation UI, integrate with your product
Week 4: Add memory/persistence layer (your DB or OpenAI threads)
```

**Escape hatch:** If you hit limits later, you can migrate to LangGraph/Agno while keeping OpenAI as the model provider. The function schemas you define are portable.

### Alternative: Claude API + MCP

**Why consider:**
- Better reasoning for complex tasks (especially Claude 3.5/Opus)
- MCP ecosystem is growing fast (future-proofing)
- Tool Search Tool for dynamic tool discovery

**Trade-off:** Code execution requires setting up an MCP server (e.g., Python sandbox MCP server) vs OpenAI's built-in interpreter.

### What You Don't Need (Yet)

- **LangGraph/CrewAI** - Overkill for speed-to-market; add later if needed
- **Google ADK** - Enterprise-focused, more setup than you need at this scale
- **Multi-agent orchestration** - Start with single agent + tools, evolve later

---

## Sources

- [Speakeasy: Architecture patterns for agentic applications](https://www.speakeasy.com/mcp/using-mcp/ai-agents/architecture-patterns)
- [Microsoft: AI Agent Orchestration Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)
- [LangWatch: Best AI Agent Frameworks 2025](https://langwatch.ai/blog/best-ai-agent-frameworks-in-2025-comparing-langgraph-dspy-crewai-agno-and-more)
- [Anthropic: Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)
- [Anthropic: Advanced tool use](https://www.anthropic.com/engineering/advanced-tool-use)
- [a16z: Deep dive into MCP](https://a16z.com/a-deep-dive-into-mcp-and-the-future-of-ai-tooling/)
- [Klavis: MCP design patterns](https://www.klavis.ai/blog/less-is-more-mcp-design-patterns-for-ai-agents)
- [mcp-agent framework](https://github.com/lastmile-ai/mcp-agent)
- [Claude Agent SDK vs Google ADK](https://prabha.ai/writing/2025/12/21/claude-agent-sdk-vs-google-adk/)
- [OpenAI Agents SDK vs Claude Agent SDK](https://medium.com/@richardhightower/claude-agent-sdk-vs-openai-agentkit-a-developers-guide-to-building-ai-agents-95780ec777ea)
- [Building AI Agents: LangChain vs OpenAI](https://medium.com/@fahey_james/building-ai-agents-in-2025-langchain-vs-openai-d26fbceea05d)
- [MCP vs Function Calling](https://www.descope.com/blog/post/mcp-vs-function-calling)
- [Claude Agent SDK Overview](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Claude Tool Use Implementation](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use)
- [MCP Architecture](https://modelcontextprotocol.io/docs/learn/architecture)
- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)

---

## Quick Start Recommendations

### If You Choose OpenAI:
1. Start with the Responses API + code_interpreter
2. Add custom functions for your domain tools
3. Use the React frontend pattern above
4. Scale: OpenAI handles infrastructure

### If You Choose Claude:
1. **For speed**: Use Claude Agent SDK with built-in tools
2. **For control**: Use direct Claude API with tool use loop
3. Add MCP servers for extensibility (Python sandbox, Playwright, your APIs)
4. Scale: You manage infrastructure, but get MCP ecosystem

### Hybrid Approach (Future-Proof):
1. Build your tool definitions as MCP servers
2. Connect to Claude today
3. MCP is becoming a standard - OpenAI and others are adopting it
4. Same tools work across providers
