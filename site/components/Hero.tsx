import Link from "next/link";
import { ArrowRight } from "lucide-react";

export function Hero() {
  return (
    <section className="pt-16 pb-12 px-6">
      <div className="mx-auto max-w-[85rem]">
        <div className="inline-flex items-center gap-2 rounded-full border border-violet-500/50 bg-violet-950/50 px-3 py-1 mb-4">
          <span className="text-xs font-bold uppercase tracking-wide text-violet-400">New</span>
          <span className="text-sm text-zinc-300">
            AgentSafe — lightweight safety with zero config
          </span>
          <ArrowRight className="h-3.5 w-3.5 text-violet-400" />
        </div>

        <div className="inline-flex items-center gap-2 rounded-full border border-amber-500/50 bg-zinc-800 px-3 py-1 mb-6">
          <span className="text-sm font-medium text-zinc-300">Powered by</span>
          <span className="font-semibold text-zinc-100">NVIDIA Nemotron</span>
        </div>

        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-zinc-100 mb-3">
          AgentSafe, Zero Config
        </h1>
        <p className="text-lg text-zinc-400 max-w-2xl mb-8">
          One decorator. Full observability with OpenTelemetry. Wrap any agent with input/output safety checks using NVIDIA&apos;s Nemotron Safety Guard.
        </p>

        <div className="flex flex-wrap gap-3">
          <Link
            href="https://github.com/knhn1004/agentsafe/tree/main/examples"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-full bg-violet-600 px-5 py-2.5 text-sm text-white font-medium hover:bg-violet-700 transition-colors"
          >
            Get Started
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
          <Link
            href="/docs/quickstart"
            className="inline-flex items-center rounded-full border border-zinc-600 bg-zinc-800 px-5 py-2.5 text-sm text-zinc-200 font-medium hover:bg-zinc-700 transition-colors"
          >
            Docs
          </Link>
        </div>
      </div>
    </section>
  );
}
