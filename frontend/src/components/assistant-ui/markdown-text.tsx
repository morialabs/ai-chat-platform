"use client";

import "@assistant-ui/react-markdown/styles/dot.css";
import {
  MarkdownTextPrimitive,
  unstable_memoizeMarkdownComponents as memoizeMarkdownComponents,
} from "@assistant-ui/react-markdown";
import remarkGfm from "remark-gfm";
import { memo, type FC } from "react";

// Define custom styled components for markdown elements
const defaultComponents = memoizeMarkdownComponents({
  h1: ({ children }) => <h1 className="text-2xl font-bold mb-4">{children}</h1>,
  h2: ({ children }) => <h2 className="text-xl font-bold mb-3">{children}</h2>,
  h3: ({ children }) => <h3 className="text-lg font-bold mb-2">{children}</h3>,
  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
  ul: ({ children }) => <ul className="list-disc pl-4 mb-2">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal pl-4 mb-2">{children}</ol>,
  li: ({ children }) => <li className="mb-1">{children}</li>,
  a: ({ href, children }) => (
    <a
      href={href}
      className="text-blue-500 hover:underline"
      target="_blank"
      rel="noopener noreferrer"
    >
      {children}
    </a>
  ),
  code: ({ children, className }) => {
    const isCodeBlock = className?.includes("language-");
    if (isCodeBlock) {
      return (
        <code
          className={`${className} block bg-gray-800 text-gray-100 p-3 rounded my-2 overflow-x-auto`}
        >
          {children}
        </code>
      );
    }
    return (
      <code className="bg-gray-200 dark:bg-gray-700 px-1 py-0.5 rounded text-sm">
        {children}
      </code>
    );
  },
  pre: ({ children }) => <pre className="my-2">{children}</pre>,
  blockquote: ({ children }) => (
    <blockquote className="border-l-4 border-gray-300 dark:border-gray-600 pl-4 italic my-2">
      {children}
    </blockquote>
  ),
});

const MarkdownTextImpl: FC = () => {
  return (
    <MarkdownTextPrimitive
      remarkPlugins={[remarkGfm]}
      className="prose dark:prose-invert max-w-none"
      components={defaultComponents}
    />
  );
};

export const MarkdownText = memo(MarkdownTextImpl);
