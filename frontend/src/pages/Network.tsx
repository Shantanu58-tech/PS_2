import { useEffect, useMemo, useRef, useState } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ArrowDown, ArrowRight, ArrowUp, Minus, Pause, Play, X } from 'lucide-react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useGraph, useInfluencers, useNode, useSegmentSpread, useSpread } from '../hooks/useApi'
import { useAppStore } from '../store/app'
import { Card, ChartOrTable, ChartTip, Empty, InfoPop, Legend, NextStep, PageHead, Seg, StatusBadge } from '../components/ui'
import { AXIS_TICK, PLATFORMS, PLATFORM_LABEL, PLATFORM_SLOT, cssVar } from '../lib/viz'
import { ist, istShort, num, pct } from '../lib/fmt'

// Only the first three categorical slots are distinguishable all-pairs (dataviz palette note);
// smaller communities fold into a neutral "other".
const COMMUNITY_TOKENS = ['--s1', '--s2', '--s3']

function useSize(ref: React.RefObject<HTMLDivElement>) {
  const [w, setW] = useState(600)
  useEffect(() => {
    if (!ref.current) return
    const ro = new ResizeObserver(e => setW(Math.floor(e[0].contentRect.width)))
    ro.observe(ref.current)
    return () => ro.disconnect()
  }, [ref])
  return w
}

function RankDelta({ rank, other }: { rank: number; other?: number | null }) {
  if (!other) return <span className="muted" title="Not ranked in the other view">new</span>
  const d = other - rank
  if (d === 0) return <span className="muted"><Minus size={12} /></span>
  return <span className="row tnum" style={{ gap: 2 }} title={`Rank ${other} in the other view`}>{d > 0 ? <ArrowUp size={12} /> : <ArrowDown size={12} />}{Math.abs(d)}</span>
}

const SEG_SLOT: Record<string, string> = { s0: 'var(--critical)', s1: 'var(--s1)', s2: 'var(--s2)', s3: 'var(--s3)', s4: 'var(--s4)', other: 'var(--neutral-series)' }

/** How one narrative hops between audience segments over time, and how anxious each segment gets. */
function SegmentSpread() {
  const { data } = useSegmentSpread()
  const frames: any[] = data?.frames ?? []
  const summary: any[] = data?.summary ?? []
  if (!frames.length) return null
  const max = Math.max(1, ...frames.flatMap(f => summary.map(s => f[s.key] ?? 0)))
  const t0 = new Date(frames[0].hour).getTime()
  const t1 = new Date(frames[frames.length - 1].hour).getTime()
  const x = (h: string) => 3 + 90 * ((new Date(h).getTime() - t0) / Math.max(1, t1 - t0))
  return (
    <Card title="How it spread between groups" style={{ marginTop: 20 }}
      sub={`the most-pushed narrative, ${data.bucket === '10m' ? '10-minute' : 'hourly'} steps · bubble size = posts`}
      actions={<InfoPop>Groups are communities found in the interaction network; the coordinated group is kept separate. Reading down the list shows the order in which each group was reached.</InfoPop>}>
      <ChartOrTable
        chart={
          <div className="stack" style={{ gap: 4 }}>
            {summary.map(s => (
              <div key={s.key} className="lane" style={{ gridTemplateColumns: '230px 1fr 110px' }}>
                <span className="row" style={{ fontSize: 13 }}>
                  <span style={{ width: 10, height: 10, borderRadius: 3, background: SEG_SLOT[s.key], flexShrink: 0 }} />{s.label}
                </span>
                <div className="lane-track">
                  {frames.filter(f => f[s.key]).map(f => {
                    const r = 5 + 13 * Math.sqrt((f[s.key] ?? 0) / max)
                    return <span key={f.hour} title={`${ist(f.hour)} · ${f[s.key]} posts`} className="lane-dot"
                      style={{ left: `${x(f.hour)}%`, width: r * 2, height: r * 2, background: SEG_SLOT[s.key], opacity: 0.85 }} />
                  })}
                </div>
                <span className="muted" style={{ fontSize: 12.5, textAlign: 'right' }}>anxiety {s.anxiety != null ? pct(s.anxiety, 0) : '—'}</span>
              </div>
            ))}
            <div className="spread muted" style={{ fontSize: 12, paddingLeft: 242, paddingRight: 122 }}>
              <span>{istShort(frames[0].hour)}</span><span>{istShort(frames[frames.length - 1].hour)}</span>
            </div>
          </div>}
        table={<table className="tbl"><thead><tr><th>Group</th><th>First reached</th><th className="num">Posts</th><th className="num">Anxiety</th></tr></thead>
          <tbody>{summary.map(s => <tr key={s.key}><td>{s.label}</td><td>{ist(s.first_seen)}</td><td className="num">{num(s.posts)}</td><td className="num">{s.anxiety != null ? pct(s.anxiety, 0) : '—'}</td></tr>)}</tbody></table>} />
    </Card>
  )
}

