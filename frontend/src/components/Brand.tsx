/**
 * PRAHARI mark: a sentinel's shield with a single watchful eye.
 * Flat, two-colour and legible down to 16px. An original project emblem.
 */
export function PrahariMark({ size = 36 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" role="img" aria-label="PRAHARI logo">
      <defs>
        <linearGradient id="prahari-g" x1="12" y1="5" x2="52" y2="59" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#3b6ff5" />
          <stop offset="1" stopColor="#1d4ed8" />
        </linearGradient>
      </defs>
      <path d="M32 5 L52 12 V29.5 C52 43.5 43.5 53.5 32 59 C20.5 53.5 12 43.5 12 29.5 V12 Z" fill="url(#prahari-g)" />
      <path d="M19 32 C24 24.5 40 24.5 45 32 C40 39.5 24 39.5 19 32 Z" fill="#ffffff" />
      <circle cx="32" cy="32" r="5.2" fill="#1d4ed8" />
    </svg>
  )
}

export function PrahariLogo({ size = 36, compact = false }: { size?: number; compact?: boolean }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 10 }}>
      <PrahariMark size={size} />
      {!compact && (
        <span style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.1 }}>
          <span style={{ fontWeight: 800, fontSize: 19, letterSpacing: '0.08em', color: 'var(--ink-1)' }}>PRAHARI</span>
          <span style={{ fontSize: 11.5, color: 'var(--ink-3)', fontWeight: 500 }}>प्रहरी · narrative watch</span>
        </span>
      )}
    </span>
  )
}
