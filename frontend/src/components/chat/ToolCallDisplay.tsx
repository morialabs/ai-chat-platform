"use client";

import { useState, type ReactNode } from "react";
import { ChevronDown, ChevronRight, Loader2, Check, X } from "lucide-react";

type ToolStatus = "pending" | "running" | "complete" | "error";

interface ToolCallProps {
  toolCall: {
    toolCallId: string;
    toolName: string;
    args?: Record<string, unknown>;
    result?: string;
    status: ToolStatus;
  };
}

const TOOL_ICONS: Record<string, string> = {
  mcp__knowledge__search: "🔍",
  mcp__knowledge__get_document: "📄",
  WebSearch: "🌐",
  WebFetch: "📥",
  Read: "📖",
  Write: "✍️",
  Edit: "✏️",
  Bash: "💻",
  Glob: "📁",
  Grep: "🔎",
  Task: "🤖",
};

function getStatusIcon(status: ToolStatus): ReactNode {
  switch (status) {
    case "pending":
      return <Loader2 className="w-4 h-4 animate-spin text-gray-400" />;
    case "running":
      return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />;
    case "complete":
      return <Check className="w-4 h-4 text-green-500" />;
    case "error":
      return <X className="w-4 h-4 text-red-500" />;
  }
}

export function ToolCallDisplay({ toolCall }: ToolCallProps) {
  const [expanded, setExpanded] = useState(false);
  const icon = TOOL_ICONS[toolCall.toolName] || "🔧";

  return (
    <div className="my-2 border rounded-lg overflow-hidden bg-gray-50 dark:bg-gray-800 dark:border-gray-700">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-3 flex items-center gap-2 hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-100 transition-colors"
      >
        {expanded ? (
          <ChevronDown className="w-4 h-4" />
        ) : (
          <ChevronRight className="w-4 h-4" />
        )}
        <span className="text-lg">{icon}</span>
        <span className="font-mono text-sm">{toolCall.toolName}</span>
        <span className="flex-1" />
        {getStatusIcon(toolCall.status)}
      </button>

      {expanded && (
        <div className="p-3 border-t bg-white dark:bg-gray-900 dark:border-gray-700">
          {toolCall.args && (
            <div className="mb-3">
              <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">
                Input
              </h4>
              <pre className="text-xs bg-gray-100 dark:bg-gray-800 dark:text-gray-200 p-2 rounded overflow-x-auto">
                {JSON.stringify(toolCall.args, null, 2)}
              </pre>
            </div>
          )}

          {toolCall.result && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">
                Result
              </h4>
              <pre className="text-xs bg-gray-100 dark:bg-gray-800 dark:text-gray-200 p-2 rounded overflow-x-auto max-h-48 overflow-y-auto">
                {typeof toolCall.result === "string"
                  ? toolCall.result
                  : JSON.stringify(toolCall.result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