function NodeDrawer({ id, onClose }: { id: string; onClose: () => void }) {
  const { data: d, isLoading } = useNode(id)
  const navigate = useNavigate()
  const prof = d?.profile
  return (
    <>
      <div className="drawer-back" onClick={onClose} />
      <aside className="drawer" role="dialog" aria-label={`Account ${id}`}>
        <div className="drawer-head">
          <div>
            <div className="page-stage" style={{ marginBottom: 2 }}>Account in the network</div>
            <h2 style={{ margin: 0, fontSize: 19 }}>@{prof?.handle ?? id}</h2>
            <div className="muted" style={{ fontSize: 12.5 }}>{prof?.display_name ?? id}{prof?.platform ? ` · ${PLATFORM_LABEL[prof.platform] ?? prof.platform}` : ''}</div>
          </div>
          <button className="btn btn-ghost btn-sm" aria-label="Close" onClick={onClose}><X size={16} /></button>
        </div>
        <div className="drawer-body">
          {isLoading || !d ? <div className="muted">Loading…</div> : <>
            {d.coord_score != null && d.coord_score >= 0.7 && <span className="lvl critical" style={{ alignSelf: 'flex-start' }}>Acting in sync · {pct(d.coord_score, 0)}</span>}
            <div className="kv">
              <div><div className="k">Followers</div><div className="v">{prof?.followers != null ? num(prof.followers) : '—'}</div></div>
              <div><div className="k">Following</div><div className="v">{prof?.following != null ? num(prof.following) : '—'}</div></div>
              <div><div className="k">Engaged by</div><div className="v">{num(d.engaged_by)} accounts</div></div>
              <div><div className="k">Engages with</div><div className="v">{num(d.engages_with)} accounts</div></div>
            </div>
            {!prof && <div className="muted" style={{ fontSize: 12 }}>No public profile in the source (e.g. official-export data), so follower counts are not available.</div>}
            <div>
              <h3>Activity by platform</h3>
              <table className="tbl" style={{ marginTop: 6 }}>
                <thead><tr><th>Platform</th><th className="num">Posts</th><th className="num">Comments</th><th>Active</th></tr></thead>
                <tbody>{d.platforms.map((r: any) => (
                  <tr key={r.platform}><td><span className="row"><span style={{ width: 9, height: 9, borderRadius: 3, background: PLATFORM_SLOT[r.platform] }} />{PLATFORM_LABEL[r.platform] ?? r.platform}</span></td>
                    <td className="num">{num(r.n)}</td><td className="num">{num(r.comments)}</td><td className="muted" style={{ fontSize: 12 }}>{istShort(r.first)} → {istShort(r.last)}</td></tr>
                ))}</tbody>
              </table>
            </div>
            {d.topics.length > 0 && <div>
              <h3>Talks about</h3>
              <div className="row-wrap" style={{ marginTop: 6 }}>{d.topics.map((t: any) => (
                <Link key={t.topic_id} className="acct" to={`/trends?topic=${t.topic_id}`} style={{ textTransform: 'capitalize' }}>
                  {t.nature === 'manufactured' && <span className="dot" style={{ background: 'var(--critical)' }} />}{t.label} · {t.n}</Link>
              ))}</div>
            </div>}
            <div>
              <h3>Connected followers (who engages with this account)</h3>
              {d.followers_interacting.length === 0 ? <div className="muted" style={{ fontSize: 12.5, marginTop: 4 }}>None recorded.</div> : (
                <table className="tbl" style={{ marginTop: 6 }}><tbody>{d.followers_interacting.map((r: any, i: number) => (
                  <tr key={i} style={{ cursor: 'pointer' }} onClick={() => navigate(`/network?account=${encodeURIComponent(r.account)}`)}>
                    <td><span className="row"><span style={{ width: 8, height: 8, borderRadius: 2, background: PLATFORM_SLOT[r.platform] }} />@{r.account}</span></td>
                    <td className="muted">{r.kind}</td><td className="num">{r.n}×</td></tr>
                ))}</tbody></table>)}
            </div>
            {d.interacts_with.length > 0 && <div>
              <h3>Engages with</h3>
              <table className="tbl" style={{ marginTop: 6 }}><tbody>{d.interacts_with.map((r: any, i: number) => (
                <tr key={i} style={{ cursor: 'pointer' }} onClick={() => navigate(`/network?account=${encodeURIComponent(r.account)}`)}>
                  <td><span className="row"><span style={{ width: 8, height: 8, borderRadius: 2, background: PLATFORM_SLOT[r.platform] }} />@{r.account}</span></td>
                  <td className="muted">{r.kind}</td><td className="num">{r.n}×</td></tr>
              ))}</tbody></table>
            </div>}
            {d.segment && <div className="muted" style={{ fontSize: 12.5 }}>Audience segment: <b>{d.segment}</b></div>}
            {d.coord_score != null && d.coord_score >= 0.7 && <Link className="btn btn-primary" to="/coordination">Open in Coordination<ArrowRight size={14} /></Link>}
          </>}
        </div>
      </aside>
    </>
  )
}

