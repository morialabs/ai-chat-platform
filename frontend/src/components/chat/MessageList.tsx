"use client";

import React, { useEffect, useRef } from "react";
import type { Message } from "@ai-sdk/react";
import type { ToolInvocation } from "ai";
import { User, Bot } from "lucide-react";
import { useChatContext } from "./ChatProvider";
import { MarkdownContent } from "./MarkdownContent";
import { ToolCallDisplay } from "./ToolCallDisplay";
import { AskUserQuestionUI } from "./AskUserQuestionUI";
import type { UserQuestion } from "@/lib/types";

/**
 * Renders the list of messages in the conversation.
 * Auto-scrolls to bottom when new messages arrive.
 */
export function MessageList(): React.JSX.Element {
  const { messages, isLoading, respondToQuestion } = useChatContext();
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  if (messages.length === 0) {
    return <WelcomeMessage />;
  }

  return (
    <div className="space-y-4 max-w-4xl mx-auto">
      {messages.map((message) => (
        <MessageItem
          key={message.id}
          message={message}
          onRespondToQuestion={respondToQuestion}
        />
      ))}

      {/* Loading indicator */}
      {isLoading && messages[messages.length - 1]?.role === "user" && (
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
            <Bot className="w-5 h-5 text-gray-600 dark:text-gray-300" />
          </div>
          <div className="flex-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
              <div
                className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                style={{ animationDelay: "0.1s" }}
              />
              <div
                className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                style={{ animationDelay: "0.2s" }}
              />
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}

/**
 * Welcome message shown when there are no messages.
 */
function WelcomeMessage(): React.JSX.Element {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-4">
      <div className="w-16 h-16 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mb-4">
        <Bot className="w-8 h-8 text-blue-500" />
      </div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
        AI Assistant
      </h1>
      <p className="text-gray-500 dark:text-gray-400 max-w-md">
        Ask me anything. I can search documentation, analyze code, answer
        questions, and help with research.
      </p>
    </div>
  );
}

interface MessageItemProps {
  message: Message;
  onRespondToQuestion: (
    toolCallId: string,
    answers: Record<string, string>
  ) => void;
}

/**
 * Renders a single message (user or assistant).
 */
function MessageItem({
  message,
  onRespondToQuestion,
}: MessageItemProps): React.JSX.Element {
  if (message.role === "user") {
    return <UserMessage content={message.content} />;
  }

  return (
    <AssistantMessage
      message={message}
      onRespondToQuestion={onRespondToQuestion}
    />
  );
}

interface UserMessageProps {
  content: string;
}

/**
 * Renders a user message.
 */
function UserMessage({ content }: UserMessageProps): React.JSX.Element {
  return (
    <div className="flex items-start gap-3 justify-end">
      <div className="flex-1 max-w-[80%]">
        <div className="bg-blue-500 text-white rounded-lg p-4 ml-auto w-fit max-w-full">
          <p className="whitespace-pre-wrap break-words">{content}</p>
        </div>
      </div>
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
        <User className="w-5 h-5 text-blue-500" />
      </div>
    </div>
  );
}

interface AssistantMessageProps {
  message: Message;
  onRespondToQuestion: (
    toolCallId: string,
    answers: Record<string, string>
  ) => void;
}

/**
 * Renders an assistant message with text content and tool invocations.
 */
function AssistantMessage({
  message,
  onRespondToQuestion,
}: AssistantMessageProps): React.JSX.Element {
  const hasContent = message.content && message.content.trim().length > 0;
  const hasToolInvocations =
    message.toolInvocations && message.toolInvocations.length > 0;

  return (
    <div className="flex items-start gap-3">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
        <Bot className="w-5 h-5 text-gray-600 dark:text-gray-300" />
      </div>
      <div className="flex-1 max-w-[80%] space-y-3">
        {/* Text content */}
        {hasContent && (
          <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4">
            <MarkdownContent content={message.content} />
          </div>
        )}

        {/* Tool invocations */}
        {hasToolInvocations &&
          message.toolInvocations!.map((toolInvocation) => (
            <ToolInvocationItem
              key={toolInvocation.toolCallId}
              toolInvocation={toolInvocation}
              onRespondToQuestion={onRespondToQuestion}
            />
          ))}
      </div>
    </div>
  );
}

interface ToolInvocationItemProps {
  toolInvocation: ToolInvocation;
  onRespondToQuestion: (
    toolCallId: string,
    answers: Record<string, string>
  ) => void;
}

/**
 * Extracts result string and error status from a tool invocation result.
 * Handles various formats: string, object with result/error keys, or JSON.
 */
function extractToolResult(rawResult: unknown): {
  result: string | undefined;
  isError: boolean;
} {
  if (rawResult === undefined || rawResult === null) {
    return { result: undefined, isError: false };
  }

  if (typeof rawResult === "string") {
    return { result: rawResult, isError: false };
  }

  if (typeof rawResult === "object") {
    const obj = rawResult as Record<string, unknown>;
    const isError = Boolean(obj.isError) || "error" in obj;

    if ("result" in obj) {
      return { result: String(obj.result), isError };
    }
    if ("error" in obj) {
      return { result: String(obj.error), isError: true };
    }
    return { result: JSON.stringify(rawResult), isError };
  }

  return { result: JSON.stringify(rawResult), isError: false };
}

/**
 * Renders a tool invocation (either AskUserQuestion or regular tool).
 */
function ToolInvocationItem({
  toolInvocation,
  onRespondToQuestion,
}: ToolInvocationItemProps): React.JSX.Element {
  // Handle AskUserQuestion specially
  if (toolInvocation.toolName === "AskUserQuestion") {
    const questions = (toolInvocation.args?.questions || []) as UserQuestion[];
    const result =
      toolInvocation.state === "result"
        ? (toolInvocation.result as string)
        : undefined;

    return (
      <AskUserQuestionUI
        questions={questions}
        result={result}
        onRespond={(answers) =>
          onRespondToQuestion(toolInvocation.toolCallId, answers)
        }
      />
    );
  }

  // Regular tool call - extract status and result
  const rawResult =
    toolInvocation.state === "result" ? toolInvocation.result : undefined;
  const { result, isError } = extractToolResult(rawResult);

  const status: "running" | "complete" | "error" =
    toolInvocation.state !== "result"
      ? "running"
      : isError
        ? "error"
        : "complete";

  return (
    <ToolCallDisplay
      toolCall={{
        toolCallId: toolInvocation.toolCallId,
        toolName: toolInvocation.toolName,
        args: toolInvocation.args as Record<string, unknown>,
        result,
        status,
        isError,
      }}
    />
  );
}
