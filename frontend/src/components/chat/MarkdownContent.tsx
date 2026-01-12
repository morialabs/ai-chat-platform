"use client";

import React, { memo, type ComponentPropsWithoutRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

interface MarkdownContentProps {
  /** The markdown content to render */
  content: string;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Renders markdown content with syntax highlighting for code blocks.
 * Memoized to prevent unnecessary re-renders during streaming.
 */
function MarkdownContentImpl({
  content,
  className = "",
}: MarkdownContentProps): React.JSX.Element {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      className={`prose prose-sm dark:prose-invert max-w-none ${className}`}
      components={{
        // Headings
        h1: ({ children }) => (
          <h1 className="text-2xl font-bold mt-6 mb-4 first:mt-0">{children}</h1>
        ),
        h2: ({ children }) => (
          <h2 className="text-xl font-bold mt-5 mb-3 first:mt-0">{children}</h2>
        ),
        h3: ({ children }) => (
          <h3 className="text-lg font-semibold mt-4 mb-2 first:mt-0">
            {children}
          </h3>
        ),
        h4: ({ children }) => (
          <h4 className="text-base font-semibold mt-3 mb-2 first:mt-0">
            {children}
          </h4>
        ),

        // Paragraphs
        p: ({ children }) => (
          <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>
        ),

        // Lists
        ul: ({ children }) => (
          <ul className="list-disc pl-6 mb-3 space-y-1">{children}</ul>
        ),
        ol: ({ children }) => (
          <ol className="list-decimal pl-6 mb-3 space-y-1">{children}</ol>
        ),
        li: ({ children }) => <li className="leading-relaxed">{children}</li>,

        // Links
        a: ({ href, children }) => (
          <a
            href={href}
            className="text-blue-500 hover:text-blue-600 hover:underline"
            target="_blank"
            rel="noopener noreferrer"
          >
            {children}
          </a>
        ),

        // Blockquotes
        blockquote: ({ children }) => (
          <blockquote className="border-l-4 border-gray-300 dark:border-gray-600 pl-4 my-3 italic text-gray-600 dark:text-gray-400">
            {children}
          </blockquote>
        ),

        // Horizontal rule
        hr: () => <hr className="my-6 border-gray-200 dark:border-gray-700" />,

        // Tables
        table: ({ children }) => (
          <div className="overflow-x-auto my-3">
            <table className="min-w-full border-collapse border border-gray-300 dark:border-gray-600">
              {children}
            </table>
          </div>
        ),
        thead: ({ children }) => (
          <thead className="bg-gray-100 dark:bg-gray-800">{children}</thead>
        ),
        th: ({ children }) => (
          <th className="border border-gray-300 dark:border-gray-600 px-3 py-2 text-left font-semibold">
            {children}
          </th>
        ),
        td: ({ children }) => (
          <td className="border border-gray-300 dark:border-gray-600 px-3 py-2">
            {children}
          </td>
        ),

        // Code - inline and block
        code: ({
          className,
          children,
          ...props
        }: ComponentPropsWithoutRef<"code">) => {
          const match = /language-(\w+)/.exec(className || "");
          const language = match ? match[1] : "";
          const isInline = !className;

          if (isInline) {
            return (
              <code
                className="bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-sm font-mono text-pink-600 dark:text-pink-400"
                {...props}
              >
                {children}
              </code>
            );
          }

          // Block code with syntax highlighting
          const codeString = String(children).replace(/\n$/, "");

          return (
            <div className="my-3 rounded-lg overflow-hidden">
              {language && (
                <div className="bg-gray-800 px-4 py-1 text-xs text-gray-400 border-b border-gray-700">
                  {language}
                </div>
              )}
              <SyntaxHighlighter
                style={oneDark}
                language={language || "text"}
                PreTag="div"
                customStyle={{
                  margin: 0,
                  borderRadius: language ? "0 0 0.5rem 0.5rem" : "0.5rem",
                  fontSize: "0.875rem",
                }}
              >
                {codeString}
              </SyntaxHighlighter>
            </div>
          );
        },

        // Pre - wrapper for code blocks
        pre: ({ children }) => <>{children}</>,

        // Strong and emphasis
        strong: ({ children }) => (
          <strong className="font-semibold">{children}</strong>
        ),
        em: ({ children }) => <em className="italic">{children}</em>,

        // Strikethrough
        del: ({ children }) => <del className="line-through">{children}</del>,
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

/**
 * Memoized markdown content component.
 * Re-renders only when content changes.
 */
export const MarkdownContent = memo(MarkdownContentImpl);
