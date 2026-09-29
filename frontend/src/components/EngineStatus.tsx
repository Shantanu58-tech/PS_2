"use client";

import { useEffect, useState } from "react";

import { fetchHealth, type HealthStatus } from "@/lib/api";

type EngineState =
  | { kind: "waking"; attempts: number }
  | { kind: "online"; health: HealthStatus }
  | { kind: "offline"; attempts: number };

const POLL_INTERVAL_MS = 4000;
const ONLINE_REFRESH_MS = 60000;
const MAX_WAKE_ATTEMPTS = 30;

export function EngineStatus() {
  const [state, setState] = useState<EngineState>({ kind: "waking", attempts: 0 });

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let attempts = 0;

    const poll = async () => {
      const controller = new AbortController();
      const abortTimer = setTimeout(() => controller.abort(), 8000);
      try {
        const health = await fetchHealth(controller.signal);
        if (cancelled) return;
        attempts = 0;
        setState({ kind: "online", health });
        timer = setTimeout(poll, ONLINE_REFRESH_MS);
      } catch {
        if (cancelled) return;
        attempts += 1;
        setState(attempts >= MAX_WAKE_ATTEMPTS ? { kind: "offline", attempts } : { kind: "waking", attempts });
        timer = setTimeout(poll, POLL_INTERVAL_MS);
      } finally {
        clearTimeout(abortTimer);
      }
    };

    poll();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, []);

  if (state.kind === "online") {
    return (
      <div className="flex items-center gap-2 font-mono text-[11px] text-ink-muted">
        <span className="h-2 w-2 rounded-full bg-ok" />
        <span>ENGINE ONLINE</span>
        <span className="text-ink-faint">v{state.health.version}</span>
        <span className="rounded-sm border border-line-strong px-1.5 py-0.5 uppercase text-accent">
          {state.health.mode}
        </span>
      </div>
    );
  }

  if (state.kind === "offline") {
    return (
      <div className="flex items-center gap-2 font-mono text-[11px] text-alert">
        <span className="h-2 w-2 rounded-full bg-alert" />
        <span>ENGINE UNREACHABLE</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 font-mono text-[11px] text-warn">
      <span className="h-2 w-2 animate-pulse rounded-full bg-warn" />
      <span>STARTING ENGINE{state.attempts > 0 ? ` · attempt ${state.attempts}` : ""}</span>
    </div>
  );
}
