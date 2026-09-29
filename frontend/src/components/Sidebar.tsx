"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { NAV_ITEMS } from "@/lib/nav";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <nav aria-label="Console sections" className="flex flex-col gap-0.5 p-3">
      {NAV_ITEMS.map((item) => {
        const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={`group flex items-center justify-between rounded-sm border-l-2 px-3 py-2 text-sm transition-colors ${
              active
                ? "border-accent bg-panel-raised text-ink"
                : "border-transparent text-ink-muted hover:border-line-strong hover:bg-panel-raised hover:text-ink"
            }`}
          >
            <span>{item.label}</span>
            <span className="font-mono text-[10px] text-ink-faint group-hover:text-ink-muted">{item.code}</span>
          </Link>
        );
      })}
    </nav>
  );
}
