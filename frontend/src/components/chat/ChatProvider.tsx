"use client";

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import { useChat, type Message } from "@ai-sdk/react";

/**
 * Context value provided by ChatProvider.
 * Extends useChat return values with session management and question response.
 */
interface ChatContextValue {
  /** Current conversation messages */
  messages: Message[];
  /** Current input value */
  input: string;
  /** Set input value */
  setInput: (input: string) => void;
  /** Handle form submission */
  handleSubmit: (e: React.FormEvent) => void;
  /** Whether a response is being streamed */
  isLoading: boolean;
  /** Current error if any */
  error: Error | undefined;
  /** Current session ID for multi-turn conversations */
  sessionId: string | null;
  /** Add a tool result (for AskUserQuestion responses) */
  addToolResult: (params: { toolCallId: string; result: string }) => void;
  /** Respond to an AskUserQuestion tool call */
  respondToQuestion: (
    toolCallId: string,
    answers: Record<string, string>
  ) => void;
  /** Reload/retry the last message */
  reload: () => void;
  /** Stop current streaming */
  stop: () => void;
  /** Chat status */
  status: "streaming" | "submitted" | "ready" | "error";
}

const ChatContext = createContext<ChatContextValue | null>(null);

/**
 * Hook to access chat context.
 * Must be used within a ChatProvider.
 */
export function useChatContext(): ChatContextValue {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChatContext must be used within ChatProvider");
  }
  return context;
}

interface ChatProviderProps {
  children: ReactNode;
}

/**
 * Provides chat functionality using Vercel AI SDK.
 * Manages conversation state, streaming, and session persistence.
 */
export function ChatProvider({ children }: ChatProviderProps): React.JSX.Element {
  const [sessionId, setSessionId] = useState<string | null>(null);

  const chat = useChat({
    api: "/api/chat",
    // Include session_id in request body for multi-turn conversations
    body: {
      session_id: sessionId,
    },
    // Extract session_id from response headers
    onResponse: (response) => {
      const newSessionId = response.headers.get("x-session-id");
      if (newSessionId) {
        setSessionId(newSessionId);
      }
    },
    // Handle finish event metadata for session_id (backup)
    onFinish: (message, options) => {
      // Try to extract session_id from finish metadata if not in headers
      // The metadata is in the last message's annotations or we parse from stream
      if (!sessionId && options.finishReason === "stop") {
        // Session ID should have been set via onResponse or stream parsing
      }
    },
    // Handle tool calls - return undefined for AskUserQuestion to keep pending
    onToolCall: async ({ toolCall }) => {
      if (toolCall.toolName === "AskUserQuestion") {
        // Return undefined to keep tool in "call" state
        // UI will render the question form
        return undefined;
      }
      // Other tools should have been handled server-side
      return undefined;
    },
    // Handle errors
    onError: (error) => {
      // Check for session expiry
      if (
        error.message?.includes("Session not found") ||
        error.message?.includes("expired")
      ) {
        setSessionId(null);
      }
    },
  });

  /**
   * Respond to an AskUserQuestion tool call.
   * Submits the user's answers as a tool result.
   */
  const respondToQuestion = useCallback(
    (toolCallId: string, answers: Record<string, string>) => {
      chat.addToolResult({
        toolCallId,
        result: JSON.stringify(answers),
      });
    },
    [chat]
  );

  const contextValue: ChatContextValue = {
    messages: chat.messages,
    input: chat.input,
    setInput: chat.setInput,
    handleSubmit: chat.handleSubmit,
    isLoading: chat.isLoading,
    error: chat.error,
    sessionId,
    addToolResult: chat.addToolResult,
    respondToQuestion,
    reload: chat.reload,
    stop: chat.stop,
    status: chat.status,
  };

  return (
    <ChatContext.Provider value={contextValue}>{children}</ChatContext.Provider>
  );
}
