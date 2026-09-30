import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import {
  AlertTriangle, ArrowRight, Check, ChevronDown, ChevronRight, CloudRain, Cpu, Database, Eye, FileText, Fingerprint,
  Flame, GitBranch, GraduationCap, HeartPulse, IndianRupee, Landmark, Network, Shapes, Shield, ShieldCheck, TrendingUp,
  Trophy, X, XCircle, Zap,
} from 'lucide-react'
import { useAlerts, useLineage, useReview, useSituation, useVolume } from '../hooks/useApi'
import { Card, ChartOrTable, ChartTip, Empty, InfoPop, Legend, Loading, Meter, NextStep, PageHead } from '../components/ui'
import IndiaMap, { canonState, rampCss, valueOf, type Metric } from '../components/IndiaMap'
import { AXIS_TICK, ORGANIC, PLATFORM_LABEL, PLATFORM_SLOT, RAW } from '../lib/viz'
import { LEVEL_LABEL } from '../lib/flow'
import { ist, istShort, minutesBetween, num, pct, titleCase } from '../lib/fmt'

const HIGH = 70
const SECTOR_ICON: Record<string, React.ReactNode> = {
  infra: <Zap size={15} />, disaster: <CloudRain size={15} />, economy: <IndianRupee size={15} />,
  education: <GraduationCap size={15} />, civic: <Landmark size={15} />, health: <HeartPulse size={15} />,
  defence: <Shield size={15} />, tech: <Cpu size={15} />, culture: <Trophy size={15} />, other: <Shapes size={15} />,
}
const LEVEL_ICON: Record<string, React.ReactNode> = {
  critical: <AlertTriangle size={11} />, elevated: <AlertTriangle size={11} />, watch: <Eye size={11} />,
  normal: <Check size={11} />, quiet: null,
}
function Level({ level }: { level: string }) {
  return <span className={`lvl ${level}`}>{LEVEL_ICON[level]}{LEVEL_LABEL[level] ?? level}</span>
}
const plats = (ps: string[]) => ps.map(p => PLATFORM_LABEL[p] ?? p).join(' · ')

