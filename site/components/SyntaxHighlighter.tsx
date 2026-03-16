"use client";

import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

interface SyntaxHighlighterProps {
  code: string;
  language?: string;
  className?: string;
  size?: "sm" | "base" | "lg";
}

const fontSizeMap = { sm: "0.8125rem", base: "0.9375rem", lg: "1.0625rem" };

export function Code({ code, language = "python", className = "", size = "base" }: SyntaxHighlighterProps) {
  return (
    <SyntaxHighlighter
      language={language}
      style={oneDark}
      customStyle={{
        margin: 0,
        padding: "1rem",
        background: "transparent",
        fontSize: fontSizeMap[size],
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
