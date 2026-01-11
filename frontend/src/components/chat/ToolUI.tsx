"use client";

import type { ToolCallMessagePartComponent } from "@assistant-ui/react";
import { ToolCallDisplay } from "./ToolCallDisplay";
import { AskUserQuestionUI } from "./AskUserQuestionUI";
import { useChatContext } from "./ChatContext";
import type { UserQuestion } from "@/lib/types";

type ToolStatus = "pending" | "running" | "complete" | "error";

interface ToolCallStatus {
  type: string;
  reason?: string;
}

function mapStatus(status: ToolCallStatus): ToolStatus {
  switch (status.type) {
    case "running":
      return "running";
    case "complete":
      return "complete";
    case "incomplete":
      return "error";
    case "requires-action":
    case "requires_action":
      return "running";
    default:
      return "pending";
  }
}

function formatResult(result: unknown, pretty = false): string | undefined {
  if (result === undefined) return undefined;
  if (typeof result === "string") return result;
  return pretty ? JSON.stringify(result, null, 2) : JSON.stringify(result);
}

export const ToolFallback: ToolCallMessagePartComponent = ({
  toolCallId,
  toolName,
  args,
  result,
  isError,
  status,
}) => {
  const { respondToQuestion } = useChatContext();

  const derivedStatus = isError ? "error" : mapStatus(status as ToolCallStatus);

  if (toolName === "AskUserQuestion") {
    const questions = (args as { questions?: UserQuestion[] })?.questions || [];
    return (
      <AskUserQuestionUI
        questions={questions}
        result={formatResult(result)}
        onRespond={respondToQuestion}
      />
    );
  }

  return (
    <ToolCallDisplay
      toolCall={{
        toolCallId,
        toolName,
        args,
        result: formatResult(result, true),
        status: derivedStatus,
      }}
    />
  );
};