/* ---------------- 1. situation report ---------------- */
function SitRep({ sit }: { sit: any }) {
  const navigate = useNavigate()
  const { data: lin } = useLineage()
  const r = sit.sitrep
  const lead = r.lead
  const hops: any[] = useMemo(() => {
    if (!lead) return []
    const t = (lin?.topics ?? []).find((x: any) => x.topic_id === lead.topic_id)
    return t?.platforms ?? []
  }, [lin, lead])
  return (
    <section className={`card sitrep ${r.level}`}>
      <div className="row" style={{ alignItems: 'flex-start', gap: 14 }}>
        <span className="sitrep-icon"><AlertTriangle size={20} /></span>
        <div style={{ minWidth: 0 }}>
          <div className="row-wrap">
            <h2>Situation report · India</h2>
            <Level level={r.level} />
            <span className="muted" style={{ fontSize: 12.5 }}>as of {ist(r.as_of)}</span>
          </div>
          <p>
            DEEPASTAMBHA is watching <b>{num(r.posts)} posts</b> across <b>{r.platforms} platforms</b>.{' '}
            {lead ? <>
              A coordinated campaign is pushing <span className="hl" style={{ textTransform: 'capitalize' }}>“{lead.label}”</span> in <b>{lead.sector}</b>:{' '}
              <b>{pct(lead.coordinated_share, 0)}</b> of its {num(lead.posts)} posts come from a group of <b>{lead.group_accounts} accounts acting in sync</b>.
              It started on <b>{PLATFORM_LABEL[lead.first_platform] ?? lead.first_platform}</b> and has reached <b>{lead.platforms.length} platforms</b>
              {lead.reactions ? <>; <b>{num(lead.reactions)} real users</b> reacted with <b>{pct(lead.reaction_anxiety, 0)} anxiety</b></> : null}
              {lead.states?.length ? <>, most in <b>{lead.states.map(titleCase).join(' and ')}</b></> : null}.
            </> : <>No coordinated campaign is active; activity looks organic.</>}
          </p>
          <div className="row-wrap" style={{ marginTop: 14 }}>
            {lead && <button className="btn btn-danger" onClick={() => navigate(`/coordination?topic=${lead.topic_id}`)}><Fingerprint size={15} />Investigate the group</button>}
            {lead && <button className="btn" onClick={() => navigate(`/lineage?topic=${lead.topic_id}`)}><GitBranch size={15} />Trace the origin</button>}
            {lead && <button className="btn" onClick={() => navigate(`/network`)}><Network size={15} />See the network</button>}
            <button className="btn" onClick={() => navigate('/cases')}><FileText size={15} />Evidence & cases</button>
          </div>
        </div>
      </div>
      {lead && (
        <div className="hop-strip">
          <div className="spread" style={{ marginBottom: 6 }}>
            <b style={{ fontSize: 12.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>How it travelled</b>
            <Link to={`/lineage?topic=${lead.topic_id}`} style={{ fontSize: 12 }}>Lineage →</Link>
          </div>
          {hops.length === 0 ? <Loading label="Tracing" /> : hops.map((h, i) => (
            <div key={h.platform} className="hop">
              <span className="d" style={{ background: PLATFORM_SLOT[h.platform] }} />
              <span><b>{PLATFORM_LABEL[h.platform]}</b> <span className="muted">· {num(h.n_posts)} posts</span></span>
              <span className="muted tnum" style={{ fontSize: 12 }}>{i === 0 ? `first · ${istShort(h.first_seen).slice(-5)}` : `+${minutesBetween(hops[0].first_seen, h.first_seen)} min`}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

/* ---------------- 2. KPI strip ---------------- */
function Kpis({ k }: { k: any }) {
  const navigate = useNavigate()
  return (
    <div className="grid g-4" style={{ marginTop: 18 }}>
      <button className="card kpi-card" onClick={() => navigate('/ledger')}>
        <div className="top">Posts secured<span className="ic"><Database size={16} /></span></div>
        <div className="val">{num(k.posts_secured)}</div>
        <div className="foot"><span style={{ color: 'var(--good-ink)', fontWeight: 600 }}><ShieldCheck size={13} style={{ verticalAlign: -2 }} /> tamper-evident</span><span className="mono">{num(k.checkpoints)} signed seals</span></div>
      </button>
      <button className="card kpi-card alert" onClick={() => document.getElementById('signals')?.scrollIntoView({ behavior: 'smooth' })}>
        <div className="top" style={{ color: 'var(--critical)' }}>Priority alerts<span className="ic"><AlertTriangle size={16} /></span></div>
        <div className="val" style={{ color: 'var(--critical)' }}>{k.priority_alerts}<small>of {k.signals} signals</small></div>
        <div className="foot"><span style={{ color: 'var(--critical)', textTransform: 'capitalize', fontWeight: 600 }}>{k.top_alert?.label ?? '—'}</span><span>{k.top_alert?.status === 'new' ? 'requires triage' : k.top_alert?.status}</span></div>
      </button>
      <button className="card kpi-card" onClick={() => navigate('/coordination')}>
        <div className="top">Coordinated accounts<span className="ic"><Fingerprint size={16} /></span></div>
        <div className="val">{num(k.coordinated_accounts)}</div>
        <div className="foot"><span>acting in sync</span>{k.sync_index != null && <span className="mono">sync {k.sync_index.toFixed(2)}</span>}</div>
      </button>
      <button className="card kpi-card" onClick={() => navigate('/trends?sort=coordinated')}>
        <div className="top">Manufactured trends<span className="ic"><TrendingUp size={16} /></span></div>
        <div className="val" style={{ color: k.manufactured_trends ? 'var(--accent-ink)' : undefined }}>{k.manufactured_trends}<small>of {k.topics} topics</small></div>
        <div className="foot"><span style={{ color: 'var(--accent-ink)', textTransform: 'capitalize', fontWeight: 600 }}>{k.top_manufactured ?? 'none'}</span><span>{k.platforms} platforms</span></div>
      </button>
    </div>
  )
}

/* ---------------- 3. states + narratives ---------------- */
function StateDrawer({ state, sit, onClose }: { state: any; sit: any; onClose: () => void }) {
  const navigate = useNavigate()
  const secName = (id: string) => sit.sector_names?.[id] ?? id
  return (
    <>
      <div className="drawer-back" onClick={onClose} />
      <aside className="drawer" role="dialog" aria-label={`${state.state} details`}>
        <div className="drawer-head">
          <div>
            <div className="page-stage" style={{ marginBottom: 2 }}>State view</div>
            <h2 style={{ margin: 0, fontSize: 20, textTransform: 'capitalize' }}>{state.state}</h2>
            <div className="muted" style={{ fontSize: 12.5 }}>aggregate of {num(state.accounts)} accounts · no individual profiles</div>
          </div>
          <button className="btn btn-ghost btn-sm" aria-label="Close" onClick={onClose}><X size={16} /></button>
        </div>
        <div className="drawer-body">
          <div className="kv">
            <div><div className="k">Posts</div><div className="v">{num(state.posts)}</div></div>
            <div><div className="k">Anxiety</div><div className="v">{pct(state.anxiety, 0)}</div></div>
            <div><div className="k">Exposed to pushed narratives</div><div className="v">{pct(state.manufactured_share, 1)}</div></div>
            <div><div className="k">Platforms</div><div className="v" style={{ fontSize: 13.5 }}>{plats(state.platforms)}</div></div>
          </div>
          <div>
            <h3>What people here talk about</h3>
            <table className="tbl" style={{ marginTop: 6 }}><tbody>{state.top_topics.map((t: any) => (
              <tr key={t.topic_id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/trends?topic=${t.topic_id}`)}>
                <td style={{ textTransform: 'capitalize' }}>{t.label}<div className="muted" style={{ fontSize: 11.5 }}>{secName(t.sector)}</div></td>
                <td>{t.nature === 'manufactured' && <span className="lvl critical">Pushed</span>}</td>
                <td className="num">{num(t.posts)}</td>
              </tr>
            ))}</tbody></table>
          </div>
          <div className="muted" style={{ fontSize: 12 }}>
            State comes only from the location people write on their public profile; states with fewer than {sit.k_anon} accounts are withheld.
          </div>
          <Link className="btn btn-primary" to="/audience">Open audience view<ArrowRight size={14} /></Link>
        </div>
      </aside>
    </>
  )
}

function StatesPanel({ sit }: { sit: any }) {
  const [metric, setMetric] = useState<Metric>('exposure')
  const [sel, setSel] = useState<string | null>(null)
  const states: any[] = sit.states
  const released = states.filter(s => s.released)
  const ranked = [...released].sort((a, b) => (valueOf(b, metric) ?? 0) - (valueOf(a, metric) ?? 0)).slice(0, 5)
  const selState = states.find(s => s.state === sel)
  const fmt = (v: number | null) => v == null ? '—' : metric === 'posts' ? num(v) : metric === 'exposure' ? pct(v, 1) : pct(v, 0)
  const labels: Record<Metric, string> = { exposure: 'Exposure to pushed narratives', anxiety: 'Average anxiety', posts: 'Posts' }
  return (
    <Card title="Impact by state" sub={`${released.length} states with enough accounts to report · click a state for detail`}
      actions={<select className="input" value={metric} onChange={e => setMetric(e.target.value as Metric)} aria-label="Map metric" style={{ padding: '6px 10px' }}>
        <option value="exposure">Pushed-narrative exposure</option><option value="anxiety">Anxiety</option><option value="posts">Posts</option>
      </select>}>
      <div className="grid" style={{ gridTemplateColumns: 'minmax(0, 1.5fr) minmax(0, 1fr)', alignItems: 'start' }}>
        <div>
          <IndiaMap states={states} metric={metric} selected={sel} onSelect={setSel} />
          <div className="ramp" style={{ marginTop: 10 }}>
            <span>low</span><span className="bar" style={{ background: rampCss(metric) }} /><span>high</span>
            <span style={{ marginLeft: 'auto' }}>dashed = no data / withheld</span>
          </div>
        </div>
        <div>
          <div className="muted" style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>Top states · {labels[metric]}</div>
          <table className="tbl"><tbody>{ranked.map((s, i) => (
            <tr key={s.state} style={{ cursor: 'pointer' }} onClick={() => setSel(s.state)}>
              <td className="muted tnum" style={{ width: 20 }}>{i + 1}</td>
              <td style={{ textTransform: 'capitalize', fontWeight: 600 }}>{canonState(s.state)}
                <div className="muted" style={{ fontSize: 11.5, fontWeight: 400 }}>{s.top_topic?.label}</div></td>
              <td className="num">{fmt(valueOf(s, metric))}</td>
            </tr>
          ))}</tbody></table>
        </div>
      </div>
      {selState && <StateDrawer state={selState} sit={sit} onClose={() => setSel(null)} />}
    </Card>
  )
}

function Narratives({ sit }: { sit: any }) {
  const navigate = useNavigate()
  const list: any[] = sit.narratives
  const secName = (id: string) => sit.sector_names?.[id] ?? id
  return (
    <Card title="Narratives being pushed" sub="and the coordinated groups and accounts pushing them"
      actions={<InfoPop>A narrative is listed when coordinated accounts post in it. The group is the coordinated cluster the detector found; amplifiers are its most active accounts. This is a behaviour signal for review, not an accusation.</InfoPop>}>
      {list.length === 0 ? <Empty>No coordinated narratives right now.</Empty> : (
        <div className="stack" style={{ gap: 10 }}>
          {list.slice(0, 3).map(n => (
            <div key={n.topic_id} className={`narr ${n.nature}`}>
              <div className="spread" style={{ alignItems: 'flex-start' }}>
                <div>
                  <div className="t">{n.label}</div>
                  <div className="muted" style={{ fontSize: 12 }}>{secName(n.sector)} · first seen {istShort(n.first_seen)}</div>
                </div>
                {n.nature === 'manufactured' ? <span className="lvl critical"><AlertTriangle size={11} />Manufactured</span> : <span className="lvl watch">Coordinated</span>}
              </div>
              <Meter value={n.coordinated_share} color="var(--critical)" label="Coordinated share" />
              <dl className="who">
                <dt>Pushed by</dt>
                <dd>{n.groups.length ? n.groups.map((g: any) => <span key={g.cluster_id}><b>{g.accounts} accounts</b> in sync (sync {g.sync.toFixed(2)}) · </span>) : null}
                  <b>{pct(n.coordinated_share, 0)}</b> of {num(n.posts)} posts</dd>
                <dt>Amplifiers</dt>
                <dd>{n.amplifiers.map((a: any) => (
                  <button key={a.account_id} className="acct" onClick={() => navigate(`/network?account=${encodeURIComponent(a.account_id)}`)} title="Open in the network">
                    <span className="dot" style={{ background: PLATFORM_SLOT[a.platform] }} />@{a.account_id}</button>
                ))}</dd>
                <dt>Platforms</dt><dd>{plats(n.platforms)}</dd>
                {n.states.length > 0 && <><dt>Reached</dt><dd style={{ textTransform: 'capitalize' }}>{n.states.join(', ')}{n.reactions ? ` · ${num(n.reactions)} reactions` : ''}</dd></>}
              </dl>
              <div className="row-wrap">
                <Link className="btn btn-sm btn-primary" to={`/coordination?topic=${n.topic_id}`}>Investigate<ArrowRight size={13} /></Link>
                <Link className="btn btn-sm" to={`/trends?topic=${n.topic_id}`}>Trend</Link>
                <Link className="btn btn-sm" to={`/lineage?topic=${n.topic_id}`}>Origin</Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}

/* ---------------- 4. sectors ---------------- */
function Sectors({ sit }: { sit: any }) {
  const navigate = useNavigate()
  return (
    <div className="sector-grid">
      {sit.sectors.filter((s: any) => s.id !== 'other').map((s: any) => (
        <button key={s.id} className={`sector ${s.level}`} onClick={() => navigate(`/trends?sector=${s.id}`)} aria-label={`${s.name}: ${LEVEL_LABEL[s.level]}`}>
          <div className="spread" style={{ alignItems: 'flex-start', gap: 6 }}>
            <span className="row nm" style={{ gap: 6 }}>{SECTOR_ICON[s.id]}{s.name}</span>
          </div>
          <Level level={s.level} />
          <div className="lead">{s.lead_topic ? s.lead_topic.label : 'No activity in this period'}</div>
          <div>
            <div className="spread" style={{ fontSize: 11.5, color: 'var(--ink-3)', marginBottom: 3 }}><span>Coordinated share</span><b style={{ color: s.coordinated_share > 0.1 ? 'var(--critical)' : 'var(--ink-2)' }}>{pct(s.coordinated_share, 0)}</b></div>
            <Meter value={s.coordinated_share} color={s.coordinated_share > 0.1 ? 'var(--critical)' : 'var(--good)'} label="Coordinated share" />
          </div>
          <div className="foot"><span>{num(s.posts)} posts · {s.topics} topics</span><span style={{ color: 'var(--accent-ink)', fontWeight: 700 }}>Deep dive →</span></div>
        </button>
      ))}
    </div>
  )
}

/* ---------------- 5. signals (analyst review) + hot topics + activity ---------------- */
function priorityParts(ev: any) {
  const B = Math.min(1, (ev.burst_level ?? 0) / 5), C = ev.coordinated_share ?? 0
  const S = Math.min(1, Math.abs(ev.anxiety_shift ?? 0) / 0.5), R = ev.reach_percentile ?? 0
  return [
    { k: 'Burst level', w: 0.35, v: B, raw: `level ${ev.burst_level ?? 0} of 5` },
    { k: 'Coordinated share', w: 0.30, v: C, raw: pct(C) },
    { k: 'Anxiety shift', w: 0.20, v: S, raw: `${(ev.anxiety_shift ?? 0) >= 0 ? '+' : ''}${(ev.anxiety_shift ?? 0).toFixed(2)}` },
    { k: 'Reach', w: 0.15, v: R, raw: pct(R) },
  ]
}
const STATUS_TEXT: Record<string, string> = { new: 'Awaiting review', acked: 'Seen', approved: 'Approved → case', cased: 'Case opened', watchlist: 'On watchlist', dismissed: 'Dismissed' }

function Signal({ a }: { a: any }) {
  const [open, setOpen] = useState(false)
  const review = useReview()
  const navigate = useNavigate()
  const ev = a.evidence ?? {}
  const high = a.priority >= HIGH
  const manufactured = (ev.coordinated_share ?? 0) >= 0.3
  const decide = (action: 'approve' | 'watchlist' | 'dismiss') =>
    review.mutate({ alertId: a.alert_id, action }, { onSuccess: (r: any) => { if (r.case?.case_id) navigate(`/cases?case=${r.case.case_id}`) } })
  return (
    <article className={`card signal ${high ? 'high' : a.priority >= 50 ? 'mid' : ''}`} style={{ padding: '14px 16px 12px 20px' }}>
      <div className="spread">
        <div className="row-wrap">
          {manufactured ? <span className="lvl critical"><AlertTriangle size={11} />Manufactured surge</span> : <span className="lvl normal"><Check size={11} />Organic burst</span>}
          {high && <span className="lvl elevated">High priority</span>}
          <span className="muted" style={{ fontSize: 12 }}>{plats(ev.platforms ?? [])}</span>
        </div>
        <span className="row"><span className="muted" style={{ fontSize: 12 }}>Priority</span><b style={{ fontSize: 22, color: high ? 'var(--critical)' : 'var(--ink-1)' }}>{a.priority.toFixed(0)}</b></span>
      </div>
      <div className="spread" style={{ marginTop: 8 }}>
        <Link to={`/trends?topic=${a.topic_id}`} style={{ fontSize: 15.5, fontWeight: 750, color: 'var(--ink-1)', textTransform: 'capitalize' }}>{a.topic_label ?? 'Topic'}</Link>
        <span className="review">{STATUS_TEXT[a.status] ?? a.status}</span>
      </div>
      <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>{num(ev.n_posts)} posts · {pct(ev.coordinated_share ?? 0, 0)} coordinated · {istShort(ev.start)} → {istShort(ev.end)}</div>
      <div className="row-wrap" style={{ marginTop: 10 }}>
        <button className="btn btn-sm btn-ghost" aria-expanded={open} onClick={() => setOpen(!open)}>{open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}Why it fired</button>
        <span style={{ marginLeft: 'auto' }} />
        <span className="muted" style={{ fontSize: 12 }}>Analyst review:</span>
        <button className="btn btn-sm btn-primary" disabled={review.isPending} onClick={() => decide('approve')} title="Approve and open an evidence case"><FileText size={13} />Approve → case</button>
        <button className="btn btn-sm" disabled={review.isPending} onClick={() => decide('watchlist')}><Eye size={13} />Watchlist</button>
        <button className="btn btn-sm btn-ghost" disabled={review.isPending} onClick={() => decide('dismiss')}><XCircle size={13} />Dismiss</button>
      </div>
      {open && (
        <table className="tbl" style={{ marginTop: 8 }}>
          <thead><tr><th>Signal</th><th>Value</th><th style={{ width: '36%' }}>Strength</th><th className="num">Points</th></tr></thead>
          <tbody>{priorityParts(ev).map(p => (
            <tr key={p.k}><td>{p.k}</td><td className="tnum">{p.raw}</td><td><Meter value={p.v} label={p.k} /></td><td className="num">{(100 * p.w * p.v).toFixed(1)}</td></tr>
          ))}</tbody>
        </table>
      )}
    </article>
  )
}

function HotTopics({ sit }: { sit: any }) {
  const navigate = useNavigate()
  const secName = (id: string) => sit.sector_names?.[id] ?? id
  return (
    <Card title={<span className="row" style={{ gap: 6 }}><Flame size={16} color="var(--critical)" />Hot topics</span>} sub="biggest bursts right now">
      {sit.hot_topics.slice(0, 6).map((h: any, i: number) => (
        <button key={h.topic_id} className="hot" onClick={() => navigate(`/trends?topic=${h.topic_id}`)}>
          <span className="rank">#{i + 1}</span>
          <span style={{ minWidth: 0 }}>
            <span className="t">{h.label}</span>
            <span className="muted" style={{ display: 'block', fontSize: 12 }}>{secName(h.sector)} · {num(h.posts)} posts · {plats(h.platforms)}</span>
          </span>
          <span style={{ textAlign: 'right' }}>
            <span className={`spike ${h.nature === 'manufactured' ? '' : 'org'}`}>{h.nature === 'manufactured' ? 'PUSHED' : 'ORGANIC'} · {h.spike.toFixed(0)}×</span>
            <span className="muted" style={{ display: 'block', fontSize: 11.5, marginTop: 3 }}>{pct(h.coordinated_share, 0)} coordinated</span>
          </span>
        </button>
      ))}
    </Card>
  )
}

function Activity() {
  const { data: vol } = useVolume('1h')
  const series = useMemo(() => {
    const m = new Map<string, any>()
    for (const r of vol?.buckets ?? []) {
      const e = m.get(r.bucket) ?? { bucket: r.bucket, raw: 0, organic: 0 }
      e.raw += r.n; e.organic += r.n - (r.coordinated ?? 0); m.set(r.bucket, e)
    }
    return [...m.values()]
  }, [vol])
  return (
    <Card title="Activity & amplification gap" sub="posts per hour · the gap between the lines is coordinated amplification">
      {series.length === 0 ? <Empty>No posts yet.</Empty> : (
        <ChartOrTable
          chart={<>
            <Legend items={[{ label: 'Organic', color: ORGANIC }, { label: 'All activity', color: RAW }]} />
            <div style={{ height: 190, marginTop: 8 }}>
              <ResponsiveContainer>
                <AreaChart data={series} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid stroke="var(--hairline)" vertical={false} />
                  <XAxis dataKey="bucket" tick={AXIS_TICK} tickFormatter={istShort} minTickGap={80} axisLine={{ stroke: 'var(--axis)' }} tickLine={false} />
                  <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} width={44} />
                  <Tooltip content={<ChartTip fmtLabel={(l: string) => ist(l)} />} />
                  <Area type="monotone" dataKey="raw" name="All activity" stroke={RAW} fill={RAW} fillOpacity={0.25} strokeWidth={2} isAnimationActive={false} />
                  <Area type="monotone" dataKey="organic" name="Organic" stroke={ORGANIC} fill={ORGANIC} fillOpacity={0.22} strokeWidth={2} isAnimationActive={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </>}
          table={<table className="tbl"><thead><tr><th>Hour</th><th className="num">All</th><th className="num">Organic</th></tr></thead>
            <tbody>{series.map(r => <tr key={r.bucket}><td>{ist(r.bucket)}</td><td className="num">{r.raw}</td><td className="num">{r.organic}</td></tr>)}</tbody></table>} />
      )}
    </Card>
  )
}

export default function SituationRoom() {
  const { data: sit, error } = useSituation()
  const { data: alertsData } = useAlerts()
  if (error) return <Empty>Could not load the situation picture.</Empty>
  if (!sit) return <Loading label="Building the national picture" />
  const alerts: any[] = alertsData?.alerts ?? []
  return (
    <div>
      <PageHead title="National Situation Room"
        sub="What is happening across India on social media right now: which narratives are being pushed, by whom, and where the impact is." />
      <SitRep sit={sit} />
      <Kpis k={sit.kpis} />

      <div className="section-head"><h2 className="section-title">Who is pushing what, and where</h2><span className="section-sub">narratives, coordinated groups and state-level impact</span></div>
      <div className="grid g-7-5" style={{ alignItems: 'start' }}>
        <StatesPanel sit={sit} />
        <Narratives sit={sit} />
      </div>

      <div className="section-head"><h2 className="section-title">Sector-wise national impact</h2><span className="section-sub">click a sector to see its topics</span></div>
      <Sectors sit={sit} />

      <div className="grid g-7-5" style={{ alignItems: 'start', marginTop: 8 }}>
        <div>
          <div className="section-head" id="signals"><h2 className="section-title">Signals for review</h2><span className="section-sub">approve to open a case, or keep on the watchlist</span></div>
          <div className="stack" style={{ gap: 12 }}>{alerts.slice(0, 4).map(a => <Signal key={a.alert_id} a={a} />)}</div>
        </div>
        <div>
          <div className="section-head"><h2 className="section-title">Trending now</h2></div>
          <div className="stack" style={{ gap: 16 }}>
            <HotTopics sit={sit} />
            <Activity />
          </div>
        </div>
      </div>
      <NextStep />
    </div>
  )
}