export default function Network() {
  const { organicOnly, theme } = useAppStore()
  const { data: g, isFetching } = useGraph(organicOnly, 300)
  const { data: inf } = useInfluencers(organicOnly, 15)
  const { data: spread } = useSpread()
  const [params, setParams] = useSearchParams()
  const selected = params.get('account')
  const openNode = (id: string | null) => { const p = new URLSearchParams(params); if (id) p.set('account', id); else p.delete('account'); setParams(p) }
  const box = useRef<HTMLDivElement>(null)
  const width = useSize(box)
  const [hover, setHover] = useState<any>(null)
  const [colorBy, setColorBy] = useState<'platform' | 'community'>('platform')
  const [hidden, setHidden] = useState<Set<string>>(new Set())
  const [cursor, setCursor] = useState<number | null>(null)  // time-lapse position (ms); null = everything
  const [playing, setPlaying] = useState(false)

  const colors = useMemo(() => ({
    comm: COMMUNITY_TOKENS.map(cssVar), other: cssVar('--neutral-series'), ring: cssVar('--critical'),
    link: cssVar('--axis'), label: cssVar('--ink-2'), bg: cssVar('--surface-1'),
    plat: Object.fromEntries(PLATFORMS.map(p => [p, cssVar(PLATFORM_SLOT[p].slice(4, -1))])) as Record<string, string>,
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }), [theme])

  // stable node/link objects so the layout keeps its positions while filtering or playing
  const base = useMemo(() => {
    const nodes = (g?.nodes ?? []).map((n: any) => ({ ...n }))
    const sizes = new Map<number, number>()
    nodes.forEach((n: any) => sizes.set(n.community, (sizes.get(n.community) ?? 0) + 1))
    const top = [...sizes.entries()].sort((a, b) => b[1] - a[1]).slice(0, 3).map(e => e[0])
    nodes.forEach((n: any) => { n.slot = top.indexOf(n.community) })
    const links = (g?.edges ?? []).map((e: any) => ({ ...e, t: e.ts ? new Date(e.ts).getTime() : 0 }))
    const ts = links.map((l: any) => l.t).filter(Boolean)
    return { nodes, links, t0: ts.length ? Math.min(...ts) : 0, t1: ts.length ? Math.max(...ts) : 0 }
  }, [g])

  const data = useMemo(() => {
    const id = (x: any) => (typeof x === 'object' ? x.id : x)
    const byId = new Map(base.nodes.map((n: any) => [n.id, n]))
    const links = base.links.filter((l: any) => {
      if (cursor != null && l.t > cursor) return false
      const s: any = byId.get(id(l.source)), t: any = byId.get(id(l.target))
      return s && t && !hidden.has(s.platform) && !hidden.has(t.platform)
    })
    const keep = new Set<string>()
    links.forEach((l: any) => { keep.add(id(l.source)); keep.add(id(l.target)) })
    const nodes = base.nodes.filter((n: any) => !hidden.has(n.platform) && (cursor == null ? true : keep.has(n.id)))
    return { nodes, links }
  }, [base, cursor, hidden])

  useEffect(() => {
    if (!playing) return
    const step = (base.t1 - base.t0) / 160
    const iv = setInterval(() => setCursor(c => {
      const next = (c ?? base.t0) + step
      if (next >= base.t1) { setPlaying(false); return null }
      return next
    }), 90)
    return () => clearInterval(iv)
  }, [playing, base.t0, base.t1])

  const present = PLATFORMS.filter(p => base.nodes.some((n: any) => n.platform === p))
  const maxPr = Math.max(0.0001, ...base.nodes.map((n: any) => n.pagerank))
  const fill = (n: any) => colorBy === 'platform' ? (colors.plat[n.platform] ?? colors.other) : (n.slot >= 0 ? colors.comm[n.slot] : colors.other)
  const toggle = (p: string) => setHidden(h => { const x = new Set(h); if (x.has(p)) x.delete(p); else x.add(p); return x })

  return (
    <div>
      <PageHead title="Network"
        sub={organicOnly ? 'Showing organic accounts only: rankings recomputed without coordinated accounts.' : 'Who influences whom across every app. Click any account for its followers, connections and activity.'} />
      <div className="grid g-main">
        <Card title="Interaction map" sub={g ? `${num(data.nodes.length)} of the ${num(base.nodes.length)} most-connected accounts · ${num(data.links.length)} interactions` : ''}
          actions={<Seg<'platform' | 'community'> label="Colour by" value={colorBy} onChange={setColorBy}
            options={[{ value: 'platform', label: 'By platform' }, { value: 'community', label: 'By group' }]} />}>
          <div className="row-wrap" style={{ marginBottom: 8 }}>
            {colorBy === 'platform' ? present.map(p => (
              <button key={p} className="acct" onClick={() => toggle(p)} aria-pressed={!hidden.has(p)} title={hidden.has(p) ? 'Show' : 'Hide'}
                style={{ opacity: hidden.has(p) ? 0.45 : 1, textDecoration: hidden.has(p) ? 'line-through' : 'none' }}>
                <span className="dot" style={{ background: PLATFORM_SLOT[p] }} />{PLATFORM_LABEL[p]}</button>
            )) : <Legend items={[{ label: 'Group 1', color: 'var(--s1)' }, { label: 'Group 2', color: 'var(--s2)' }, { label: 'Group 3', color: 'var(--s3)' }, { label: 'Other', color: 'var(--neutral-series)' }]} />}
            <span className="legend"><span><span className="sw" style={{ background: 'var(--critical)', borderRadius: '50%' }} />Red ring: in sync</span></span>
          </div>
          <div className="row" style={{ marginBottom: 8, gap: 10 }}>
            <button className="btn btn-sm btn-primary" onClick={() => { if (!playing && cursor == null) setCursor(base.t0); setPlaying(!playing) }} disabled={!base.t1}>
              {playing ? <Pause size={13} /> : <Play size={13} />}{playing ? 'Pause' : 'Play the week'}</button>
            <input type="range" min={base.t0} max={base.t1} value={cursor ?? base.t1} aria-label="Time"
              onChange={e => { setPlaying(false); const v = Number(e.target.value); setCursor(v >= base.t1 ? null : v) }} style={{ flex: 1, accentColor: 'var(--accent)' }} />
            <span className="muted tnum" style={{ fontSize: 12, minWidth: 110, textAlign: 'right' }}>{cursor == null ? 'whole week' : istShort(new Date(cursor).toISOString())}</span>
          </div>
          <div ref={box} className={isFetching ? 'loading-hold' : ''} style={{ height: 470, borderRadius: 8, overflow: 'hidden', background: 'var(--surface-1)', position: 'relative', border: '1px solid var(--hairline)' }}>
            {base.nodes.length === 0 ? <Empty>No interactions yet.</Empty> : (
              <ForceGraph2D
                width={width} height={470} graphData={data} backgroundColor={colors.bg}
                nodeId="id" cooldownTicks={120} d3VelocityDecay={0.35}
                linkColor={() => colors.link} linkWidth={(l: any) => Math.min(3, 0.5 + l.weight / 4)}
                linkDirectionalArrowLength={2.5} linkDirectionalArrowRelPos={1}
                linkDirectionalParticles={(l: any) => (playing && cursor != null && cursor - l.t < (base.t1 - base.t0) / 40 ? 2 : 0)}
                linkDirectionalParticleWidth={2.5} linkDirectionalParticleColor={() => colors.ring}
                nodeLabel={(n: any) => `@${n.id} · ${PLATFORM_LABEL[n.platform] ?? n.platform}${n.followers != null ? ` · ${num(n.followers)} followers` : ''}${n.coordinated ? ' · in sync' : ''}`}
                onNodeHover={(n: any) => setHover(n)}
                onNodeClick={(n: any) => openNode(n.id)}
                nodeCanvasObject={(n: any, ctx, scale) => {
                  const r = 3 + 12 * Math.sqrt(n.pagerank / maxPr)
                  ctx.beginPath(); ctx.arc(n.x, n.y, r, 0, 2 * Math.PI)
                  ctx.fillStyle = fill(n); ctx.fill()
                  ctx.lineWidth = 2 / scale; ctx.strokeStyle = colors.bg; ctx.stroke()
                  if (n.coordinated) { ctx.beginPath(); ctx.arc(n.x, n.y, r + 2.5, 0, 2 * Math.PI); ctx.lineWidth = 2; ctx.strokeStyle = colors.ring; ctx.stroke() }
                  if (n.id === selected) { ctx.beginPath(); ctx.arc(n.x, n.y, r + 5, 0, 2 * Math.PI); ctx.lineWidth = 2.5; ctx.strokeStyle = colors.label; ctx.stroke() }
                  if (r > 9 && scale > 0.8) { ctx.font = `${11 / scale}px system-ui`; ctx.fillStyle = colors.label; ctx.fillText(n.id, n.x + r + 3, n.y + 3) }
                }}
                nodePointerAreaPaint={(n: any, color, ctx) => { ctx.fillStyle = color; ctx.beginPath(); ctx.arc(n.x, n.y, 12, 0, 2 * Math.PI); ctx.fill() }}
              />
            )}
            {hover && (
              <div className="chart-tip" style={{ position: 'absolute', top: 10, left: 10 }}>
                <div className="t">@{hover.id}</div>
                <div className="r"><span>Platform</span><span>{PLATFORM_LABEL[hover.platform] ?? hover.platform}</span></div>
                <div className="r"><span>Followers</span><span className="tnum">{hover.followers != null ? num(hover.followers) : '—'}</span></div>
                <div className="r"><span>Interactions</span><span className="tnum">{hover.degree}</span></div>
                <div className="r"><span>Coordination</span><span className="tnum">{Math.round(hover.coord_score * 100)}%</span></div>
                <div className="muted" style={{ marginTop: 4 }}>click for details</div>
              </div>
            )}
          </div>
        </Card>

        <div className="stack">
          <Card title="Top influencers" sub={organicOnly ? 'organic accounts only' : 'all activity'}
            actions={<InfoPop>Influence combines how far an account's posts travel (replies, reposts and forwards, direct or indirect) with its position in the network. The arrow shows how its rank changes when you flip the All activity / Organic only switch.</InfoPop>}>
            <table className="tbl">
              <thead><tr><th>#</th><th>Account</th><th className="num">Reach</th><th className="num">Change</th></tr></thead>
              <tbody>{(inf?.influencers ?? []).map((k: any) => (
                <tr key={k.account_id}>
                  <td className="tnum">{k.rank}</td>
                  <td style={{ cursor: 'pointer' }} onClick={() => openNode(k.account_id)}>@{k.account_id}
                    {k.coordinated && <div style={{ marginTop: 3 }}><StatusBadge status="critical">In sync</StatusBadge></div>}
                  </td>
                  <td className="num">{num(k.cascade_size)}</td>
                  <td className="num"><RankDelta rank={k.rank} other={k.rank_other_view} /></td>
                </tr>
              ))}</tbody>
            </table>
          </Card>
          <Card title="Bridges" sub="accounts linking otherwise separate groups">
            <table className="tbl"><tbody>{(inf?.bridges ?? []).slice(0, 5).map((b: any) => (
              <tr key={b.account_id} style={{ cursor: 'pointer' }} onClick={() => openNode(b.account_id)}><td>@{b.account_id}</td><td className="num muted">{b.communities_touched} groups</td></tr>
            ))}</tbody></table>
          </Card>
        </div>
      </div>

      <SegmentSpread />

      <Card title="Reach over time" sub="cumulative reach of the most-pushed narrative" style={{ marginTop: 20 }}>
        {(spread?.frames ?? []).length === 0 ? <Empty>No spread data.</Empty> : (
          <ChartOrTable
            chart={<>
              <Legend items={[{ label: 'Posts', color: 'var(--s1)' }, { label: 'Accounts reached', color: 'var(--s2)' }]} />
              <div style={{ height: 220, marginTop: 8 }}>
                <ResponsiveContainer>
                  <LineChart data={spread.frames} margin={{ top: 6, right: 8, left: -16, bottom: 0 }}>
                    <CartesianGrid stroke="var(--hairline)" vertical={false} />
                    <XAxis dataKey="hour" tick={AXIS_TICK} tickFormatter={v => istShort(v)} minTickGap={70} axisLine={{ stroke: 'var(--axis)' }} tickLine={false} />
                    <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} width={44} />
                    <Tooltip content={<ChartTip fmtLabel={(l: string) => ist(l)} />} />
                    <Line type="stepAfter" dataKey="posts" name="Posts" stroke="var(--s1)" strokeWidth={2} dot={false} isAnimationActive={false} />
                    <Line type="stepAfter" dataKey="accounts" name="Accounts" stroke="var(--s2)" strokeWidth={2} dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </>}
            table={<table className="tbl"><thead><tr><th>Hour</th><th className="num">Posts</th><th className="num">Accounts</th><th>Platforms</th></tr></thead>
              <tbody>{spread.frames.map((f: any) => <tr key={f.hour}><td>{ist(f.hour)}</td><td className="num">{f.posts}</td><td className="num">{f.accounts}</td><td>{Object.entries(f.platforms).map(([p, n]) => `${p}: ${n}`).join(' · ')}</td></tr>)}</tbody></table>} />
        )}
      </Card>
      <NextStep />
      {selected && <NodeDrawer id={selected} onClose={() => openNode(null)} />}
    </div>
  )
}
