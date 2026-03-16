"use client";

import { useEffect, useState } from "react";

export interface TocItem {
  id: string;
  label: string;
  children?: { id: string; label: string }[];
}

interface OnThisPageProps {
  items: TocItem[];
}

export function OnThisPage({ items }: OnThisPageProps) {
  const [activeId, setActiveId] = useState<string | null>(null);

  useEffect(() => {
    const ids = items.flatMap((item) =>
      item.children ? [item.id, ...item.children.map((c) => c.id)] : [item.id]
    );

    const updateActiveId = () => {
      const offset = 120;
      const viewportTop = window.scrollY + offset;
      let current: string | null = null;
      for (const id of ids) {
        const el = document.getElementById(id);
        if (el && el.offsetTop <= viewportTop) {
          current = id;
        }
      }
      setActiveId(current ?? ids[0]);
    };

    updateActiveId();
    window.addEventListener("scroll", updateActiveId, { passive: true });
    return () => window.removeEventListener("scroll", updateActiveId);
  }, [items]);

  return (
    <nav
      className="hidden xl:block w-56 shrink-0"
      aria-label="On this page"
    >
      <div className="sticky top-24">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-4">
          On this page
        </h3>
        <ul className="space-y-1 text-sm">
          {items.map((item) => (
            <li key={item.id}>
              <a
                href={`#${item.id}`}
                className={`block py-1 transition-colors ${
                  activeId === item.id
                    ? "text-violet-400 font-medium"
                    : "text-zinc-400 hover:text-zinc-100"
                }`}
              >
                {item.label}
              </a>
              {item.children && (
                <ul className="ml-4 mt-1 space-y-1 border-l border-zinc-700 pl-3">
                  {item.children.map((child) => (
                    <li key={child.id}>
                      <a
                        href={`#${child.id}`}
                        className={`block py-1 transition-colors ${
                          activeId === child.id
                            ? "text-violet-400 font-medium"
                            : "text-zinc-400 hover:text-zinc-100"
                        }`}
                      >
                        {child.label}
                      </a>
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}
