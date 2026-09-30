import { ReactNode, useEffect, useRef, useState } from 'react'
import { AlertTriangle, CheckCircle2, Info, ShieldAlert, BarChart3, Table2, Loader2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useHealth } from '../hooks/useApi'

export function PageHead({ title, sub, actions }: { title: string; sub?: ReactNode; actions?: ReactNode; code?: string }) {
  return (
    <div className="page-head">
      <div>
        <h1 className="page-title">{title}</h1>
        {sub && <p className="page-sub">{sub}</p>}
      </div>
      {actions && <div className="row-wrap">{actions}</div>}
    </div>
  )
}

export function Card({ title, sub, actions, children, pad = false, className = '', style }: {
  title?: ReactNode; sub?: ReactNode; actions?: ReactNode; children: ReactNode; pad?: boolean; className?: string; style?: React.CSSProperties
}) {
  return (
    <section className={`card ${className}`} style={style}>
      {(title || actions) && (
        <div className="card-head">
          <div>
            {title && <h2 className="card-title">{title}</h2>}
            {sub && <p className="card-sub">{sub}</p>}
          </div>
          {actions && <div className="row-wrap">{actions}</div>}
        </div>
      )}
      <div className={pad ? 'card-pad' : 'card-body'}>{children}</div>
    </section>
  )
}

export function Kpi({ label, value, foot, info, tone, icon }: { label: ReactNode; value: ReactNode; foot?: ReactNode; info?: ReactNode; tone?: 'good' | 'critical'; icon?: ReactNode }) {
  return (
    <div className="card kpi">
      {icon && <div className="kpi-icon" aria-hidden="true">{icon}</div>}
      <div style={{ minWidth: 0 }}>
        <div className="kpi-label">{label}{info && <InfoPop>{info}</InfoPop>}</div>
        <div className="kpi-value" style={tone ? { color: tone === 'good' ? 'var(--good-ink)' : 'var(--ink-1)' } : undefined}>{value}</div>
        {foot && <div className="kpi-foot">{foot}</div>}
      </div>
    </div>
  )
}

type Status = 'good' | 'warning' | 'serious' | 'critical'
const STATUS_ICON: Record<Status, ReactNode> = {
  good: <CheckCircle2 size={12} color="var(--good)" />,
  warning: <AlertTriangle size={12} color="var(--warning)" />,
  serious: <AlertTriangle size={12} color="var(--serious)" />,
  critical: <ShieldAlert size={12} color="var(--critical)" />,
}
/** Status colour never carries meaning alone: icon + label always travel with it. */
export function StatusBadge({ status, children, title }: { status: Status; children: ReactNode; title?: string }) {
  return <span className={`badge status-${status}`} title={title}>{STATUS_ICON[status]}{children}</span>
}

export function SeriesBadge({ color, children }: { color: string; children: ReactNode }) {
  return <span className="badge"><span className="dot" style={{ background: color }} />{children}</span>
}

/** "Why / formula" popover (PRD 13.4: every score has an info popover with formula, inputs, limits). */
export function InfoPop({ children, label = 'How this is computed' }: { children: ReactNode; label?: string }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLSpanElement>(null)
  useEffect(() => {
    if (!open) return
    const close = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false) }
    const esc = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('mousedown', close)
    document.addEventListener('keydown', esc)
    return () => { document.removeEventListener('mousedown', close); document.removeEventListener('keydown', esc) }
  }, [open])
  return (
    <span className="pop" ref={ref}>
      <button type="button" className="pop-btn" aria-label={label} aria-expanded={open} onClick={() => setOpen(!open)}><Info size={13} /></button>
      {open && <div className="pop-panel" role="dialog">{children}</div>}
    </span>
  )
}

export function Seg<T extends string>({ value, options, onChange, label }: {
  value: T; options: { value: T; label: ReactNode; icon?: ReactNode }[]; onChange: (v: T) => void; label: string
}) {
  return (
    <div className="seg" role="group" aria-label={label}>
      {options.map(o => (
        <button key={o.value} type="button" aria-pressed={o.value === value} onClick={() => onChange(o.value)}>{o.icon}{o.label}</button>
      ))}
    </div>
  )
}

/** Every chart has a table-view twin (dataviz accessibility rule). */
export function ChartOrTable({ chart, table, initial = 'chart' }: { chart: ReactNode; table: ReactNode; initial?: 'chart' | 'table' }) {
  const [view, setView] = useState<'chart' | 'table'>(initial)
  return (
    <div>
      <div className="spread" style={{ marginBottom: 8, justifyContent: 'flex-end' }}>
        <Seg<'chart' | 'table'> label="View" value={view} onChange={setView} options={[
          { value: 'chart', label: 'Chart', icon: <BarChart3 size={13} /> },
          { value: 'table', label: 'Table', icon: <Table2 size={13} /> },
        ]} />
      </div>
      {view === 'chart' ? chart : <div className="table-wrap" style={{ maxHeight: 360, overflowY: 'auto' }}>{table}</div>}
    </div>
  )
}

export function Legend({ items }: { items: { label: ReactNode; color: string }[] }) {
  return (
    <div className="legend" aria-label="Legend">
      {items.map((it, i) => <span key={i}><span className="sw" style={{ background: it.color }} />{it.label}</span>)}
    </div>
  )
}

/** Recharts tooltip body using text tokens (values never wear the series colour). */
export function ChartTip({ active, payload, label, fmtLabel, fmtValue }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tip">
      <div className="t">{fmtLabel ? fmtLabel(label) : label}</div>
      {payload.map((p: any) => (
        <div className="r" key={p.dataKey ?? p.name}>
          <span className="row"><span className="sw" style={{ width: 8, height: 8, borderRadius: 2, background: p.color || p.fill, display: 'inline-block' }} />{p.name}</span>
          <span className="tnum" style={{ color: 'var(--ink-1)' }}>{fmtValue ? fmtValue(p.value, p) : p.value}</span>
        </div>
      ))}
    </div>
  )
}

export function Meter({ value, color = 'var(--accent)', label }: { value: number; color?: string; label?: string }) {
  const v = Math.max(0, Math.min(1, value))
  return (
    <div className="meter" role="meter" aria-valuemin={0} aria-valuemax={1} aria-valuenow={v} aria-label={label}>
      <span style={{ width: `${v * 100}%`, background: color }} />
    </div>
  )
}

export function Loading({ label = 'Loading' }: { label?: string }) {
  return <div className="row muted" style={{ padding: 16 }}><Loader2 size={14} className="spin" style={{ animation: 'spin 1s linear infinite' }} />{label}…</div>
}

/** Empty states never dead-end: they point to the replay (or explain read-only mode). */
export function Empty({ children }: { children?: ReactNode }) {
  const { data: health } = useHealth()
  return (
    <div className="empty">
      {children ?? 'No data yet.'}
      {health && !health.demo_readonly && <div style={{ marginTop: 8 }}><Link to="/">Load data from the Overview →</Link></div>}
    </div>
  )
}

export function ErrorNote({ error }: { error: unknown }) {
  if (!error) return null
  return <div className="notice crit">Could not load: {String((error as Error).message || error)}</div>
}
