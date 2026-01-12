import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { AskUserQuestionUI } from "../AskUserQuestionUI";
import type { UserQuestion } from "@/lib/types";

describe("AskUserQuestionUI", () => {
  const singleSelectQuestion: UserQuestion = {
    question: "Which color do you prefer?",
    header: "Color",
    options: [
      { label: "Red", description: "A warm color" },
      { label: "Blue", description: "A cool color" },
    ],
    multiSelect: false,
  };

  const multiSelectQuestion: UserQuestion = {
    question: "Which features do you want?",
    header: "Features",
    options: [
      { label: "TypeScript", description: "Type safety" },
      { label: "Testing", description: "Unit tests" },
      { label: "Linting", description: "Code quality" },
    ],
    multiSelect: true,
  };

  let onRespond: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    onRespond = vi.fn();
  });

  describe("question rendering", () => {
    it("renders question text", () => {
      render(
        <AskUserQuestionUI
          questions={[singleSelectQuestion]}
          onRespond={onRespond}
        />
      );

      expect(
        screen.getByText("Which color do you prefer?")
      ).toBeInTheDocument();
    });

    it("renders header badge", () => {
      render(
        <AskUserQuestionUI
          questions={[singleSelectQuestion]}
          onRespond={onRespond}
        />
      );

      expect(screen.getByText("Color")).toBeInTheDocument();
    });

    it("renders all options", () => {
      render(
        <AskUserQuestionUI
          questions={[singleSelectQuestion]}
          onRespond={onRespond}
        />
      );

      expect(screen.getByText("Red")).toBeInTheDocument();
      expect(screen.getByText("Blue")).toBeInTheDocument();
    });

    it("renders option descriptions", () => {
      render(
        <AskUserQuestionUI
          questions={[singleSelectQuestion]}
          onRespond={onRespond}
        />
      );

      expect(screen.getByText("A warm color")).toBeInTheDocument();
      expect(screen.getByText("A cool color")).toBeInTheDocument();
    });

    it("renders multiple questions", () => {
      render(
        <AskUserQuestionUI
          questions={[singleSelectQuestion, multiSelectQuestion]}
          onRespond={onRespond}
        />
      );

      expect(
        screen.getByText("Which color do you prefer?")
      ).toBeInTheDocument();
      expect(
        screen.getByText("Which features do you want?")
      ).toBeInTheDocument();
    });
  });

  describe("single select", () => {
    it("selects one option at a time", () => {
      render(
        <AskUserQuestionUI
          questions={[singleSelectQuestion]}
          onRespond={onRespond}
        />
      );

      const redButton = screen.getByText("Red").closest("button")!;
      const blueButton = screen.getByText("Blue").closest("button")!;

      // Select Red
      fireEvent.click(redButton);
      expect(redButton).toHaveClass("border-blue-500");

      // Select Blue - Red should be deselected
      fireEvent.click(blueButton);
      expect(blueButton).toHaveClass("border-blue-500");
      expect(redButton).not.toHaveClass("border-blue-500");
    });

    it("deselects previous on new selection", () => {
      render(
        <AskUserQuestionUI
          questions={[singleSelectQuestion]}
          onRespond={onRespond}
        />
      );

      const redButton = screen.getByText("Red").closest("button")!;

      fireEvent.click(redButton);
      expect(redButton).toHaveClass("border-blue-500");

      // Select another option
      fireEvent.click(screen.getByText("Blue").closest("button")!);
      expect(redButton).not.toHaveClass("border-blue-500");
    });
  });

  describe("multi select", () => {
    it("allows multiple selections", () => {
      render(
        <AskUserQuestionUI
          questions={[multiSelectQuestion]}
          onRespond={onRespond}
        />
      );

      const tsButton = screen.getByText("TypeScript").closest("button")!;
      const testButton = screen.getByText("Testing").closest("button")!;

      fireEvent.click(tsButton);
      fireEvent.click(testButton);

      expect(tsButton).toHaveClass("border-blue-500");
      expect(testButton).toHaveClass("border-blue-500");
    });

    it("toggles selection on click", () => {
      render(
        <AskUserQuestionUI
          questions={[multiSelectQuestion]}
          onRespond={onRespond}
        />
      );

      const tsButton = screen.getByText("TypeScript").closest("button")!;

      // Select
      fireEvent.click(tsButton);
      expect(tsButton).toHaveClass("border-blue-500");

      // Deselect
      fireEvent.click(tsButton);
      expect(tsButton).not.toHaveClass("border-blue-500");
    });

    it("joins answers with comma on submit", () => {
      render(
        <AskUserQuestionUI
          questions={[multiSelectQuestion]}
          onRespond={onRespond}
        />
      );

      fireEvent.click(screen.getByText("TypeScript").closest("button")!);
      fireEvent.click(screen.getByText("Testing").closest("button")!);
      fireEvent.click(screen.getByText("Submit"));

      expect(onRespond).toHaveBeenCalledWith({
        "Which features do you want?": "TypeScript, Testing",
      });
    });
  });

  describe("other option", () => {
    it("shows other option", () => {
      render(
        <AskUserQuestionUI
          questions={[singleSelectQuestion]}
          onRespond={onRespond}
        />
      );

      expect(screen.getByText("Other")).toBeInTheDocument();
    });

    it("reveals input when selected", () => {
      render(
        <AskUserQuestionUI
          questions={[singleSelectQuestion]}
          onRespond={onRespond}
        />
      );

      // Initially no input
      expect(
        screen.queryByPlaceholderText("Enter your response...")
      ).not.toBeInTheDocument();

      // Click Other
      fireEvent.click(screen.getByText("Other").closest("button")!);

      // Input should appear
      expect(
        screen.getByPlaceholderText("Enter your response...")
      ).toBeInTheDocument();
    });

    it("captures custom input", () => {
      render(
        <AskUserQuestionUI
          questions={[singleSelectQuestion]}
          onRespond={onRespond}
        />
      );

      // Select Other and enter custom value
      fireEvent.click(screen.getByText("Other").closest("button")!);
      const input = screen.getByPlaceholderText("Enter your response...");
      fireEvent.change(input, { target: { value: "Green" } });
      fireEvent.click(screen.getByText("Submit"));

      expect(onRespond).toHaveBeenCalledWith({
        "Which color do you prefer?": "Green",
      });
    });

    it("works with multi select", () => {
      render(
        <AskUserQuestionUI
          questions={[multiSelectQuestion]}
          onRespond={onRespond}
        />
      );

      // Select an option and other
      fireEvent.click(screen.getByText("TypeScript").closest("button")!);
      fireEvent.click(screen.getByText("Other").closest("button")!);
      const input = screen.getByPlaceholderText("Enter your response...");
      fireEvent.change(input, { target: { value: "CI/CD" } });
      fireEvent.click(screen.getByText("Submit"));

      expect(onRespond).toHaveBeenCalledWith({
        "Which features do you want?": "TypeScript, CI/CD",
      });
    });
  });

  describe("submit", () => {
    it("disables submit until answered", () => {
      render(
        <AskUserQuestionUI
          questions={[singleSelectQuestion]}
          onRespond={onRespond}
        />
      );

      expect(screen.getByText("Submit")).toBeDisabled();
    });

    it("enables submit when all answered", () => {
      render(
        <AskUserQuestionUI
          questions={[singleSelectQuestion]}
          onRespond={onRespond}
        />
      );

      fireEvent.click(screen.getByText("Red").closest("button")!);

      expect(screen.getByText("Submit")).not.toBeDisabled();
    });

    it("calls onRespond with answers", () => {
      render(
        <AskUserQuestionUI
          questions={[singleSelectQuestion]}
          onRespond={onRespond}
        />
      );

      fireEvent.click(screen.getByText("Blue").closest("button")!);
      fireEvent.click(screen.getByText("Submit"));

      expect(onRespond).toHaveBeenCalledWith({
        "Which color do you prefer?": "Blue",
      });
    });

    it("requires all questions to be answered", () => {
      render(
        <AskUserQuestionUI
          questions={[singleSelectQuestion, multiSelectQuestion]}
          onRespond={onRespond}
        />
      );

      // Answer only first question
      fireEvent.click(screen.getByText("Red").closest("button")!);

      // Submit should still be disabled
      expect(screen.getByText("Submit")).toBeDisabled();

      // Answer second question
      fireEvent.click(screen.getByText("TypeScript").closest("button")!);

      // Now submit should be enabled
      expect(screen.getByText("Submit")).not.toBeDisabled();
    });
  });

  describe("answered state", () => {
    it("disables options when result provided", () => {
      render(
        <AskUserQuestionUI
          questions={[singleSelectQuestion]}
          result={JSON.stringify({ "Which color do you prefer?": "Red" })}
          onRespond={onRespond}
        />
      );

      const redButton = screen.getByText("Red").closest("button")!;
      expect(redButton).toBeDisabled();
    });

    it("shows selected answer", () => {
      render(
        <AskUserQuestionUI
          questions={[singleSelectQuestion]}
          result={JSON.stringify({ "Which color do you prefer?": "Red" })}
          onRespond={onRespond}
        />
      );

      expect(screen.getByText("Selected: Red")).toBeInTheDocument();
    });

    it("hides submit button when answered", () => {
      render(
        <AskUserQuestionUI
          questions={[singleSelectQuestion]}
          result={JSON.stringify({ "Which color do you prefer?": "Red" })}
          onRespond={onRespond}
        />
      );

      expect(screen.queryByText("Submit")).not.toBeInTheDocument();
    });

    it("shows 'Response submitted' when submitted without parseable result", () => {
      render(
        <AskUserQuestionUI
          questions={[singleSelectQuestion]}
          result="invalid json"
          onRespond={onRespond}
        />
      );

      expect(screen.getByText("Response submitted")).toBeInTheDocument();
    });

    it("prevents further interaction after submission", () => {
      render(
        <AskUserQuestionUI
          questions={[singleSelectQuestion]}
          onRespond={onRespond}
        />
      );

      // Submit an answer
      fireEvent.click(screen.getByText("Red").closest("button")!);
      fireEvent.click(screen.getByText("Submit"));

      // Try to click another option - it should be disabled
      const blueButton = screen.getByText("Blue").closest("button")!;
      expect(blueButton).toBeDisabled();
    });
  });
});
