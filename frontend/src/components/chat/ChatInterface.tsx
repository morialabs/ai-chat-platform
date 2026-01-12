"use client";

import React from "react";
import { ChatProvider, useChatContext } from "./ChatProvider";
import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
import { AlertCircle } from "lucide-react";

/**
 * Error banner component displayed when there's a chat error.
 */
function ErrorBanner(): React.JSX.Element | null {
  const { error } = useChatContext();

  if (!error) return null;

  return (
    <div className="bg-red-50 dark:bg-red-900/20 border-t border-red-200 dark:border-red-800 p-4">
      <div className="flex items-center gap-2 max-w-4xl mx-auto">
        <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
        <p className="text-sm text-red-600 dark:text-red-400">{error.message}</p>
      </div>
    </div>
  );
}

/**
 * Main chat content area with messages and input.
 */
function ChatContent(): React.JSX.Element {
  return (
    <div className="flex flex-col h-screen bg-white dark:bg-gray-900">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4">
        <MessageList />
      </div>

      {/* Error banner */}
      <ErrorBanner />

      {/* Input area */}
      <ChatInput />
    </div>
  );
}

/**
 * Main chat interface component.
 * Provides the chat context and renders the chat UI.
 */
export function ChatInterface(): React.JSX.Element {
  return (
    <ChatProvider>
      <ChatContent />
    </ChatProvider>
  );
}
