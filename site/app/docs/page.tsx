import Link from "next/link";

export default function DocsPage() {
  return (
    <div className="py-12">
      <h1 className="text-2xl font-bold text-zinc-100 mb-4">Documentation</h1>
      <p className="text-zinc-400 mb-6">
        Get started with AgentSafe and add safety rails to your AI agents.
      </p>
      <Link
        href="/docs/quickstart"
        className="inline-flex items-center rounded-lg bg-violet-600 px-4 py-2 text-white font-medium hover:bg-violet-700"
      >
        Quickstart →
      </Link>
    </div>
  );
}
