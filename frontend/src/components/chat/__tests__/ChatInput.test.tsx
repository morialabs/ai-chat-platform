import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ChatInput } from "../ChatInput";
import * as ChatProviderModule from "../ChatProvider";

// Mock the ChatProvider context
const mockUseChatContext = vi.spyOn(ChatProviderModule, "useChatContext");

describe("ChatInput", () => {
  const defaultContextValue = {
    input: "",
    setInput: vi.fn(),
    handleSubmit: vi.fn(),
    isLoading: false,
    stop: vi.fn(),
    status: "ready" as const,
    messages: [],
    error: undefined,
    sessionId: null,
    addToolResult: vi.fn(),
    respondToQuestion: vi.fn(),
    reload: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseChatContext.mockReturnValue(defaultContextValue);
  });

  describe("input field", () => {
    it("renders textarea", () => {
      render(<ChatInput />);

      const textarea = screen.getByRole("textbox");
      expect(textarea).toBeInTheDocument();
      expect(textarea.tagName).toBe("TEXTAREA");
    });

    it("shows placeholder text", () => {
      render(<ChatInput />);

      expect(
        screen.getByPlaceholderText("Type your message...")
      ).toBeInTheDocument();
    });

    it("updates on change", () => {
      const setInput = vi.fn();
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        setInput,
      });

      render(<ChatInput />);

      const textarea = screen.getByRole("textbox");
      fireEvent.change(textarea, { target: { value: "Hello" } });

      expect(setInput).toHaveBeenCalledWith("Hello");
    });

    it("is disabled when loading and not streaming", () => {
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        isLoading: true,
        status: "submitted",
      });

      render(<ChatInput />);

      expect(screen.getByRole("textbox")).toBeDisabled();
    });

    it("is not disabled when streaming", () => {
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        isLoading: true,
        status: "streaming",
      });

      render(<ChatInput />);

      expect(screen.getByRole("textbox")).not.toBeDisabled();
    });
  });

  describe("submit button", () => {
    it("renders send button", () => {
      render(<ChatInput />);

      expect(screen.getByLabelText("Send message")).toBeInTheDocument();
    });

    it("is disabled when input empty", () => {
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        input: "",
      });

      render(<ChatInput />);

      expect(screen.getByLabelText("Send message")).toBeDisabled();
    });

    it("is disabled when input is whitespace only", () => {
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        input: "   ",
      });

      render(<ChatInput />);

      expect(screen.getByLabelText("Send message")).toBeDisabled();
    });

    it("is enabled when input has content", () => {
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        input: "Hello",
      });

      render(<ChatInput />);

      expect(screen.getByLabelText("Send message")).not.toBeDisabled();
    });

    it("is disabled when loading", () => {
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        input: "Hello",
        isLoading: true,
      });

      render(<ChatInput />);

      // When not streaming, send button should be disabled
      expect(screen.getByLabelText("Send message")).toBeDisabled();
    });
  });

  describe("stop button", () => {
    it("shows stop button when streaming", () => {
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        isLoading: true,
        status: "streaming",
      });

      render(<ChatInput />);

      expect(screen.getByLabelText("Stop generation")).toBeInTheDocument();
    });

    it("calls stop on click", () => {
      const stop = vi.fn();
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        isLoading: true,
        status: "streaming",
        stop,
      });

      render(<ChatInput />);

      fireEvent.click(screen.getByLabelText("Stop generation"));

      expect(stop).toHaveBeenCalled();
    });

    it("hides send button when streaming", () => {
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        isLoading: true,
        status: "streaming",
      });

      render(<ChatInput />);

      expect(screen.queryByLabelText("Send message")).not.toBeInTheDocument();
      expect(screen.getByLabelText("Stop generation")).toBeInTheDocument();
    });
  });

  describe("keyboard", () => {
    it("submits on Enter when input has content", () => {
      const handleSubmit = vi.fn();
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        input: "Hello",
        handleSubmit,
      });

      render(<ChatInput />);

      const textarea = screen.getByRole("textbox");
      fireEvent.keyDown(textarea, { key: "Enter", shiftKey: false });

      // Form should be submitted via requestSubmit which triggers handleSubmit
      expect(handleSubmit).toHaveBeenCalled();
    });

    it("does not submit on Shift+Enter", () => {
      const handleSubmit = vi.fn();
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        input: "Hello",
        handleSubmit,
      });

      render(<ChatInput />);

      const textarea = screen.getByRole("textbox");
      fireEvent.keyDown(textarea, { key: "Enter", shiftKey: true });

      // Should not submit when Shift is held
      expect(handleSubmit).not.toHaveBeenCalled();
    });

    it("does not submit on Enter when input is empty", () => {
      const handleSubmit = vi.fn();
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        input: "",
        handleSubmit,
      });

      render(<ChatInput />);

      const textarea = screen.getByRole("textbox");
      fireEvent.keyDown(textarea, { key: "Enter", shiftKey: false });

      expect(handleSubmit).not.toHaveBeenCalled();
    });
  });

  describe("form submission", () => {
    it("prevents default form behavior", () => {
      const handleSubmit = vi.fn();
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        input: "Hello",
        handleSubmit,
      });

      render(<ChatInput />);

      const form = screen.getByRole("textbox").closest("form")!;
      const submitEvent = new Event("submit", {
        bubbles: true,
        cancelable: true,
      });

      form.dispatchEvent(submitEvent);

      expect(submitEvent.defaultPrevented).toBe(true);
    });

    it("does not call handleSubmit when input is empty", () => {
      const handleSubmit = vi.fn();
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        input: "",
        handleSubmit,
      });

      render(<ChatInput />);

      const form = screen.getByRole("textbox").closest("form")!;
      fireEvent.submit(form);

      expect(handleSubmit).not.toHaveBeenCalled();
    });

    it("does not submit whitespace only", () => {
      const handleSubmit = vi.fn();
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        input: "   \n\t   ",
        handleSubmit,
      });

      render(<ChatInput />);

      const form = screen.getByRole("textbox").closest("form")!;
      fireEvent.submit(form);

      expect(handleSubmit).not.toHaveBeenCalled();
    });

    it("calls handleSubmit when input has content", () => {
      const handleSubmit = vi.fn();
      mockUseChatContext.mockReturnValue({
        ...defaultContextValue,
        input: "Hello world",
        handleSubmit,
      });

      render(<ChatInput />);

      const form = screen.getByRole("textbox").closest("form")!;
      fireEvent.submit(form);

      expect(handleSubmit).toHaveBeenCalled();
    });
  });

  describe("helper text", () => {
    it("shows keyboard shortcut hint", () => {
      render(<ChatInput />);

      expect(
        screen.getByText("Press Enter to send, Shift+Enter for new line")
      ).toBeInTheDocument();
    });
  });
});
