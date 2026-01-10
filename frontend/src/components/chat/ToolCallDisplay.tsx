"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, Loader2, Check, X } from "lucide-react";

interface ToolCallProps {
  toolCall: {
    toolCallId: string;
    toolName: string;
    args?: Record<string, unknown>;
    result?: string;
    status: "pending" | "running" | "complete" | "error";
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

export function ToolCallDisplay({ toolCall }: ToolCallProps) {
  const [expanded, setExpanded] = useState(false);
  const icon = TOOL_ICONS[toolCall.toolName] || "🔧";

  const statusIcon = {
    pending: <Loader2 className="w-4 h-4 animate-spin text-gray-400" />,
    running: <Loader2 className="w-4 h-4 animate-spin text-blue-500" />,
    complete: <Check className="w-4 h-4 text-green-500" />,
    error: <X className="w-4 h-4 text-red-500" />,
  }[toolCall.status];

  return (
    <div className="my-2 border rounded-lg overflow-hidden bg-gray-50">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-3 flex items-center gap-2 hover:bg-gray-100 transition-colors"
      >
        {expanded ? (
          <ChevronDown className="w-4 h-4" />
        ) : (
          <ChevronRight className="w-4 h-4" />
        )}
        <span className="text-lg">{icon}</span>
        <span className="font-mono text-sm">{toolCall.toolName}</span>
        <span className="flex-1" />
        {statusIcon}
      </button>

      {expanded && (
        <div className="p-3 border-t bg-white">
          {toolCall.args && (
            <div className="mb-3">
              <h4 className="text-xs font-semibold text-gray-500 mb-1">
                Input
              </h4>
              <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                {JSON.stringify(toolCall.args, null, 2)}
              </pre>
            </div>
          )}

          {toolCall.result && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 mb-1">
                Result
              </h4>
              <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto max-h-48 overflow-y-auto">
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
