import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-zinc-800 bg-zinc-900/50">
      <div className="mx-auto max-w-[85rem] px-6 py-12">
        <div className="grid sm:grid-cols-3 gap-8">
          <div>
            <h4 className="font-semibold text-zinc-100 mb-4">Product</h4>
            <ul className="space-y-2">
              <li>
                <Link
                  href="https://pypi.org/project/agentsafe/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-zinc-400 hover:text-zinc-100"
                >
                  Install
                </Link>
              </li>
              <li>
                <Link
                  href="/docs/quickstart"
                  className="text-zinc-400 hover:text-zinc-100"
                >
                  Documentation
                </Link>
              </li>
              <li>
                <Link
                  href="https://github.com/knhn1004/agentsafe/tree/main/examples"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-zinc-400 hover:text-zinc-100"
                >
                  Examples
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-zinc-100 mb-4">Company</h4>
            <ul className="space-y-2">
              <li>
                <Link
                  href="https://github.com/knhn1004/agentsafe"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-zinc-400 hover:text-zinc-100"
                >
                  GitHub
                </Link>
              </li>
              <li>
                <Link
                  href="https://build.nvidia.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-zinc-400 hover:text-zinc-100"
                >
                  NVIDIA API
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-zinc-100 mb-4">Legal</h4>
            <ul className="space-y-2">
              <li>
                <span className="text-zinc-400">Apache 2.0 License</span>
              </li>
            </ul>
          </div>
        </div>
        <div className="mt-12 pt-8 border-t border-zinc-800 text-center text-sm text-zinc-500">
          © {new Date().getFullYear()} agentsafe contributors. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
