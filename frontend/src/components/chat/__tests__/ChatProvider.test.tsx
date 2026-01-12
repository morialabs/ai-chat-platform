import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, renderHook, act } from "@testing-library/react";
import { ChatProvider, useChatContext } from "../ChatProvider";
import * as aiSdkReact from "@ai-sdk/react";

// Mock the useChat hook
vi.mock("@ai-sdk/react", async () => {
  const actual = await vi.importActual("@ai-sdk/react");
  return {
    ...actual,
    useChat: vi.fn(),
  };
});

const mockUseChat = aiSdkReact.useChat as ReturnType<typeof vi.fn>;

describe("ChatProvider", () => {
  const defaultUseChatReturn = {
    messages: [],
    input: "",
    setInput: vi.fn(),
    handleSubmit: vi.fn(),
    isLoading: false,
    error: undefined,
    reload: vi.fn(),
    stop: vi.fn(),
    status: "ready" as const,
    addToolResult: vi.fn(),
    append: vi.fn(),
    setMessages: vi.fn(),
    id: "chat-1",
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseChat.mockReturnValue(defaultUseChatReturn);
  });

  describe("rendering", () => {
    it("renders children", () => {
      render(
        <ChatProvider>
          <div data-testid="child">Child content</div>
        </ChatProvider>
      );

      expect(screen.getByTestId("child")).toBeInTheDocument();
    });

    it("provides context to children", () => {
      function ChildComponent() {
        const context = useChatContext();
        return <div data-testid="has-context">{context ? "yes" : "no"}</div>;
      }

      render(
        <ChatProvider>
          <ChildComponent />
        </ChatProvider>
      );

      expect(screen.getByTestId("has-context")).toHaveTextContent("yes");
    });
  });

  describe("useChatContext", () => {
    it("throws when used outside provider", () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

      expect(() => {
        renderHook(() => useChatContext());
      }).toThrow("useChatContext must be used within ChatProvider");

      consoleSpy.mockRestore();
    });

    it("returns context value inside provider", () => {
      const { result } = renderHook(() => useChatContext(), {
        wrapper: ChatProvider,
      });

      expect(result.current).toBeDefined();
      expect(result.current.messages).toBeDefined();
    });
  });

  describe("session management", () => {
    it("starts with null sessionId", () => {
      const { result } = renderHook(() => useChatContext(), {
        wrapper: ChatProvider,
      });

      expect(result.current.sessionId).toBeNull();
    });

    it("includes sessionId in request body", () => {
      render(
        <ChatProvider>
          <div>Test</div>
        </ChatProvider>
      );

      // Check that useChat was called with body containing session_id
      expect(mockUseChat).toHaveBeenCalledWith(
        expect.objectContaining({
          body: expect.objectContaining({
            session_id: null,
          }),
        })
      );
    });

    it("configures onResponse callback", () => {
      render(
        <ChatProvider>
          <div>Test</div>
        </ChatProvider>
      );

      expect(mockUseChat).toHaveBeenCalledWith(
        expect.objectContaining({
          onResponse: expect.any(Function),
        })
      );
    });

    it("configures onError callback", () => {
      render(
        <ChatProvider>
          <div>Test</div>
        </ChatProvider>
      );

      expect(mockUseChat).toHaveBeenCalledWith(
        expect.objectContaining({
          onError: expect.any(Function),
        })
      );
    });

    it("configures onToolCall callback", () => {
      render(
        <ChatProvider>
          <div>Test</div>
        </ChatProvider>
      );

      expect(mockUseChat).toHaveBeenCalledWith(
        expect.objectContaining({
          onToolCall: expect.any(Function),
        })
      );
    });
  });

  describe("respondToQuestion", () => {
    it("calls addToolResult with serialized answers", () => {
      const addToolResult = vi.fn();
      mockUseChat.mockReturnValue({
        ...defaultUseChatReturn,
        addToolResult,
      });

      const { result } = renderHook(() => useChatContext(), {
        wrapper: ChatProvider,
      });

      act(() => {
        result.current.respondToQuestion("tool-123", { question: "answer" });
      });

      expect(addToolResult).toHaveBeenCalledWith({
        toolCallId: "tool-123",
        result: JSON.stringify({ question: "answer" }),
      });
    });

    it("formats answers as JSON string", () => {
      const addToolResult = vi.fn();
      mockUseChat.mockReturnValue({
        ...defaultUseChatReturn,
        addToolResult,
      });

      const { result } = renderHook(() => useChatContext(), {
        wrapper: ChatProvider,
      });

      act(() => {
        result.current.respondToQuestion("tool-1", {
          "What color?": "Blue",
          "What size?": "Large",
        });
      });

      const call = addToolResult.mock.calls[0][0];
      expect(JSON.parse(call.result)).toEqual({
        "What color?": "Blue",
        "What size?": "Large",
      });
    });
  });

  describe("context values", () => {
    it("exposes messages array", () => {
      const messages = [{ id: "1", role: "user" as const, content: "Hello" }];
      mockUseChat.mockReturnValue({
        ...defaultUseChatReturn,
        messages,
      });

      const { result } = renderHook(() => useChatContext(), {
        wrapper: ChatProvider,
      });

      expect(result.current.messages).toEqual(messages);
    });

    it("exposes input and setInput", () => {
      const setInput = vi.fn();
      mockUseChat.mockReturnValue({
        ...defaultUseChatReturn,
        input: "test input",
        setInput,
      });

      const { result } = renderHook(() => useChatContext(), {
        wrapper: ChatProvider,
      });

      expect(result.current.input).toBe("test input");
      expect(result.current.setInput).toBe(setInput);
    });

    it("exposes handleSubmit", () => {
      const handleSubmit = vi.fn();
      mockUseChat.mockReturnValue({
        ...defaultUseChatReturn,
        handleSubmit,
      });

      const { result } = renderHook(() => useChatContext(), {
        wrapper: ChatProvider,
      });

      expect(result.current.handleSubmit).toBe(handleSubmit);
    });

    it("exposes isLoading state", () => {
      mockUseChat.mockReturnValue({
        ...defaultUseChatReturn,
        isLoading: true,
      });

      const { result } = renderHook(() => useChatContext(), {
        wrapper: ChatProvider,
      });

      expect(result.current.isLoading).toBe(true);
    });

    it("exposes error state", () => {
      const error = new Error("Test error");
      mockUseChat.mockReturnValue({
        ...defaultUseChatReturn,
        error,
      });

      const { result } = renderHook(() => useChatContext(), {
        wrapper: ChatProvider,
      });

      expect(result.current.error).toBe(error);
    });

    it("exposes status", () => {
      mockUseChat.mockReturnValue({
        ...defaultUseChatReturn,
        status: "streaming" as const,
      });

      const { result } = renderHook(() => useChatContext(), {
        wrapper: ChatProvider,
      });

      expect(result.current.status).toBe("streaming");
    });

    it("exposes reload function", () => {
      const reload = vi.fn();
      mockUseChat.mockReturnValue({
        ...defaultUseChatReturn,
        reload,
      });

      const { result } = renderHook(() => useChatContext(), {
        wrapper: ChatProvider,
      });

      expect(result.current.reload).toBe(reload);
    });

    it("exposes stop function", () => {
      const stop = vi.fn();
      mockUseChat.mockReturnValue({
        ...defaultUseChatReturn,
        stop,
      });

      const { result } = renderHook(() => useChatContext(), {
        wrapper: ChatProvider,
      });

      expect(result.current.stop).toBe(stop);
    });

    it("exposes addToolResult", () => {
      const addToolResult = vi.fn();
      mockUseChat.mockReturnValue({
        ...defaultUseChatReturn,
        addToolResult,
      });

      const { result } = renderHook(() => useChatContext(), {
        wrapper: ChatProvider,
      });

      expect(result.current.addToolResult).toBe(addToolResult);
    });
  });

  describe("useChat configuration", () => {
    it("uses /api/chat endpoint", () => {
      render(
        <ChatProvider>
          <div>Test</div>
        </ChatProvider>
      );

      expect(mockUseChat).toHaveBeenCalledWith(
        expect.objectContaining({
          api: "/api/chat",
        })
      );
    });
  });
});
