"use client";

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  useRef,
  type ReactNode,
} from "react";
import { useChat, type Message } from "@ai-sdk/react";

/**
 * JSON value type for data from the stream.
 */
type JSONValue =
  | null
  | string
  | number
  | boolean
  | { [key: string]: JSONValue }
  | JSONValue[];

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
 * Type for session data from the stream.
 */
interface SessionData {
  session_id?: string;
  cost?: number;
}

/**
 * Extract session_id from data array (sent via code "2" events).
 */
function extractSessionId(data: JSONValue[] | undefined): string | null {
  if (!data || !Array.isArray(data)) return null;

  for (const item of data) {
    if (
      item &&
      typeof item === "object" &&
      "session_id" in item &&
      typeof (item as SessionData).session_id === "string"
    ) {
      return (item as SessionData).session_id!;
    }
  }
  return null;
}

/**
 * Provides chat functionality using Vercel AI SDK.
 * Manages conversation state, streaming, and session persistence.
 */
export function ChatProvider({ children }: ChatProviderProps): React.JSX.Element {
  const [sessionId, setSessionId] = useState<string | null>(null);
  // Use a ref to ensure the latest sessionId is always used in requests
  const sessionIdRef = useRef<string | null>(null);

  // Keep ref in sync with state
  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  const chat = useChat({
    api: "/api/chat",
    // Use streamProtocol to match our backend format
    streamProtocol: "data",
    // Use experimental_prepareRequestBody to dynamically include session_id
    // This ensures the latest sessionId is always used, avoiding stale closures
    experimental_prepareRequestBody: ({ messages, requestData }) => {
      return {
        messages,
        data: requestData,
        session_id: sessionIdRef.current,
      };
    },
    // Extract session_id from response headers (for existing sessions)
    onResponse: (response) => {
      const newSessionId = response.headers.get("x-session-id");
      if (newSessionId) {
        setSessionId(newSessionId);
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

  // Extract session_id from data stream (code "2" events)
  // This is the primary method for new sessions since headers aren't available
  useEffect(() => {
    if (!sessionId && chat.data) {
      const newSessionId = extractSessionId(chat.data);
      if (newSessionId) {
        // eslint-disable-next-line react-hooks/set-state-in-effect -- Syncing external stream data into state
        setSessionId(newSessionId);
      }
    }
  }, [chat.data, sessionId]);

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
