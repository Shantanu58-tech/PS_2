import { findNavItem } from "@/lib/nav";

export function SectionPlaceholder({ href }: { href: string }) {
  const item = findNavItem(href);

  return (
    <section className="flex flex-col gap-6">
      <header className="flex flex-col gap-2 border-b border-line pb-5">
        <p className="font-mono text-[11px] tracking-[0.2em] text-ink-faint">{item.code}</p>
        <h1 className="text-2xl font-semibold tracking-tight text-ink">{item.label}</h1>
        <p className="max-w-3xl text-sm leading-relaxed text-ink-muted">{item.summary}</p>
      </header>
      <div className="rounded-sm border border-dashed border-line-strong bg-panel p-8">
        <p className="font-mono text-xs text-ink-muted">
          Not yet built. This view is delivered in <span className="text-accent">Phase {item.phase}</span> and will
          only show measured results backed by evidence.
        </p>
      </div>
    </section>
  );
}
