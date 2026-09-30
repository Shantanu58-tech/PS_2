/**
 * PRAHARI mark: a sentinel's shield holding a watchful eye. The pupil is a
 * network node with three links, for narratives spreading between accounts.
 * An original project emblem.
 */
export function PrahariMark({ size = 40 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" role="img" aria-label="PRAHARI logo">
      <defs>
        <linearGradient id="prahari-g" x1="10" y1="4" x2="54" y2="60" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#3b6ff5" />
          <stop offset="1" stopColor="#1e3a8a" />
        </linearGradient>
      </defs>
      <path d="M32 3.5 L54.5 11.5 V30 C54.5 44.5 45 54.5 32 60.5 C19 54.5 9.5 44.5 9.5 30 V11.5 Z" fill="url(#prahari-g)" />
      <path d="M32 3.5 L54.5 11.5 V30 C54.5 44.5 45 54.5 32 60.5" fill="none" stroke="#ffffff" strokeOpacity="0.18" strokeWidth="1.5" />
      {/* eye */}
      <path d="M15.5 31.5 C21 22.5 43 22.5 48.5 31.5 C43 40.5 21 40.5 15.5 31.5 Z" fill="none" stroke="#ffffff" strokeWidth="2.6" strokeLinejoin="round" />
      {/* network pupil */}
      <g stroke="#ffb86b" strokeWidth="1.6" strokeLinecap="round">
        <line x1="32" y1="31.5" x2="32" y2="15" />
        <line x1="32" y1="31.5" x2="22" y2="46" />
        <line x1="32" y1="31.5" x2="42" y2="46" />
      </g>
      <circle cx="32" cy="15" r="2.4" fill="#ffb86b" />
      <circle cx="22" cy="46" r="2.4" fill="#ffb86b" />
      <circle cx="42" cy="46" r="2.4" fill="#ffb86b" />
      <circle cx="32" cy="31.5" r="6" fill="#ffffff" />
      <circle cx="32" cy="31.5" r="2.8" fill="#eb6834" />
    </svg>
  )
}

export function PrahariLogo({ size = 40, sub = true }: { size?: number; sub?: boolean }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 10 }}>
      <PrahariMark size={size} />
      <span style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.1 }}>
        <span style={{ fontWeight: 800, fontSize: size * 0.48, letterSpacing: '0.06em', color: 'var(--ink-1)' }}>
          PRAHARI
        </span>
        {sub && <span style={{ fontSize: 11.5, color: 'var(--ink-3)', fontWeight: 500 }}>प्रहरी · narrative watch</span>}
      </span>
    </span>
  )
}
