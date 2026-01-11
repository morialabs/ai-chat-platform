"use client";

import { createContext, useContext, type ReactNode } from "react";

interface ChatContextValue {
  sessionId: string | null;
  respondToQuestion: (answers: Record<string, string>) => void;
}

const ChatContext = createContext<ChatContextValue | null>(null);

export function useChatContext(): ChatContextValue {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChatContext must be used within ChatContextProvider");
  }
  return context;
}

interface ChatContextProviderProps {
  children: ReactNode;
  sessionId: string | null;
  respondToQuestion: (answers: Record<string, string>) => void;
}

export function ChatContextProvider({
  children,
  sessionId,
  respondToQuestion,
}: ChatContextProviderProps): React.JSX.Element {
  return (
    <ChatContext.Provider value={{ sessionId, respondToQuestion }}>
      {children}
    </ChatContext.Provider>
  );
}
