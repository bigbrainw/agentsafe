import {
  Search,
  Target,
  Shield,
  Wrench,
  BarChart3,
  LineChart,
  Bell,
  Globe,
  Zap,
  Plug,
} from "lucide-react";

const features = [
  {
    icon: Search,
    title: "Input scanning",
    description: "Check user prompts before they reach your agent",
  },
  {
    icon: Target,
    title: "Intended-use scope guard",
    description: "Block requests that are outside your app's purpose",
  },
  {
    icon: Shield,
    title: "Output scanning",
    description: "Verify agent responses before they reach users",
  },
  {
    icon: Wrench,
    title: "Tool call checking",
    description: "Inspect tool calls before execution",
  },
  {
    icon: BarChart3,
    title: "Built-in observability",
    description: "Metrics, traces, structured logs — zero config. OpenTelemetry-ready.",
  },
  {
    icon: LineChart,
    title: "OpenTelemetry export",
    description: "Export traces to Jaeger, Datadog, Grafana, Honeycomb via OpenTelemetry OTLP",
  },
  {
    icon: Bell,
    title: "Violation callbacks",
    description: "Get alerted on Slack, PagerDuty, webhooks",
  },
  {
    icon: Globe,
    title: "Multilingual",
    description: "9 languages via Nemotron Safety Guard",
  },
  {
    icon: Zap,
    title: "Async support",
    description: "First-class async/await support",
  },
  {
    icon: Plug,
    title: "Framework agnostic",
    description: "Works with OpenAI, Anthropic, LangChain, raw HTTP",
  },
];

export function Features() {
  return (
    <section className="px-6 py-16">
      <div className="mx-auto max-w-[85rem]">
        <h2 className="text-3xl font-bold text-zinc-100 mb-2">
          Orchestrate agents with safety + observability
        </h2>
        <p className="text-lg text-zinc-400 mb-12">
          One SDK. Everything you need to ship safe agents, fast.
        </p>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map(({ icon: Icon, title, description }) => (
            <div
              key={title}
              className="rounded-xl border border-zinc-700 bg-zinc-800/50 p-6 shadow-sm hover:border-zinc-600 transition-colors"
            >
              <Icon className="h-8 w-8 text-violet-400 mb-4" />
              <h3 className="font-semibold text-zinc-100 mb-2">{title}</h3>
              <p className="text-sm text-zinc-400">{description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
