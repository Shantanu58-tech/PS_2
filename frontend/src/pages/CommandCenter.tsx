import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { AlertTriangle, ArrowRight, ChevronDown, ChevronRight, Database, FileText, Fingerprint, Play, TrendingUp } from 'lucide-react'
import { useAlerts, useClusters, useCreateCase, useHealth, useLedgerStatus, useTopics, useVolume, postJSON } from '../hooks/useApi'
import { ChartOrTable, ChartTip, Empty, ErrorNote, Kpi, Legend, Meter, PageHead, StatusBadge } from '../components/ui'
import { AXIS_TICK, ORGANIC, PLATFORM_LABEL, RAW } from '../lib/viz'
import { ist, istShort, num, pct } from '../lib/fmt'

const HIGH = 70

function priorityParts(ev: any) {
  const B = Math.min(1, (ev.burst_level ?? 0) / 5)
  const C = ev.coordinated_share ?? 0
  const S = Math.min(1, Math.abs(ev.anxiety_shift ?? 0) / 0.5)
  const R = ev.reach_percentile ?? 0
  return [
    { k: 'Burst level', w: 0.35, v: B, raw: `level ${ev.burst_level ?? 0} of 5` },
    { k: 'Coordinated share', w: 0.30, v: C, raw: pct(C) },
    { k: 'Anxiety shift', w: 0.20, v: S, raw: `${(ev.anxiety_shift ?? 0) >= 0 ? '+' : ''}${(ev.anxiety_shift ?? 0).toFixed(2)}` },
    { k: 'Reach percentile', w: 0.15, v: R, raw: pct(R) },
  ]
}

