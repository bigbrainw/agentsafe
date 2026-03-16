"use client";

import { Code } from "@/components/SyntaxHighlighter";

interface DocCodeBlockProps {
  code: string;
  language?: string;
}

export function DocCodeBlock({ code, language = "python" }: DocCodeBlockProps) {
  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-900 overflow-hidden my-4">
      <div className="flex items-center justify-between px-4 py-2 border-b border-zinc-700 bg-zinc-800">
        <span className="text-xs font-medium text-zinc-400 uppercase tracking-wide">
          {language}
        </span>
      </div>
      <div className="overflow-x-auto [&>div]:!bg-transparent [&>pre]:!p-4">
        <Code code={code} language={language} />
      </div>
    </div>
  );
}
