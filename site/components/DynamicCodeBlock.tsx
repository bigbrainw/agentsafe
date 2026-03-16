"use client";

import { useState } from "react";
import { Code } from "@/components/SyntaxHighlighter";

const MODEL_SNIPPETS: Record<string, string> = {
  simple: `from agentsafe import safe

@safe
def my_agent(prompt: str) -> str:
    return call_any_llm(prompt)

my_agent("What's the weather?")     # passes through
my_agent("How to make a bomb?")     # raises SafetyViolation`,

  nvidia: `from openai import OpenAI
from agentsafe import SafeAgent

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="..."  # or os.environ["NVIDIA_API_KEY"]
)
agent = SafeAgent.from_openai(client, model="nvidia/llama-3.1-8b-instruct")

result = agent("explain quantum computing")`,

  openai: `from openai import OpenAI
from agentsafe import SafeAgent

client = OpenAI(api_key="...")
agent = SafeAgent.from_openai(client, model="gpt-4o")

result = agent("explain quantum computing")`,

  anthropic: `from anthropic import Anthropic
from agentsafe import SafeAgent

def my_agent(prompt: str) -> str:
    client = Anthropic()
    msg = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text

agent = SafeAgent(my_agent, name="claude-agent")
result = agent("hello")`,
};

const MODELS = [
  { id: "simple", label: "Simple (@safe)" },
  { id: "nvidia", label: "NVIDIA" },
  { id: "openai", label: "OpenAI" },
  { id: "anthropic", label: "Anthropic" },
] as const;

export function DynamicCodeBlock() {
  const [model, setModel] = useState<string>("simple");

  return (
    <section className="px-6 pb-16">
      <div className="mx-auto max-w-3xl">
        <div className="rounded-xl border border-zinc-700 bg-zinc-900 shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-zinc-700 bg-zinc-800">
            <span className="text-base font-medium text-zinc-400">AGENTSAFE SDK</span>
            <div className="flex items-center gap-2 flex-wrap">
              <div className="flex flex-wrap rounded-lg bg-zinc-800/80 p-1 gap-0.5">
                {MODELS.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => setModel(m.id)}
                    className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                      model === m.id
                        ? "bg-violet-600 text-white"
                        : "text-zinc-400 hover:text-zinc-200"
                    }`}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
              <a
                href="https://github.com/knhn1004/agentsafe"
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-500 hover:text-zinc-300 text-sm"
              >
                GitHub
              </a>
            </div>
          </div>
          <div className="overflow-x-auto [&>div]:!bg-transparent [&>pre]:!p-6">
            <Code code={MODEL_SNIPPETS[model] ?? MODEL_SNIPPETS.simple} language="python" size="lg" />
          </div>
        </div>
      </div>
    </section>
  );
}
