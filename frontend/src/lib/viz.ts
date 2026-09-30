// Chart colour roles. Values come from CSS tokens (validated palette, both themes),
// so charts re-colour with the theme. Colour follows the ENTITY via fixed slots,
// never its rank (dataviz: no recolour-on-filter).

export const EMOTIONS = ['anxiety', 'excitement', 'supportive', 'against', 'sarcasm'] as const
export type Emotion = (typeof EMOTIONS)[number]
export const EMOTION_SLOT: Record<Emotion, string> = {
  anxiety: 'var(--s1)', excitement: 'var(--s2)', supportive: 'var(--s3)', against: 'var(--s4)', sarcasm: 'var(--s5)',
}
export const EMOTION_LABEL: Record<Emotion, string> = {
  anxiety: 'Anxiety / panic', excitement: 'Excitement', supportive: 'Supportive', against: 'Against', sarcasm: 'Sarcasm',
}

export const PLATFORMS = ['x', 'telegram', 'instagram', 'facebook', 'reddit', 'youtube'] as const
export const PLATFORM_SLOT: Record<string, string> = {
  x: 'var(--s1)', telegram: 'var(--s2)', reddit: 'var(--s3)', youtube: 'var(--s4)', instagram: 'var(--s5)', facebook: 'var(--s6)',
}
export const PLATFORM_LABEL: Record<string, string> = {
  x: 'X', telegram: 'Telegram', reddit: 'Reddit', youtube: 'YouTube', instagram: 'Instagram', facebook: 'Facebook', synthetic: 'Synthetic',
}

// Raw vs organic uses EMPHASIS: organic is the story (slot 1), raw is context (neutral).
export const ORGANIC = 'var(--s1)'
export const RAW = 'var(--neutral-series)'

// Status colours are reserved for state and always paired with an icon + label.
export const STATUS = { good: 'var(--good)', warning: 'var(--warning)', serious: 'var(--serious)', critical: 'var(--critical)' }

// Recharts needs concrete colours for SVG gradients/fills in some places; resolve tokens at render time.
export function cssVar(name: string): string {
  if (typeof window === 'undefined') return '#888'
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || '#888'
}

export const AXIS_TICK = { fill: 'var(--ink-3)', fontSize: 11 }
export const GRID = { stroke: 'var(--hairline)', strokeDasharray: undefined as undefined, vertical: false }
