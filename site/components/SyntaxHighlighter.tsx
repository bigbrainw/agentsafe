"use client";

import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

interface SyntaxHighlighterProps {
  code: string;
  language?: string;
  className?: string;
}

export function Code({ code, language = "python", className = "" }: SyntaxHighlighterProps) {
  return (
    <SyntaxHighlighter
      language={language}
      style={oneDark}
      customStyle={{
        margin: 0,
        padding: "1rem",
        background: "transparent",
        fontSize: "0.875rem",
      }}
      codeTagProps={{ style: { fontFamily: "var(--font-geist-mono), monospace" } }}
      showLineNumbers={false}
      PreTag="div"
      className={className}
    >
      {code}
    </SyntaxHighlighter>
  );
}
