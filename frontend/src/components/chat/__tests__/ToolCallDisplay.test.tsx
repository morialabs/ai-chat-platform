import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ToolCallDisplay } from "../ToolCallDisplay";

describe("ToolCallDisplay", () => {
  describe("header", () => {
    it("shows tool name", () => {
      render(
        <ToolCallDisplay
          toolCall={{
            toolCallId: "test-1",
            toolName: "Read",
            status: "running",
          }}
        />
      );

      expect(screen.getByText("Read")).toBeInTheDocument();
    });

    it("shows tool icon for known tools", () => {
      render(
        <ToolCallDisplay
          toolCall={{
            toolCallId: "test-1",
            toolName: "Bash",
            status: "running",
          }}
        />
      );

      expect(screen.getByText("💻")).toBeInTheDocument();
    });

    it("shows default icon for unknown tools", () => {
      render(
        <ToolCallDisplay
          toolCall={{
            toolCallId: "test-1",
            toolName: "CustomTool",
            status: "running",
          }}
        />
      );

      expect(screen.getByText("🔧")).toBeInTheDocument();
    });
  });

  describe("status icons", () => {
    it("shows spinner for running status", () => {
      const { container } = render(
        <ToolCallDisplay
          toolCall={{
            toolCallId: "test-1",
            toolName: "Read",
            status: "running",
          }}
        />
      );

      // Check for spinner animation class
      const spinner = container.querySelector(".animate-spin");
      expect(spinner).toBeInTheDocument();
    });

    it("shows check for complete status", () => {
      const { container } = render(
        <ToolCallDisplay
          toolCall={{
            toolCallId: "test-1",
            toolName: "Read",
            status: "complete",
          }}
        />
      );

      const checkIcon = container.querySelector(".text-green-500");
      expect(checkIcon).toBeInTheDocument();
    });

    it("shows x for error status", () => {
      const { container } = render(
        <ToolCallDisplay
          toolCall={{
            toolCallId: "test-1",
            toolName: "Read",
            status: "error",
          }}
        />
      );

      const errorIcon = container.querySelector(".text-red-500");
      expect(errorIcon).toBeInTheDocument();
    });

    it("uses isError to determine error state when status is complete", () => {
      const { container } = render(
        <ToolCallDisplay
          toolCall={{
            toolCallId: "test-1",
            toolName: "Read",
            status: "complete",
            isError: true,
          }}
        />
      );

      // Should show red error icon despite complete status
      const errorIcon = container.querySelector(".text-red-500");
      expect(errorIcon).toBeInTheDocument();
    });
  });

  describe("expandable content", () => {
    it("starts collapsed", () => {
      render(
        <ToolCallDisplay
          toolCall={{
            toolCallId: "test-1",
            toolName: "Read",
            status: "complete",
            args: { file_path: "/test.txt" },
            result: "File contents",
          }}
        />
      );

      // Input/Result labels should not be visible when collapsed
      expect(screen.queryByText("Input")).not.toBeInTheDocument();
      expect(screen.queryByText("Result")).not.toBeInTheDocument();
    });

    it("expands on click", () => {
      render(
        <ToolCallDisplay
          toolCall={{
            toolCallId: "test-1",
            toolName: "Read",
            status: "complete",
            args: { file_path: "/test.txt" },
            result: "File contents",
          }}
        />
      );

      // Click to expand
      fireEvent.click(screen.getByRole("button"));

      // Input/Result labels should now be visible
      expect(screen.getByText("Input")).toBeInTheDocument();
      expect(screen.getByText("Result")).toBeInTheDocument();
    });

    it("shows input when expanded", () => {
      render(
        <ToolCallDisplay
          toolCall={{
            toolCallId: "test-1",
            toolName: "Read",
            status: "complete",
            args: { file_path: "/test.txt" },
          }}
        />
      );

      // Expand
      fireEvent.click(screen.getByRole("button"));

      // Check that args are displayed
      expect(screen.getByText(/"file_path": "\/test.txt"/)).toBeInTheDocument();
    });

    it("shows result when expanded and available", () => {
      render(
        <ToolCallDisplay
          toolCall={{
            toolCallId: "test-1",
            toolName: "Read",
            status: "complete",
            result: "Hello from file",
          }}
        />
      );

      // Expand
      fireEvent.click(screen.getByRole("button"));

      expect(screen.getByText("Hello from file")).toBeInTheDocument();
    });
  });

  describe("input display", () => {
    it("formats args as JSON", () => {
      render(
        <ToolCallDisplay
          toolCall={{
            toolCallId: "test-1",
            toolName: "Write",
            status: "running",
            args: { file_path: "/test.txt", content: "Hello" },
          }}
        />
      );

      fireEvent.click(screen.getByRole("button"));

      // Check formatted JSON is displayed
      expect(screen.getByText(/"file_path": "\/test.txt"/)).toBeInTheDocument();
      expect(screen.getByText(/"content": "Hello"/)).toBeInTheDocument();
    });

    it("handles empty args", () => {
      render(
        <ToolCallDisplay
          toolCall={{
            toolCallId: "test-1",
            toolName: "Read",
            status: "running",
            args: {},
          }}
        />
      );

      fireEvent.click(screen.getByRole("button"));

      // Empty object should be displayed
      expect(screen.getByText("{}")).toBeInTheDocument();
    });

    it("handles undefined args", () => {
      render(
        <ToolCallDisplay
          toolCall={{
            toolCallId: "test-1",
            toolName: "Read",
            status: "running",
          }}
        />
      );

      fireEvent.click(screen.getByRole("button"));

      // Input section should not be rendered when args is undefined
      expect(screen.queryByText("Input")).not.toBeInTheDocument();
    });
  });

  describe("result display", () => {
    it("shows result string", () => {
      render(
        <ToolCallDisplay
          toolCall={{
            toolCallId: "test-1",
            toolName: "Read",
            status: "complete",
            result: "This is the file content",
          }}
        />
      );

      fireEvent.click(screen.getByRole("button"));

      expect(screen.getByText("This is the file content")).toBeInTheDocument();
    });

    it("handles missing result", () => {
      render(
        <ToolCallDisplay
          toolCall={{
            toolCallId: "test-1",
            toolName: "Read",
            status: "running",
          }}
        />
      );

      fireEvent.click(screen.getByRole("button"));

      // Result section should not be rendered
      expect(screen.queryByText("Result")).not.toBeInTheDocument();
    });
  });

  describe("tool icons", () => {
    const iconTests = [
      { toolName: "WebSearch", expectedIcon: "🌐" },
      { toolName: "WebFetch", expectedIcon: "📥" },
      { toolName: "Read", expectedIcon: "📖" },
      { toolName: "Write", expectedIcon: "✍️" },
      { toolName: "Edit", expectedIcon: "✏️" },
      { toolName: "Bash", expectedIcon: "💻" },
      { toolName: "Glob", expectedIcon: "📁" },
      { toolName: "Grep", expectedIcon: "🔎" },
      { toolName: "Task", expectedIcon: "🤖" },
    ];

    iconTests.forEach(({ toolName, expectedIcon }) => {
      it(`shows ${expectedIcon} for ${toolName}`, () => {
        render(
          <ToolCallDisplay
            toolCall={{
              toolCallId: "test-1",
              toolName,
              status: "running",
            }}
          />
        );

        expect(screen.getByText(expectedIcon)).toBeInTheDocument();
      });
    });
  });
});
