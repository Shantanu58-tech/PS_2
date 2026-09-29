export type NavItem = {
  href: string;
  label: string;
  code: string;
  summary: string;
  phase: number;
};

export const NAV_ITEMS: NavItem[] = [
  {
    href: "/",
    label: "Overview",
    code: "OVR",
    summary: "Replay or live clock, top narratives with velocity, coordination share and affect sparkline.",
    phase: 4,
  },
  {
    href: "/narratives",
    label: "Narratives",
    code: "NAR",
    summary:
      "Timeline, affect over time by platform, representative posts, cross-platform cascade lineage and forecast band.",
    phase: 4,
  },
  {
    href: "/coordination",
    label: "Coordination",
    code: "CRD",
    summary: "Coordinated clusters with null-model p-values, evidence posts and a timing heatmap.",
    phase: 4,
  },
  {
    href: "/network",
    label: "Network",
    code: "NET",
    summary: "Interactive graph, KOL table with temporal influence metrics and community flow.",
    phase: 4,
  },
  {
    href: "/audience",
    label: "Audience",
    code: "AUD",
    summary:
      "Aggregate-only language, state, interest and age-band estimates with k-suppression, DP epsilon and intervals.",
    phase: 4,
  },
  {
    href: "/eval",
    label: "Eval card",
    code: "EVL",
    summary: "Hinglish affect metrics against baselines, calibration, abstention and known failure cases.",
    phase: 2,
  },
  {
    href: "/audit",
    label: "Audit",
    code: "LDG",
    summary: "Query ledger, hourly Merkle roots, integrity verification and refused queries.",
    phase: 3,
  },
  {
    href: "/sources",
    label: "Sources",
    code: "SRC",
    summary: "Connector status, X budget used, provenance mix and platform terms of service notes.",
    phase: 1,
  },
];

export function findNavItem(href: string): NavItem {
  const item = NAV_ITEMS.find((entry) => entry.href === href);
  if (!item) {
    throw new Error(`Unknown console route: ${href}`);
  }
  return item;
}