function SignalCard({ alert }: { alert: any }) {
  const [open, setOpen] = useState(false)
  const createCase = useCreateCase()
  const navigate = useNavigate()
  const ev = alert.evidence ?? {}
  const high = alert.priority >= HIGH
  const manufactured = ev.coordinated_share >= 0.3
  const parts = priorityParts(ev)
  return (
    <article className={`card signal ${high ? 'high' : alert.priority >= 50 ? 'mid' : ''}`} style={{ padding: '18px 20px 16px 24px' }}>
      <div className="spread">
        <div className="row-wrap">
          {manufactured
            ? <StatusBadge status="critical">Manufactured surge</StatusBadge>
            : <StatusBadge status="good">Organic burst</StatusBadge>}
          {high && <StatusBadge status="serious">High priority</StatusBadge>}
          <span className="muted" style={{ fontSize: 12.5 }}>{(ev.platforms ?? []).map((p: string) => PLATFORM_LABEL[p] ?? p).join(' · ')}</span>
        </div>
        <div className="row" title="Priority 0–100">
          <span className="muted" style={{ fontSize: 12 }}>Priority</span>
          <span style={{ fontSize: 22, fontWeight: 700 }}>{alert.priority.toFixed(0)}</span>
        </div>
      </div>
      <h3 style={{ fontSize: 16, fontWeight: 650, margin: '12px 0 4px', textTransform: 'capitalize' }}>{alert.topic_label ?? 'Topic'}</h3>
      <p className="secondary" style={{ margin: 0, fontSize: 13.5 }}>{(alert.headline ?? '').split(' - ').slice(1).join(' - ') || alert.headline}</p>
      <div className="muted" style={{ fontSize: 12.5, marginTop: 4 }}>{istShort(ev.start)} → {istShort(ev.end)}</div>
      <div style={{ marginTop: 10 }}>
        <Meter value={alert.priority / 100} color={high ? 'var(--critical)' : 'var(--serious)'} label="Priority" />
      </div>
      <div className="row-wrap" style={{ marginTop: 12 }}>
        <button className="btn btn-sm btn-ghost" aria-expanded={open} onClick={() => setOpen(!open)}>
          {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}Why it fired
        </button>
        <button className="btn btn-sm" disabled={createCase.isPending}
          onClick={() => createCase.mutate({ alert_id: alert.alert_id, title: (alert.topic_label ?? alert.headline).slice(0, 80) },
            { onSuccess: () => navigate('/cases') })}>
          <FileText size={14} />{createCase.isPending ? 'Assembling…' : 'Open case'}
        </button>
        {manufactured && <Link className="btn btn-sm btn-ghost" to="/coordination">Investigate<ArrowRight size={14} /></Link>}
      </div>
      {createCase.isError && <div className="notice crit" style={{ marginTop: 8 }}>{String(createCase.error)}</div>}
      {open && (
        <div style={{ marginTop: 12 }}>
          <div className="muted" style={{ fontSize: 12.5, marginBottom: 8 }}>Priority is built from four signals, each scaled 0–1:</div>
          <table className="tbl">
            <thead><tr><th>Signal</th><th>Value</th><th style={{ width: '36%' }}>Strength</th><th className="num">Points</th></tr></thead>
            <tbody>
              {parts.map(p => (
                <tr key={p.k}>
                  <td>{p.k}</td><td className="tnum">{p.raw}</td>
                  <td><Meter value={p.v} label={p.k} /></td>
                  <td className="num">{(100 * p.w * p.v).toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </article>
  )
}

export default function CommandCenter() {
  const { data: health } = useHealth()
  const { data: alertsData, error } = useAlerts()
  const { data: ledger } = useLedgerStatus()
  const { data: topicsData } = useTopics('rising', 8)
  const { data: allTopicsData } = useTopics('coordinated', 100)
  const { data: clustersData } = useClusters()
  const { data: vol } = useVolume('1h')
  const [replayMsg, setReplayMsg] = useState('')
  const readOnly = !!health?.demo_readonly
  const alerts: any[] = alertsData?.alerts ?? []
  const topics: any[] = topicsData?.topics ?? []
  const allTopics: any[] = allTopicsData?.topics ?? []
  const highCount = alerts.filter(a => a.priority >= HIGH).length
  const coordinated = (clustersData?.clusters ?? []).reduce((s: number, c: any) => s + (c.n_coordinated ?? 0), 0)

  const series = useMemo(() => {
    const byHour = new Map<string, { bucket: string; raw: number; organic: number }>()
    for (const r of vol?.buckets ?? []) {
      const e = byHour.get(r.bucket) ?? { bucket: r.bucket, raw: 0, organic: 0 }
      e.raw += r.n; e.organic += r.n - (r.coordinated ?? 0)
      byHour.set(r.bucket, e)
    }
    return [...byHour.values()]
  }, [vol])

  const startReplay = async () => {
    try {
      await postJSON('/api/replay/start', {})
      setReplayMsg('Loading data. The Live indicator in the top bar shows progress.')
    } catch (e) {
      setReplayMsg(String((e as Error).message))
    }
  }

  return (
    <div>
      <PageHead title="Overview"
        sub="What is trending right now, and which of it is being pushed by coordinated accounts."
        actions={!readOnly && <button className="btn btn-primary" onClick={startReplay}><Play size={14} />Load data</button>} />
      {replayMsg && <div className="notice" style={{ marginBottom: 16 }}>{replayMsg}</div>}
      <ErrorNote error={error} />

      <div className="grid g-4" style={{ marginBottom: 24 }} data-tour="kpis">
        <Kpi icon={<Database size={20} />} label="Posts secured" value={num(ledger?.record_count)} foot="tamper-evident"
          info={<>Every post is hash-chained before analysis, and each block of 100 is sealed with a signed Merkle root.</>} />
        <Kpi icon={<AlertTriangle size={20} />} label="Priority alerts" value={num(highCount)} foot={`of ${num(alerts.length)} signals`} />
        <Kpi icon={<Fingerprint size={20} />} label="Coordinated accounts" value={num(coordinated)} foot="acting in sync"
          info={<>Accounts that post near-identical content in lock-step inside one narrative. A signal for review, not an accusation.</>} />
        <Kpi icon={<TrendingUp size={20} />} label="Manufactured trends" value={num(allTopics.filter(t => t.nature === 'manufactured').length)} foot={`of ${num(allTopics.length)} topics`}
          info={<>A trend is manufactured when 30% or more of its posts come from coordinated accounts.</>} />
      </div>

      <div className="grid g-main">
        <div className="stack">
          <div className="spread">
            <h2 className="card-title" style={{ fontSize: 17 }}>Signals</h2>
            <span className="muted" style={{ fontSize: 12.5 }}>highest priority first</span>
          </div>
          {alerts.length === 0 ? <Empty>No signals yet.</Empty> : alerts.slice(0, 5).map(a => <SignalCard key={a.alert_id} alert={a} />)}
        </div>

        <div className="stack">
          <section className="card">
            <div className="card-head">
              <div>
                <h2 className="card-title">Activity</h2>
                <p className="card-sub">posts per hour · the gap is coordinated amplification</p>
              </div>
            </div>
            <div className="card-body">
              {series.length === 0 ? <Empty>No posts yet.</Empty> : (
                <ChartOrTable
                  chart={<>
                    <Legend items={[{ label: 'Organic', color: ORGANIC }, { label: 'All activity', color: RAW }]} />
                    <div style={{ height: 220, marginTop: 8 }}>
                      <ResponsiveContainer>
                        <AreaChart data={series} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                          <CartesianGrid stroke="var(--hairline)" vertical={false} />
                          <XAxis dataKey="bucket" tick={AXIS_TICK} tickFormatter={v => istShort(v)} minTickGap={70} axisLine={{ stroke: 'var(--axis)' }} tickLine={false} />
                          <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} width={48} />
                          <Tooltip content={<ChartTip fmtLabel={(l: string) => ist(l)} />} />
                          <Area type="monotone" dataKey="raw" name="Raw" stroke={RAW} fill={RAW} fillOpacity={0.18} strokeWidth={2} isAnimationActive={false} />
                          <Area type="monotone" dataKey="organic" name="Organic" stroke={ORGANIC} fill={ORGANIC} fillOpacity={0.22} strokeWidth={2} isAnimationActive={false} />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </>}
                  table={<table className="tbl"><thead><tr><th>Hour (IST)</th><th className="num">Raw</th><th className="num">Organic</th></tr></thead>
                    <tbody>{series.map(r => <tr key={r.bucket}><td>{ist(r.bucket)}</td><td className="num">{r.raw}</td><td className="num">{r.organic}</td></tr>)}</tbody></table>}
                />
              )}
            </div>
          </section>

          <section className="card">
            <div className="card-head">
              <div>
                <h2 className="card-title">Rising topics</h2>
                <p className="card-sub">fastest growing right now</p>
              </div>
              <Link to="/trends" className="btn btn-sm btn-ghost">All trends</Link>
            </div>
            <div className="card-body" style={{ paddingTop: 4 }}>
              {topics.length === 0 ? <Empty>No topics yet.</Empty> : (
                <table className="tbl">
                  <thead><tr><th>Topic</th><th /><th className="num">Posts</th></tr></thead>
                  <tbody>{topics.map(t => (
                    <tr key={t.topic_id}>
                      <td style={{ maxWidth: 200, textTransform: 'capitalize' }}>{t.label}</td>
                      <td>{t.nature === 'manufactured' ? <StatusBadge status="critical">Manufactured</StatusBadge> : <StatusBadge status="good">Organic</StatusBadge>}</td>
                      <td className="num">{num(t.n_posts)}</td>
                    </tr>
                  ))}</tbody>
                </table>
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
