"use client";

import { Menu } from "lucide-react";
import Link from "next/link";

export function Header() {
  return (
    <nav className="fixed top-2 right-0 left-0 sm:top-0 z-[70] transition-all duration-500 ease-in-out p-0">
      <div className="mx-auto flex items-center justify-between border transition-all duration-400 ease-out w-full max-w-[85rem] border-transparent bg-transparent px-6 py-0 pt-1.5 shadow-none backdrop-blur-none">
        <Link href="/" className="flex items-center gap-2 font-semibold text-zinc-100">
          <ShieldIcon className="h-6 w-6" />
          agentsafe
        </Link>

        <div className="hidden md:flex items-center gap-6">
          <Link
            href="https://github.com/knhn1004/agentsafe"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-medium text-zinc-400 hover:text-zinc-100 transition-colors"
          >
            GitHub
          </Link>
          <Link
            href="https://pypi.org/project/agentsafe/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-medium text-zinc-400 hover:text-zinc-100 transition-colors"
          >
            PyPI
          </Link>
          <Link
            href="/docs/quickstart"
            className="text-sm font-medium text-zinc-400 hover:text-zinc-100 transition-colors"
          >
            Docs
          </Link>
        </div>

        <button
          className="md:hidden text-zinc-100 focus-visible:ring-primary/50 relative z-20 flex h-10 w-10 items-center justify-center rounded-full transition-all duration-200 hover:bg-white/10 focus:outline-none focus-visible:ring-2 active:scale-95"
          aria-label="Open menu"
        >
          <Menu className="h-6 w-6" />
        </button>
      </div>
    </nav>
  );
}

function ShieldIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  );
}
