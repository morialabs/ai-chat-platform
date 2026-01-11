"use client";

import type { ReactNode } from "react";

import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
  type ChatModelRunResult,
} from "@assistant-ui/react";

import type { StreamEvent, UserPrompt } from "@/lib/types";

interface ToolCallState {
  toolCallId: string;
  toolName: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  args: any;
  argsText: string;
  result?: unknown;
  isError?: boolean;
}

function buildContent(
  text: string,
  toolCalls: Map<string, ToolCallState>
): ChatModelRunResult["content"] {
  const textPart = text ? [{ type: "text" as const, text }] : [];
  const toolCallParts = Array.from(toolCalls.values()).map((tc) => ({
    type: "tool-call" as const,
    toolCallId: tc.toolCallId,
    toolName: tc.toolName,
    args: tc.args,
    argsText: tc.argsText,
    result: tc.result,
    isError: tc.isError,
  }));

  return [...textPart, ...toolCallParts];
}

const createChatAdapter = (
  sessionId: string | null,
  onSessionId: (id: string) => void,
  onUserInputRequired: (data: UserPrompt) => void
): ChatModelAdapter => {
  return {
    async *run({ messages, abortSignal }): AsyncGenerator<ChatModelRunResult> {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.role !== "user") return;

      const userContent = lastMessage.content
        .filter((c): c is { type: "text"; text: string } => c.type === "text")
        .map((c) => c.text)
        .join("\n");

      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";
      let accumulatedText = "";
      const toolCalls = new Map<string, ToolCallState>();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") continue;

            try {
              const event: StreamEvent = JSON.parse(data);

              switch (event.type) {
                case "text":
                  accumulatedText += event.text || "";
                  yield {
                    content: [{ type: "text", text: accumulatedText }],
                  };
                  break;

                case "tool_start":
                  if (event.tool_id && event.tool_name) {
                    toolCalls.set(event.tool_id, {
                      toolCallId: event.tool_id,
                      toolName: event.tool_name,
                      args: (event.tool_input as Record<string, unknown>) || {},
                      argsText: JSON.stringify(event.tool_input || {}),
                    });
                    yield { content: buildContent(accumulatedText, toolCalls) };
                  }
                  break;

                case "tool_result":
                  if (event.tool_id) {
                    const tc = toolCalls.get(event.tool_id);
                    if (tc) {
                      tc.result = event.tool_result;
                      tc.isError = event.is_error;
                      yield { content: buildContent(accumulatedText, toolCalls) };
                    }
                  }
                  break;

                case "user_input_required":
                  // Extract questions from the event (they can be at top level or in tool_input)
                  const questions =
                    event.questions ||
                    (event.tool_input as { questions?: UserPrompt["questions"] })?.questions ||
                    [];
                  onUserInputRequired({ questions });
                  break;

                case "done":
                  if (event.session_id) {
                    onSessionId(event.session_id);
                  }
                  break;

                case "error":
                  // Clear session ID if session expired/not found
                  if (
                    event.text?.includes("Session not found") ||
                    event.text?.includes("expired")
                  ) {
                    onSessionId("");
                  }
                  throw new Error(event.error || event.text || "Unknown error");
              }
            } catch (e) {
              if (e instanceof SyntaxError) {
                console.error("JSON parse error:", e, "Data:", data);
              } else {
                throw e;
              }
            }
          }
        }
      }

      yield {
        content: buildContent(accumulatedText, toolCalls),
        status: { type: "complete", reason: "stop" },
      };
    },
  };
};

interface ChatProviderProps {
  children: ReactNode;
  sessionId?: string | null;
  onSessionIdChange?: (id: string) => void;
  onUserInputRequired?: (data: UserPrompt) => void;
}

export function ChatProvider({
  children,
  sessionId = null,
  onSessionIdChange = () => {},
  onUserInputRequired = () => {},
}: ChatProviderProps): ReactNode {
  const adapter = createChatAdapter(sessionId, onSessionIdChange, onUserInputRequired);
  const runtime = useLocalRuntime(adapter);

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {children}
    </AssistantRuntimeProvider>
  );
}
