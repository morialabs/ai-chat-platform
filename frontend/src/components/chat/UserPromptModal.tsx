"use client";

import { useState } from "react";
import type { UserPrompt } from "@/lib/types";

interface UserPromptModalProps {
  prompt: UserPrompt;
  onRespond: (answers: Record<string, string>) => void;
  onCancel: () => void;
}

function getOptionClassName(isSelected: boolean): string {
  const baseClass = "w-full p-3 text-left border rounded-lg transition-colors dark:border-gray-600";
  if (isSelected) {
    return `${baseClass} border-blue-500 bg-blue-50 dark:bg-blue-900/30`;
  }
  return `${baseClass} hover:bg-gray-50 dark:hover:bg-gray-800`;
}

export function UserPromptModal({
  prompt,
  onRespond,
  onCancel,
}: UserPromptModalProps) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [multiAnswers, setMultiAnswers] = useState<Record<string, string[]>>(
    {}
  );

  const handleSingleSelect = (question: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [question]: value }));
  };

  const handleMultiSelect = (question: string, value: string) => {
    setMultiAnswers((prev) => {
      const current = prev[question] || [];
      const updated = current.includes(value)
        ? current.filter((v) => v !== value)
        : [...current, value];
      return { ...prev, [question]: updated };
    });
  };

  const handleSubmit = () => {
    const finalAnswers: Record<string, string> = { ...answers };
    for (const [q, values] of Object.entries(multiAnswers)) {
      finalAnswers[q] = values.join(", ");
    }
    onRespond(finalAnswers);
  };

  const allAnswered = prompt.questions.every((q) => {
    if (q.multiSelect) {
      return (multiAnswers[q.question]?.length || 0) > 0;
    }
    return !!answers[q.question];
  });

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-gray-900 dark:text-gray-100 rounded-xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-lg font-semibold mb-4">Input Required</h2>

          {prompt.questions.map((q, i) => (
            <div key={i} className="mb-6">
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs font-medium">
                  {q.header}
                </span>
              </div>
              <p className="text-gray-700 dark:text-gray-200 mb-3">{q.question}</p>

              <div className="space-y-2">
                {q.options.map((opt, j) => {
                  const isSelected = q.multiSelect
                    ? multiAnswers[q.question]?.includes(opt.label) ?? false
                    : answers[q.question] === opt.label;

                  return (
                    <button
                      key={j}
                      onClick={() =>
                        q.multiSelect
                          ? handleMultiSelect(q.question, opt.label)
                          : handleSingleSelect(q.question, opt.label)
                      }
                      className={getOptionClassName(isSelected)}
                    >
                      <div className="font-medium">{opt.label}</div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">{opt.description}</div>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}

          <div className="flex gap-3 mt-6">
            <button
              onClick={onCancel}
              className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-800"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={!allAnswered}
              className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Submit
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
