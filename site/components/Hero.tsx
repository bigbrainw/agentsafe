import Link from "next/link";
import { ArrowRight } from "lucide-react";

export function Hero() {
  return (
    <section className="pt-24 pb-16 px-6">
      <div className="mx-auto max-w-[85rem]">
        <div className="inline-flex items-center gap-2 rounded-full border border-violet-500/50 bg-violet-950/50 px-4 py-1.5 mb-6">
          <span className="text-xs font-bold uppercase tracking-wide text-violet-400">New</span>
          <span className="text-sm text-zinc-300">
            Lightweight AI agent safety with zero config
          </span>
          <ArrowRight className="h-4 w-4 text-violet-400" />
        </div>

        <div className="inline-flex items-center gap-2 rounded-full border border-amber-500/50 bg-zinc-800 px-4 py-1.5 mb-8">
          <span className="text-sm font-medium text-zinc-300">Powered by</span>
          <span className="font-semibold text-zinc-100">NVIDIA Nemotron</span>
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-zinc-100 mb-4">
          AI Agent Safety, Zero Config
        </h1>
        <p className="text-xl text-zinc-400 max-w-2xl mb-10">
          One decorator. Full observability. Wrap any agent with input/output safety checks using NVIDIA&apos;s Nemotron Safety Guard.
        </p>

        <div className="flex flex-wrap gap-4">
          <Link
            href="https://github.com/knhn1004/agentsafe/tree/main/examples"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-full bg-violet-600 px-6 py-3 text-white font-medium hover:bg-violet-700 transition-colors"
          >
            Get Started
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/docs/quickstart"
            className="inline-flex items-center rounded-full border border-zinc-600 bg-zinc-800 px-6 py-3 text-zinc-200 font-medium hover:bg-zinc-700 transition-colors"
          >
            Docs
          </Link>
        </div>
      </div>
    </section>
  );
}
