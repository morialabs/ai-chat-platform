"use client";

import React, { useCallback, useRef } from "react";
import { Send, Square } from "lucide-react";
import { useChatContext } from "./ChatProvider";

/**
 * Chat input component with text field and submit button.
 * Handles form submission and shows loading state.
 */
export function ChatInput(): React.JSX.Element {
  const { input, setInput, handleSubmit, isLoading, stop, status } =
    useChatContext();
  const formRef = useRef<HTMLFormElement>(null);

  const onSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (!input.trim() || isLoading) return;
      handleSubmit(e);
    },
    [input, isLoading, handleSubmit]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (input.trim() && !isLoading) {
          formRef.current?.requestSubmit();
        }
      }
    },
    [input, isLoading]
  );

  const isStreaming = status === "streaming";

  return (
    <form
      ref={formRef}
      onSubmit={onSubmit}
      className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4"
    >
      <div className="flex items-end gap-2 max-w-4xl mx-auto">
        <div className="flex-1 relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            disabled={isLoading && !isStreaming}
            rows={1}
            className="w-full resize-none p-3 pr-12 border border-gray-300 dark:border-gray-600 rounded-lg
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-400
                       disabled:opacity-50 disabled:cursor-not-allowed
                       min-h-[48px] max-h-[200px]"
            style={{
              height: "auto",
              minHeight: "48px",
            }}
          />
        </div>

        {isStreaming ? (
          <button
            type="button"
            onClick={stop}
            className="flex items-center justify-center w-12 h-12 rounded-lg
                       bg-red-500 hover:bg-red-600 text-white
                       transition-colors duration-200"
            aria-label="Stop generation"
          >
            <Square className="w-5 h-5" fill="currentColor" />
          </button>
        ) : (
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="flex items-center justify-center w-12 h-12 rounded-lg
                       bg-blue-500 hover:bg-blue-600 text-white
                       disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors duration-200"
            aria-label="Send message"
          >
            <Send className="w-5 h-5" />
          </button>
        )}
      </div>

      <p className="text-xs text-gray-400 dark:text-gray-500 text-center mt-2">
        Press Enter to send, Shift+Enter for new line
      </p>
    </form>
  );
}
