"use client";

import type { ToolCallMessagePartComponent } from "@assistant-ui/react";
import { ToolCallDisplay } from "./ToolCallDisplay";

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

// ToolFallback component for rendering any tool call
export const ToolFallback: ToolCallMessagePartComponent = ({
  toolCallId,
  toolName,
  args,
  result,
  isError,
  status,
}) => {
  // Override status to error if isError is true
  const derivedStatus = isError
    ? "error"
    : mapStatus(status as ToolCallStatus);

  return (
    <ToolCallDisplay
      toolCall={{
        toolCallId,
        toolName,
        args,
        result:
          result !== undefined
            ? typeof result === "string"
              ? result
              : JSON.stringify(result, null, 2)
            : undefined,
        status: derivedStatus,
      }}
    />
  );
};
