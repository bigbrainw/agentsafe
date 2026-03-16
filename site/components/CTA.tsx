import Link from "next/link";
import { ArrowRight } from "lucide-react";

export function CTA() {
  return (
    <section className="px-6 py-20">
      <div className="mx-auto max-w-[85rem] text-center">
        <h2 className="text-3xl font-bold text-zinc-100 mb-4">
          Start Shipping Safe Agents Today
        </h2>
        <p className="text-lg text-zinc-400 mb-8 max-w-xl mx-auto">
          Add a one-line decorator to any agent. No YAML, no Docker, no framework lock-in.
        </p>
        <div className="flex flex-wrap justify-center gap-4">
          <Link
            href="http://localhost:7862"
            className="inline-flex items-center gap-2 rounded-full bg-violet-600 px-6 py-3 text-white font-medium hover:bg-violet-700 transition-colors"
          >
            Get Started
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="https://github.com/knhn1004/agentsafe"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center rounded-full border border-zinc-600 bg-zinc-800 px-6 py-3 text-zinc-200 font-medium hover:bg-zinc-700 transition-colors"
          >
            View on GitHub
          </Link>
        </div>
      </div>
    </section>
  );
}
