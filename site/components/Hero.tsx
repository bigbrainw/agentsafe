import Link from "next/link";
import { ArrowRight } from "lucide-react";

export function Hero() {
  return (
    <section className="pt-24 pb-16 px-6">
      <div className="mx-auto max-w-[85rem]">
        <div className="inline-flex items-center gap-2 rounded-full border border-violet-200 bg-violet-50 px-4 py-1.5 mb-6">
          <span className="text-xs font-bold uppercase tracking-wide text-violet-600">New</span>
          <span className="text-sm text-zinc-700">
            Lightweight AI agent safety with zero config
          </span>
          <ArrowRight className="h-4 w-4 text-violet-600" />
        </div>

        <div className="inline-flex items-center gap-2 rounded-full border border-amber-200 bg-white px-4 py-1.5 mb-8">
          <span className="text-sm font-medium text-zinc-700">Powered by</span>
          <span className="font-semibold text-zinc-900">NVIDIA Nemotron</span>
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-zinc-900 mb-4">
          AI Agent Safety, Zero Config
        </h1>
        <p className="text-xl text-zinc-600 max-w-2xl mb-10">
          One decorator. Full observability. Wrap any agent with input/output safety checks using NVIDIA&apos;s Nemotron Safety Guard.
        </p>

        <div className="flex flex-wrap gap-4">
          <Link
            href="http://localhost:7862"
            className="inline-flex items-center gap-2 rounded-full bg-violet-600 px-6 py-3 text-white font-medium hover:bg-violet-700 transition-colors"
          >
            Get Started
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="https://github.com/knhn1004/agentsafe/blob/main/README.md"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center rounded-full border border-zinc-300 bg-white px-6 py-3 text-zinc-700 font-medium hover:bg-zinc-50 transition-colors"
          >
            Docs
          </Link>
        </div>
      </div>
    </section>
  );
}
