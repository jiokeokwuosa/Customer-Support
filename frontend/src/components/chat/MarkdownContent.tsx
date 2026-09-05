"use client";

import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";

type MarkdownContentProps = {
  content: string;
  className?: string;
};

const components: Components = {
  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
  strong: ({ children }) => (
    <strong className="font-semibold text-ink">{children}</strong>
  ),
  em: ({ children }) => <em className="italic">{children}</em>,
  ul: ({ children }) => (
    <ul className="mb-2 list-disc space-y-1 pl-5 last:mb-0">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="mb-2 list-decimal space-y-1 pl-5 last:mb-0">{children}</ol>
  ),
  li: ({ children }) => <li className="leading-5">{children}</li>,
  a: ({ href, children }) => (
    <a
      href={href}
      className="underline underline-offset-2 hover:text-primary"
      target="_blank"
      rel="noreferrer"
    >
      {children}
    </a>
  ),
  code: ({ children }) => (
    <code className="rounded-button bg-surface px-1 py-0.5 text-[0.9em]">
      {children}
    </code>
  ),
  pre: ({ children }) => (
    <pre className="mb-2 overflow-x-auto rounded-button bg-surface p-2 text-xs last:mb-0">
      {children}
    </pre>
  ),
};

export function MarkdownContent({ content, className }: MarkdownContentProps) {
  return (
    <div className={className}>
      <ReactMarkdown components={components}>{content}</ReactMarkdown>
    </div>
  );
}
