export function CodeBlock() {
  const code = `from agentsafe import safe

@safe
def my_agent(prompt: str) -> str:
    return call_any_llm(prompt)

my_agent("What's the weather?")     # passes through
my_agent("How to make a bomb?")     # raises SafetyViolation`;

  return (
    <section className="px-6 pb-16">
      <div className="mx-auto max-w-[85rem]">
        <div className="rounded-xl border border-zinc-200 bg-white shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-200 bg-zinc-50">
            <span className="text-sm font-medium text-zinc-600">AGENTSAFE SDK</span>
            <div className="flex items-center gap-2">
              <span className="text-xs text-zinc-500">Python</span>
              <a
                href="https://github.com/knhn1004/agentsafe"
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-500 hover:text-zinc-700"
              >
                GitHub
              </a>
            </div>
          </div>
          <div className="p-4 overflow-x-auto">
            <pre className="text-sm font-mono text-zinc-800">
              <code>{code}</code>
            </pre>
          </div>
        </div>
      </div>
    </section>
  );
}
