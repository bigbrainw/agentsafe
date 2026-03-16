import { DocCodeBlock } from "@/components/DocCodeBlock";
import { DocCard } from "@/components/DocCard";
import { CursorBackground } from "@/components/CursorBackground";
import { OnThisPage } from "@/components/OnThisPage";

export const metadata = {
  title: "Quickstart — agentsafe",
  description:
    "Learn how to add safety rails to your AI agents in minutes with agentsafe.",
};

const tocItems = [
  { id: "what-are-you-trying-to-do", label: "What are you trying to do?" },
  { id: "installation", label: "Installation" },
  { id: "api-key", label: "Set Your API Key" },
  {
    id: "first-request",
    label: "Your First Request",
    children: [
      { id: "decorator", label: "1) One-line decorator" },
      { id: "wrapper", label: "2) SafeAgent wrapper" },
      { id: "tool-calls", label: "3) Tool call checking" },
      { id: "streaming", label: "4) Stream output" },
    ],
  },
  { id: "next-steps", label: "Next steps" },
];

export default function QuickstartPage() {
  return (
    <div className="relative flex gap-12">
      <CursorBackground />

      <div className="flex-1 min-w-0">
      <h1 className="text-3xl font-bold text-zinc-100 mb-2">Quickstart</h1>
      <p className="text-zinc-400 mb-12">
        Learn how to add safety rails to your AI agents in minutes. agentsafe helps you:
      </p>
      <ul className="list-disc list-inside text-zinc-400 mb-12 space-y-1">
        <li>Check user prompts before they reach your agent</li>
        <li>Verify agent outputs before they reach users</li>
        <li>Inspect tool calls before execution</li>
        <li>Get metrics, traces, and alerts with zero config</li>
      </ul>

      <h2 id="what-are-you-trying-to-do" className="text-xl font-semibold text-zinc-100 mb-4">
        What are you trying to do?
      </h2>
      <div className="grid sm:grid-cols-2 gap-4 mb-16">
        <DocCard
          title="Add input safety"
          description="Check user prompts before they reach your agent. Block prompt injection and out-of-scope requests."
          icon="shield"
          href="#decorator"
        />
        <DocCard
          title="Add output safety"
          description="Verify agent responses before they reach users. Block harmful or unsafe content."
          icon="message"
          href="#decorator"
        />
        <DocCard
          title="Check tool calls"
          description="Inspect tool calls before execution. Prevent SQL injection, file deletion, and other dangerous ops."
          icon="wrench"
          href="#tool-calls"
        />
        <DocCard
          title="Add observability"
          description="Get metrics, traces, and violation callbacks. Export to Jaeger, Datadog, Grafana."
          icon="chart"
          href="#wrapper"
        />
        <DocCard
          title="Stream safely"
          description="Use safe_stream for streaming agents. Buffers output, runs checks, then yields chunks."
          icon="bolt"
          href="#streaming"
        />
        <DocCard
          title="Scope to intended use"
          description="Block requests outside your app's purpose. E.g. a chicken-finder bot only answers food queries."
          icon="target"
          href="https://github.com/knhn1004/agentsafe/blob/main/README.md#intended-use-scope-guard"
          external
        />
      </div>

      <h2 id="installation" className="text-xl font-semibold text-zinc-100 mb-4">Installation</h2>
      <DocCodeBlock
        code={`# Core (minimal: httpx, pydantic, rich)
uv add agentsafe

# With OpenTelemetry export
uv add agentsafe[otel]

# With OpenAI client support
uv add agentsafe[openai]

# With Gradio UI demos
uv add agentsafe[ui]

# Everything
uv add agentsafe[all]`}
        language="bash"
      />

      <h2 id="api-key" className="text-xl font-semibold text-zinc-100 mb-4 mt-12">
        Set Your API Key
      </h2>
      <p className="text-zinc-400 mb-4">
        Get a free NVIDIA API key from{" "}
        <a
          href="https://build.nvidia.com"
          target="_blank"
          rel="noopener noreferrer"
          className="text-violet-400 hover:underline"
        >
          build.nvidia.com
        </a>{" "}
        and set it as an environment variable:
      </p>
      <DocCodeBlock
        code={`export NVIDIA_API_KEY="nvapi-..."`}
        language="bash"
      />
      <p className="text-sm text-zinc-500 mt-2">
        Or use a <code className="rounded bg-zinc-800 px-1 py-0.5">.env</code> file.
      </p>

      <h2 id="first-request" className="text-xl font-semibold text-zinc-100 mb-4 mt-12">
        Your First Request
      </h2>
      <p className="text-zinc-400 mb-6">
        Let&apos;s build this incrementally.
      </p>

      <h3 className="text-lg font-semibold text-zinc-100 mb-3" id="decorator">
        1) One-line decorator
      </h3>
      <p className="text-zinc-400 mb-4">
        Wrap any agent function with <code className="rounded bg-zinc-800 px-1 py-0.5">@safe</code>.
        Input and output are checked automatically.
      </p>
      <DocCodeBlock
        code={`from agentsafe import safe

@safe
def my_agent(prompt: str) -> str:
    return my_llm.generate(prompt)

result = my_agent("hello")  # checked and safe`}
      />

      <h3 className="text-lg font-semibold text-zinc-100 mb-3 mt-10" id="wrapper">
        2) SafeAgent wrapper (more control)
      </h3>
      <p className="text-zinc-400 mb-4">
        Use <code className="rounded bg-zinc-800 px-1 py-0.5">SafeAgent</code> for config, observability, and named agents.
      </p>
      <DocCodeBlock
        code={`from agentsafe import SafeAgent, AgentSafeConfig

config = AgentSafeConfig(
    check_input=True,
    check_output=True,
    block_on_unsafe=True,
)

agent = SafeAgent(my_agent_fn, config=config, name="my-agent")
result = agent("hello")

# After some interactions...
agent.observer.print_report()`}
      />

      <h3 className="text-lg font-semibold text-zinc-100 mb-3 mt-10" id="tool-calls">
        3) Tool call checking
      </h3>
      <p className="text-zinc-400 mb-4">
        Before executing a tool, check it. Unsafe calls raise <code className="rounded bg-zinc-800 px-1 py-0.5">SafetyViolation</code>.
      </p>
      <DocCodeBlock
        code={`agent = SafeAgent(my_fn)

# Before executing a tool, check it
agent.check_tool_call("execute_sql", {"query": "DROP TABLE users"})
# raises SafetyViolation`}
      />

      <h3 className="text-lg font-semibold text-zinc-100 mb-3 mt-10" id="streaming">
        4) Stream output
      </h3>
      <p className="text-zinc-400 mb-4">
        Use <code className="rounded bg-zinc-800 px-1 py-0.5">@safe_stream</code> for streaming agents.
        Buffers the full response, runs output checks, then yields chunks.
      </p>
      <DocCodeBlock
        code={`from agentsafe import AgentSafeConfig, safe_stream

@safe_stream(config=AgentSafeConfig(check_input=True, check_output=True))
def my_streaming_agent(prompt: str):
    yield "hello "
    yield "world"

for chunk in my_streaming_agent("hi"):
    print(chunk, end="")`}
      />

      <h2 id="next-steps" className="text-xl font-semibold text-zinc-100 mb-4 mt-16">
        Next steps
      </h2>
      <div className="grid sm:grid-cols-2 gap-4 mb-16">
        <DocCard
          title="Examples"
          description="Run the SJSU chicken chatbot, Gradio UI demos, and OpenTelemetry notebooks."
          icon="lightbulb"
          href="https://github.com/knhn1004/agentsafe/tree/main/examples"
          external
        />
        <DocCard
          title="Full documentation"
          description="Observability, scope guard, OpenAI client, violation callbacks, and more."
          icon="book"
          href="https://github.com/knhn1004/agentsafe/blob/main/README.md"
          external
        />
      </div>

      <p className="text-sm text-zinc-500 border-t border-zinc-800 pt-8">
        <strong>Go deeper:</strong>{" "}
        <a
          href="https://github.com/knhn1004/agentsafe/blob/main/README.md#observability"
          target="_blank"
          rel="noopener noreferrer"
          className="text-violet-400 hover:underline"
        >
          Observability
        </a>
        {" · "}
        <a
          href="https://github.com/knhn1004/agentsafe/blob/main/README.md#intended-use-scope-guard"
          target="_blank"
          rel="noopener noreferrer"
          className="text-violet-400 hover:underline"
        >
          Scope guard
        </a>
        {" · "}
        <a
          href="https://github.com/knhn1004/agentsafe/blob/main/README.md#safety-categories"
          target="_blank"
          rel="noopener noreferrer"
          className="text-violet-400 hover:underline"
        >
          Safety categories
        </a>
      </p>
      </div>

      <OnThisPage items={tocItems} />
    </div>
  );
}
