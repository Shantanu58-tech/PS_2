// The one connected flow the whole console follows:
// 1 Situation Room (national glance) -> 2 Detect -> 3 Investigate -> 4 Evidence.
// The flow bar, the sidebar groups, page overlines and "next step" cards all read from here.

export interface Stage { n: number; id: string; label: string; desc: string; pages: string[] }

export const STAGES: Stage[] = [
  { n: 1, id: 'situation', label: 'Situation Room', desc: 'national glance', pages: ['/'] },
  { n: 2, id: 'detect', label: 'Detect', desc: 'platforms · trends · emotions', pages: ['/platforms', '/trends', '/timeline', '/search'] },
  { n: 3, id: 'investigate', label: 'Investigate', desc: 'networks · origin · audience', pages: ['/coordination', '/network', '/lineage', '/audience'] },
  { n: 4, id: 'evidence', label: 'Evidence', desc: 'cases · ledger', pages: ['/cases', '/ledger'] },
]

export function stageOf(path: string): Stage {
  return STAGES.find(s => s.pages.includes(path)) ?? STAGES[0]
}

/** What to do next from each page: keeps overview -> investigation -> evidence one click apart. */
export const NEXT: Record<string, { to: string; label: string; why: string }> = {
  '/': { to: '/trends', label: 'Detect: open Trends', why: 'See how each narrative is growing and whether the growth is organic.' },
  '/platforms': { to: '/trends', label: 'Trends', why: 'Compare the topics rising on every platform.' },
  '/trends': { to: '/coordination', label: 'Investigate: who is pushing it', why: 'Check whether a coordinated group is behind a manufactured trend.' },
  '/timeline': { to: '/coordination', label: 'Investigate: coordination', why: 'Remove the coordinated accounts and find out who they are.' },
  '/search': { to: '/trends', label: 'Trends', why: 'Place the posts you found inside their topic.' },
  '/coordination': { to: '/network', label: 'Network', why: 'See the group inside the wider network and who it reaches.' },
  '/network': { to: '/lineage', label: 'Lineage: where it started', why: 'Trace the narrative back to the first post and platform.' },
  '/lineage': { to: '/cases', label: 'Evidence: open a case', why: 'Package the findings with their ledger records.' },
  '/audience': { to: '/cases', label: 'Evidence: open a case', why: 'Package the findings with their ledger records.' },
  '/cases': { to: '/ledger', label: 'Verify the ledger', why: 'Prove none of the evidence has been changed since collection.' },
  '/ledger': { to: '/', label: 'Back to the Situation Room', why: 'Return to the national picture.' },
}

export const SECTOR_ICON: Record<string, string> = {
  infra: 'Zap', disaster: 'CloudRain', economy: 'IndianRupee', education: 'GraduationCap', civic: 'Landmark',
  health: 'HeartPulse', defence: 'Shield', tech: 'Cpu', culture: 'Trophy', other: 'Shapes',
}

export const LEVEL_LABEL: Record<string, string> = {
  critical: 'Critical', elevated: 'Elevated', watch: 'Watch', normal: 'Normal', quiet: 'Quiet',
}
