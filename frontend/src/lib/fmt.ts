// Formatting helpers. Timestamps are UTC in the API and shown in IST (CLAUDE.md rule 7).
const IST = 'Asia/Kolkata'

export function ist(ts?: string | null, opts: Intl.DateTimeFormatOptions = { dateStyle: 'medium', timeStyle: 'short' }): string {
  if (!ts) return '—'
  const d = new Date(ts)
  if (Number.isNaN(d.getTime())) return ts
  return `${d.toLocaleString('en-IN', { timeZone: IST, ...opts })} IST`
}

export function istShort(ts?: string | null): string {
  if (!ts) return ''
  const d = new Date(ts)
  // always with the year, so dates never look undated or backdated
  return d.toLocaleString('en-IN', { timeZone: IST, day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false })
}

export function istDay(ts?: string | null): string {
  if (!ts) return ''
  return new Date(ts).toLocaleDateString('en-IN', { timeZone: IST, day: '2-digit', month: 'short', year: 'numeric' })
}

export const num = (v?: number | null, digits = 0) =>
  v === null || v === undefined || Number.isNaN(v) ? '—' : v.toLocaleString('en-IN', { maximumFractionDigits: digits, minimumFractionDigits: digits })

export const pct = (v?: number | null, digits = 0) =>
  v === null || v === undefined || Number.isNaN(v) ? '—' : `${(v * 100).toFixed(digits)}%`

export const minutesBetween = (a: string, b: string) => Math.round((new Date(b).getTime() - new Date(a).getTime()) / 60000)

export function titleCase(s: string) {
  return s.replace(/[_-]/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}
