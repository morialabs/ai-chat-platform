import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MessageList } from "../MessageList";
import * as ChatProviderModule from "../ChatProvider";
import type { Message } from "@ai-sdk/react";

// Mock react-markdown and syntax highlighter
vi.mock("react-markdown", () => ({
  default: ({ children }: { children: string }) => <div>{children}</div>,
}));

vi.mock("remark-gfm", () => ({
  default: () => () => {},
}));

vi.mock("react-syntax-highlighter", () => ({
  Prism: ({ children }: { children: string }) => <pre>{children}</pre>,
}));

vi.mock("react-syntax-highlighter/dist/esm/styles/prism", () => ({
  oneDark: {},
}));

// Mock the ChatProvider context
const mockUseChatContext = vi.spyOn(ChatProviderModule, "useChatContext");

describe("MessageList", () => {
  const defaultContextValue = {
    messages: [] as Message[],
    isLoading: false,
    respondToQuestion: vi.fn(),
    input: "",
    setInput: vi.fn(),
    handleSubmit: vi.fn(),
    stop: vi.fn(),
    status: "ready" as const,
    error: undefined,
    sessionId: null,
    addToolResult: vi.fn(),
    reload: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseChatContext.mockReturnValue(defaultContextValue);
  });

  describe("empty state", () => {
    it("shows welcome message when no messages", () => {
      render(<MessageList />);

      expect(screen.getByText("AI Assistant")).toBeInTheDocument();
    });

    it("welcome message has correct content", () => {
      render(<MessageList />);

      expect(
        screen.getByText(/Ask me anything/i)
      ).toBeInTheDocument();
    });
  });

  describe("user messages", () => {
    it("renders user message with content", () => {
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        messages: [
          { id: "1", role: "user", content: "Hello, how are you?" },
        ] as Message[],
      });

      render(<MessageList />);

      expect(screen.getByText("Hello, how are you?")).toBeInTheDocument();
    });

    it("applies correct styling (blue background)", () => {
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        messages: [
          { id: "1", role: "user", content: "Test message" },
        ] as Message[],
      });

      render(<MessageList />);

      const messageDiv = screen.getByText("Test message").closest("div");
      expect(messageDiv).toHaveClass("bg-blue-500");
    });
  });

  describe("assistant messages", () => {
    it("renders assistant message content", () => {
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        messages: [
          { id: "1", role: "assistant", content: "I'm doing well, thanks!" },
        ] as Message[],
      });

      render(<MessageList />);

      expect(screen.getByText("I'm doing well, thanks!")).toBeInTheDocument();
    });

    it("applies correct styling (gray background)", () => {
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        messages: [
          { id: "1", role: "assistant", content: "Test response" },
        ] as Message[],
      });

      render(<MessageList />);

      // Find the message container with gray background
      const messageContainer = screen.getByText("Test response").closest(".bg-gray-100, .dark\\:bg-gray-800");
      expect(messageContainer).toBeInTheDocument();
    });
  });

  describe("tool invocations", () => {
    it("renders ToolCallDisplay for regular tools", () => {
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        messages: [
          {
            id: "1",
            role: "assistant",
            content: "",
            toolInvocations: [
              {
                toolCallId: "tool-1",
                toolName: "Read",
                state: "result",
                args: { file_path: "/test.txt" },
                result: { result: "File content", isError: false },
              },
            ],
          },
        ] as Message[],
      });

      render(<MessageList />);

      expect(screen.getByText("Read")).toBeInTheDocument();
    });

    it("renders AskUserQuestionUI for AskUserQuestion", () => {
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        messages: [
          {
            id: "1",
            role: "assistant",
            content: "",
            toolInvocations: [
              {
                toolCallId: "ask-1",
                toolName: "AskUserQuestion",
                state: "call",
                args: {
                  questions: [
                    {
                      question: "Choose one",
                      header: "Choice",
                      options: [{ label: "A", description: "Option A" }],
                      multiSelect: false,
                    },
                  ],
                },
              },
            ],
          },
        ] as Message[],
      });

      render(<MessageList />);

      expect(screen.getByText("Choose one")).toBeInTheDocument();
      expect(screen.getByText("Choice")).toBeInTheDocument();
    });

    it("shows running status for pending tools", () => {
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        messages: [
          {
            id: "1",
            role: "assistant",
            content: "",
            toolInvocations: [
              {
                toolCallId: "tool-1",
                toolName: "Bash",
                state: "call",
                args: { command: "ls" },
              },
            ],
          },
        ] as Message[],
      });

      const { container } = render(<MessageList />);

      // Check for spinner (running indicator)
      const spinner = container.querySelector(".animate-spin");
      expect(spinner).toBeInTheDocument();
    });
  });

  describe("loading state", () => {
    it("shows loading indicator when isLoading and last message is user", () => {
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        messages: [
          { id: "1", role: "user", content: "What time is it?" },
        ] as Message[],
        isLoading: true,
      });

      const { container } = render(<MessageList />);

      // Loading indicator has animated bouncing dots
      const bouncingDots = container.querySelectorAll(".animate-bounce");
      expect(bouncingDots.length).toBe(3);
    });

    it("hides loading indicator when not loading", () => {
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        messages: [
          { id: "1", role: "user", content: "Hello" },
        ] as Message[],
        isLoading: false,
      });

      const { container } = render(<MessageList />);

      const bouncingDots = container.querySelectorAll(".animate-bounce");
      expect(bouncingDots.length).toBe(0);
    });

    it("hides loading indicator when last message is assistant", () => {
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        messages: [
          { id: "1", role: "user", content: "Hello" },
          { id: "2", role: "assistant", content: "Hi there!" },
        ] as Message[],
        isLoading: true,
      });

      const { container } = render(<MessageList />);

      const bouncingDots = container.querySelectorAll(".animate-bounce");
      expect(bouncingDots.length).toBe(0);
    });
  });

  describe("message ordering", () => {
    it("renders messages in order", () => {
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        messages: [
          { id: "1", role: "user", content: "First message" },
          { id: "2", role: "assistant", content: "Second message" },
          { id: "3", role: "user", content: "Third message" },
        ] as Message[],
      });

      render(<MessageList />);

      const messages = screen.getAllByText(/message/i);
      expect(messages[0]).toHaveTextContent("First message");
      expect(messages[1]).toHaveTextContent("Second message");
      expect(messages[2]).toHaveTextContent("Third message");
    });
  });

  describe("auto-scroll", () => {
    it("has scroll anchor element", () => {
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        messages: [
          { id: "1", role: "user", content: "Test" },
        ] as Message[],
      });

      const { container } = render(<MessageList />);

      // The component has a ref div for scrolling at the bottom
      const scrollAnchor = container.querySelector("div.space-y-4 > div:last-child");
      expect(scrollAnchor).toBeInTheDocument();
    });
  });
});
