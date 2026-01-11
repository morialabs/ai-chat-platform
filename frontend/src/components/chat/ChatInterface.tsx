"use client";

import { useState, useCallback } from "react";
import {
  ThreadPrimitive,
  ComposerPrimitive,
  MessagePrimitive,
} from "@assistant-ui/react";

import { ChatProvider } from "./ChatProvider";
import { UserPromptModal } from "./UserPromptModal";
import type { UserPrompt } from "@/lib/types";

function ThreadMessages() {
  return (
    <ThreadPrimitive.Messages
      components={{
        UserMessage: () => (
          <MessagePrimitive.Root className="flex justify-end mb-4">
            <div className="bg-blue-500 text-white rounded-lg px-4 py-2 max-w-[80%]">
              <MessagePrimitive.Content />
            </div>
          </MessagePrimitive.Root>
        ),
        AssistantMessage: () => (
          <MessagePrimitive.Root className="flex justify-start mb-4">
            <div className="bg-gray-100 dark:bg-gray-800 dark:text-gray-100 rounded-lg px-4 py-2 max-w-[80%]">
              <MessagePrimitive.Content />
            </div>
          </MessagePrimitive.Root>
        ),
      }}
    />
  );
}

function ThreadComposer() {
  return (
    <ComposerPrimitive.Root className="p-4 border-t dark:border-gray-700">
      <div className="flex gap-2 max-w-4xl mx-auto">
        <ComposerPrimitive.Input
          placeholder="Ask a question..."
          className="flex-1 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-400"
        />
        <ComposerPrimitive.Send className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50">
          Send
        </ComposerPrimitive.Send>
      </div>
    </ComposerPrimitive.Root>
  );
}

function ThreadWelcome() {
  return (
    <ThreadPrimitive.Empty>
      <div className="text-center p-8">
        <h1 className="text-2xl font-bold mb-2">AI Assistant</h1>
        <p className="text-gray-500 dark:text-gray-400">
          Ask me anything. I can search documentation, analyze code, and help
          with research.
        </p>
      </div>
    </ThreadPrimitive.Empty>
  );
}

export function ChatInterface() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [pendingPrompt, setPendingPrompt] = useState<UserPrompt | null>(null);

  const handleUserInputRequired = useCallback((data: UserPrompt) => {
    setPendingPrompt(data);
  }, []);

  const handlePromptResponse = useCallback(
    async (answers: Record<string, string>) => {
      if (!sessionId) return;

      await fetch("/api/chat/respond", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          response: JSON.stringify(answers),
        }),
      });

      setPendingPrompt(null);
    },
    [sessionId]
  );

  return (
    <ChatProvider
      sessionId={sessionId}
      onSessionIdChange={setSessionId}
      onUserInputRequired={handleUserInputRequired}
    >
      <div className="flex flex-col h-screen bg-white dark:bg-gray-900">
        <ThreadPrimitive.Root className="flex-1 flex flex-col">
          <ThreadPrimitive.Viewport className="flex-1 overflow-y-auto p-4">
            <ThreadWelcome />
            <ThreadMessages />
          </ThreadPrimitive.Viewport>
          <ThreadComposer />
        </ThreadPrimitive.Root>

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
