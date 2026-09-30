/**
 * DEEPASTAMBHA mark: a deepastambha, the Indian temple lamp tower that keeps a light
 * burning through the night, drawn inside a round seal. The six lamps on its three
 * tiers stand for the six platforms watched; the saffron flame on top is the
 * watchful flame, with listening arcs around it; the green base line completes
 * the tricolour. An original project emblem, not an official insignia.
 * Below 28px the seal's dotted ring and outer arcs are dropped so it stays legible.
 */
export function DeepastambhaMark({ size = 36 }: { size?: number }) {
  const full = size >= 28
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" role="img" aria-label="DEEPASTAMBHA logo">
      <circle cx="32" cy="32" r="30" fill="#FBF6EF" stroke="#C87D43" strokeWidth={full ? 2.5 : 3.5} />
      {full && <circle cx="32" cy="32" r="26" fill="none" stroke="#B89F88" strokeWidth="1" strokeDasharray="1.6 2.4" />}
      <g fill="none" stroke="#C87D43" strokeWidth="1.6" strokeLinecap="round">
        <path d="M25.8 8.6 Q22.8 13 25.8 17.4" /><path d="M38.2 8.6 Q41.2 13 38.2 17.4" />
        {full && <><path d="M22.4 6.6 Q18.4 13 22.4 19.4" opacity=".6" /><path d="M41.6 6.6 Q45.6 13 41.6 19.4" opacity=".6" /></>}
      </g>
      <path d="M32 6.2 C35.9 10.8 36.3 14.1 34.5 16.8 C33.7 18 32.8 18.6 32 18.8 C31.2 18.6 30.3 18 29.5 16.8 C27.7 14.1 28.1 10.8 32 6.2 Z" fill="#FF9933" />
      <path d="M32 10.8 C33.6 13.1 33.7 14.9 33 16.2 C32.7 16.8 32.4 17.1 32 17.2 C31.6 17.1 31.3 16.8 31 16.2 C30.3 14.9 30.4 13.1 32 10.8 Z" fill="#FFE6B8" />
      <rect x="29" y="19.4" width="6" height="2.2" rx=".6" fill="#3E342F" />
      <polygon points="28.2,50 35.8,50 34.2,21.4 29.8,21.4" fill="#3E342F" />
      <g stroke="#3E342F" strokeWidth="2.3" strokeLinecap="round">
        <line x1="22" y1="44" x2="42" y2="44" /><line x1="24" y1="36.5" x2="40" y2="36.5" /><line x1="26" y1="29" x2="38" y2="29" />
      </g>
      <g fill="#FF9933">
        <circle cx="22" cy="41.7" r="2.1" /><circle cx="42" cy="41.7" r="2.1" />
        <circle cx="24" cy="34.2" r="2.1" /><circle cx="40" cy="34.2" r="2.1" />
        <circle cx="26" cy="26.7" r="2.1" /><circle cx="38" cy="26.7" r="2.1" />
      </g>
      <rect x="25" y="47.6" width="14" height="2.6" rx=".6" fill="#5F4837" />
      <rect x="22" y="50" width="20" height="3.6" rx=".8" fill="#3E342F" />
      <line x1="19.5" y1="55.4" x2="44.5" y2="55.4" stroke="#138808" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  )
}

export const TAGLINE = 'Every narrative watched. Every record kept.'
export const TAGLINE_HI = 'हर कथा पर नज़र · हर अभिलेख सुरक्षित'

export function DeepastambhaLogo({ size = 36, compact = false }: { size?: number; compact?: boolean }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 10 }}>
      <DeepastambhaMark size={size} />
      {!compact && (
        <span style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.1 }}>
          <span style={{ fontWeight: 800, fontSize: 19, letterSpacing: '0.08em', color: 'var(--ink-1)' }}>DEEPASTAMBHA</span>
          <span style={{ fontSize: 11.5, color: 'var(--ink-3)', fontWeight: 500 }}>दीपस्तम्भ · narrative watch</span>
        </span>
      )}
    </span>
  )
}
