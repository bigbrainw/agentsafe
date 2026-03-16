export function UseWith() {
  const providers = [
    "OpenAI",
    "Anthropic",
    "LangChain",
    "NVIDIA",
    "Ollama",
    "Raw HTTP",
  ];

  return (
    <section className="px-6 py-12">
      <div className="mx-auto max-w-[85rem]">
        <p className="text-sm font-medium text-zinc-500 mb-6">Use it with</p>
        <div className="flex flex-wrap gap-3">
          {providers.map((name) => (
            <div
              key={name}
              className="rounded-lg border border-zinc-700 bg-zinc-800 px-4 py-2.5 text-sm font-medium text-zinc-300 shadow-sm"
            >
              {name}
            </div>
          ))}
          <span className="rounded-lg border border-zinc-700 bg-zinc-800/50 px-4 py-2.5 text-sm font-medium text-zinc-500">
            + more
          </span>
        </div>
      </div>
    </section>
  );
}
