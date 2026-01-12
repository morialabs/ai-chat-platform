"use client";

import { useState } from "react";
import type { UserQuestion } from "@/lib/types";

interface AskUserQuestionUIProps {
  questions: UserQuestion[];
  result?: string;
  onRespond: (answers: Record<string, string>) => void;
}

const BASE_OPTION_CLASS =
  "w-full p-2 text-left border rounded-lg transition-colors text-sm dark:border-gray-600";

function parseResultSafe(result?: string): Record<string, string> | null {
  if (!result) return null;
  try {
    return JSON.parse(result);
  } catch {
    return null;
  }
}

function getOptionClassName(isSelected: boolean, isDisabled: boolean): string {
  if (isDisabled && isSelected) {
    return `${BASE_OPTION_CLASS} border-blue-500 bg-blue-50 dark:bg-blue-900/30 opacity-75`;
  }
  if (isDisabled) {
    return `${BASE_OPTION_CLASS} opacity-50 cursor-not-allowed`;
  }
  if (isSelected) {
    return `${BASE_OPTION_CLASS} border-blue-500 bg-blue-50 dark:bg-blue-900/30`;
  }
  return `${BASE_OPTION_CLASS} hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer`;
}

export function AskUserQuestionUI({
  questions,
  result,
  onRespond,
}: AskUserQuestionUIProps) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [multiAnswers, setMultiAnswers] = useState<Record<string, string[]>>(
    {}
  );
  const [otherSelected, setOtherSelected] = useState<Record<string, boolean>>(
    {}
  );
  const [otherInputs, setOtherInputs] = useState<Record<string, string>>({});
  const [isSubmitted, setIsSubmitted] = useState(false);

  const isAnswered = !!result || isSubmitted;

  const handleSingleSelect = (question: string, value: string): void => {
    if (isAnswered) return;
    setAnswers((prev) => ({ ...prev, [question]: value }));
    setOtherSelected((prev) => ({ ...prev, [question]: false }));
  };

  const handleMultiSelect = (question: string, value: string): void => {
    if (isAnswered) return;
    setMultiAnswers((prev) => {
      const current = prev[question] || [];
      const updated = current.includes(value)
        ? current.filter((v) => v !== value)
        : [...current, value];
      return { ...prev, [question]: updated };
    });
  };

  const handleOtherSelect = (question: string, isMulti: boolean): void => {
    if (isAnswered) return;
    if (isMulti) {
      setOtherSelected((prev) => ({ ...prev, [question]: !prev[question] }));
    } else {
      setOtherSelected((prev) => ({ ...prev, [question]: true }));
      setAnswers((prev) => {
        const updated = { ...prev };
        delete updated[question];
        return updated;
      });
    }
  };

  const handleOtherInput = (question: string, value: string): void => {
    setOtherInputs((prev) => ({ ...prev, [question]: value }));
  };

  const handleSubmit = (): void => {
    const finalAnswers: Record<string, string> = {};

    for (const q of questions) {
      if (q.multiSelect) {
        const selected = [...(multiAnswers[q.question] || [])];
        if (otherSelected[q.question] && otherInputs[q.question]?.trim()) {
          selected.push(otherInputs[q.question].trim());
        }
        finalAnswers[q.question] = selected.join(", ");
      } else if (otherSelected[q.question]) {
        finalAnswers[q.question] = otherInputs[q.question]?.trim() || "";
      } else {
        finalAnswers[q.question] = answers[q.question] || "";
      }
    }

    setIsSubmitted(true);
    onRespond(finalAnswers);
  };

  const allAnswered = questions.every((q) => {
    if (q.multiSelect) {
      const hasOptions = (multiAnswers[q.question]?.length || 0) > 0;
      const hasOther =
        otherSelected[q.question] && !!otherInputs[q.question]?.trim();
      return hasOptions || hasOther;
    }
    if (otherSelected[q.question]) {
      return !!otherInputs[q.question]?.trim();
    }
    return !!answers[q.question];
  });

  const parsedResult = parseResultSafe(result);

  return (
    <div className="my-2 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg border dark:border-gray-700">
      {questions.map((q, i) => (
        <div key={i} className={i > 0 ? "mt-4" : ""}>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded text-xs font-medium">
              {q.header}
            </span>
          </div>
          <p className="text-gray-700 dark:text-gray-200 text-sm mb-2">
            {q.question}
          </p>

          {isAnswered && parsedResult?.[q.question] && (
            <div className="text-sm text-green-600 dark:text-green-400 mb-2">
              Selected: {parsedResult[q.question]}
            </div>
          )}

          <div className="space-y-1">
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
                  disabled={isAnswered}
                  className={getOptionClassName(isSelected, isAnswered)}
                >
                  <div className="font-medium">{opt.label}</div>
                  {opt.description && (
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {opt.description}
                    </div>
                  )}
                </button>
              );
            })}

            <button
              onClick={() => handleOtherSelect(q.question, q.multiSelect)}
              disabled={isAnswered}
              className={getOptionClassName(
                otherSelected[q.question] ?? false,
                isAnswered
              )}
            >
              <div className="font-medium">Other</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                Provide custom input
              </div>
            </button>

            {otherSelected[q.question] && !isAnswered && (
              <input
                type="text"
                value={otherInputs[q.question] || ""}
                onChange={(e) => handleOtherInput(q.question, e.target.value)}
                placeholder="Enter your response..."
                className="w-full mt-1 p-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                autoFocus
              />
            )}
          </div>
        </div>
      ))}

      {!isAnswered && (
        <button
          onClick={handleSubmit}
          disabled={!allAnswered}
          className="mt-3 w-full px-3 py-2 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Submit
        </button>
      )}

      {isAnswered && !parsedResult && (
        <div className="mt-2 text-sm text-gray-500 dark:text-gray-400">
          Response submitted
        </div>
      )}
    </div>
  );
}
