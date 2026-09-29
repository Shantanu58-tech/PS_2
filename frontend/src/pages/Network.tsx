import { useEffect, useMemo, useRef, useState } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ArrowDown, ArrowUp, Minus } from 'lucide-react'
import { useGraph, useInfluencers, useSpread } from '../hooks/useApi'
import { useAppStore } from '../store/app'
import { Card, ChartOrTable, ChartTip, Empty, InfoPop, Legend, PageHead, StatusBadge } from '../components/ui'
import { AXIS_TICK, cssVar } from '../lib/viz'
import { ist, istShort, num } from '../lib/fmt'

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

export default function Network() {
  const { organicOnly, theme } = useAppStore()
  const { data: g, isFetching } = useGraph(organicOnly)
  const { data: inf } = useInfluencers(organicOnly, 15)
  const { data: spread } = useSpread()
  const box = useRef<HTMLDivElement>(null)
  const width = useSize(box)
  const [hover, setHover] = useState<any>(null)

  const colors = useMemo(() => ({
    comm: COMMUNITY_TOKENS.map(cssVar), other: cssVar('--neutral-series'), ring: cssVar('--critical'),
    link: cssVar('--axis'), label: cssVar('--ink-2'), bg: cssVar('--surface-1'),
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }), [theme])

  const data = useMemo(() => {
    const nodes = (g?.nodes ?? []).map((n: any) => ({ ...n }))
    const sizes = new Map<number, number>()
    nodes.forEach((n: any) => sizes.set(n.community, (sizes.get(n.community) ?? 0) + 1))
    const top = [...sizes.entries()].sort((a, b) => b[1] - a[1]).slice(0, 3).map(e => e[0])
    nodes.forEach((n: any) => { n.slot = top.indexOf(n.community) })
    return { nodes, links: (g?.edges ?? []).map((e: any) => ({ ...e })), topCount: top.map(t => sizes.get(t) ?? 0) }
  }, [g])

  const maxPr = Math.max(0.0001, ...data.nodes.map((n: any) => n.pagerank))

  return (
    <div>
      <PageHead code="PS · E" title="Network & influence"
        sub={organicOnly ? 'Organic-only view: coordinated accounts removed and every metric recomputed.' : 'Account-to-account interaction graph (replies, reposts, forwards, mentions). Switch to Organic only to see who really influences.'} />
      <div className="grid g-main">
        <Card title="Interaction graph" sub={g ? `${num(data.nodes.length)} most-connected of ${num(g.total_nodes)} accounts · ${num(g.communities)} communities · store: ${g.store}` : ''}>
          <Legend items={[
            { label: `Community 1 (${data.topCount[0] ?? 0})`, color: 'var(--s1)' },
            { label: `Community 2 (${data.topCount[1] ?? 0})`, color: 'var(--s2)' },
            { label: `Community 3 (${data.topCount[2] ?? 0})`, color: 'var(--s3)' },
            { label: 'Other communities', color: 'var(--neutral-series)' },
            { label: 'Ring = flagged coordinated', color: 'var(--critical)' },
          ]} />
          <div ref={box} className={isFetching ? 'loading-hold' : ''} style={{ height: 460, marginTop: 8, borderRadius: 8, overflow: 'hidden', background: 'var(--surface-1)', position: 'relative' }}>
            {data.nodes.length === 0 ? <Empty>No interactions yet.</Empty> : (
              <ForceGraph2D
                width={width} height={460} graphData={data} backgroundColor={colors.bg}
                nodeId="id" cooldownTicks={120} d3VelocityDecay={0.35}
                linkColor={() => colors.link} linkWidth={(l: any) => Math.min(3, 0.5 + l.weight / 4)}
                linkDirectionalArrowLength={2.5} linkDirectionalArrowRelPos={1}
                nodeLabel={(n: any) => `${n.id} · PageRank ${n.pagerank.toFixed(4)}${n.coordinated ? ' · flagged coordinated' : ''}`}
                onNodeHover={(n: any) => setHover(n)}
                nodeCanvasObject={(n: any, ctx, scale) => {
                  const r = 3 + 12 * Math.sqrt(n.pagerank / maxPr)
                  ctx.beginPath(); ctx.arc(n.x, n.y, r, 0, 2 * Math.PI)
                  ctx.fillStyle = n.slot >= 0 ? colors.comm[n.slot] : colors.other; ctx.fill()
                  ctx.lineWidth = 2 / scale; ctx.strokeStyle = colors.bg; ctx.stroke()
                  if (n.coordinated) { ctx.beginPath(); ctx.arc(n.x, n.y, r + 2.5, 0, 2 * Math.PI); ctx.lineWidth = 2; ctx.strokeStyle = colors.ring; ctx.stroke() }
                  if (r > 9 && scale > 0.8) { ctx.font = `${11 / scale}px system-ui`; ctx.fillStyle = colors.label; ctx.fillText(n.id, n.x + r + 3, n.y + 3) }
                }}
                nodePointerAreaPaint={(n: any, color, ctx) => { ctx.fillStyle = color; ctx.beginPath(); ctx.arc(n.x, n.y, 12, 0, 2 * Math.PI); ctx.fill() }}
              />
            )}
            {hover && (
              <div className="chart-tip" style={{ position: 'absolute', top: 10, left: 10 }}>
                <div className="t mono">{hover.id}</div>
                <div className="r"><span>PageRank</span><span className="tnum">{hover.pagerank.toFixed(4)}</span></div>
                <div className="r"><span>Weighted degree</span><span className="tnum">{hover.degree}</span></div>
                <div className="r"><span>Coordination score</span><span className="tnum">{hover.coord_score.toFixed(2)}</span></div>
                <div className="r"><span>Behaviour likelihood</span><span className="tnum">{hover.behaviour_likelihood.toFixed(2)}</span></div>
              </div>
            )}
          </div>
        </Card>

        <div className="stack">
          <Card title="Key opinion leaders" sub={`ranked by influence · ${organicOnly ? 'organic-only' : 'raw'} view`}
            actions={<InfoPop>Influence = 0.5·cascade + 0.3·PageRank + 0.2·betweenness (each normalised). Cascade = accounts that replied to, reposted or forwarded this account, directly or indirectly. The arrow shows the rank change versus the other view.</InfoPop>}>
            <table className="tbl">
              <thead><tr><th>#</th><th>Account</th><th className="num">Cascade</th><th className="num">vs {organicOnly ? 'raw' : 'organic'}</th></tr></thead>
              <tbody>{(inf?.influencers ?? []).map((k: any) => (
                <tr key={k.account_id}>
                  <td className="tnum">{k.rank}</td>
                  <td className="mono" style={{ fontSize: 12 }}>{k.account_id}
                    <div className="row" style={{ gap: 4, marginTop: 2 }}>
                      <span className="chip">{k.role}</span>
                      {k.coordinated && <StatusBadge status="critical">coordinated</StatusBadge>}
                    </div>
                  </td>
                  <td className="num">{num(k.cascade_size)}</td>
                  <td className="num"><RankDelta rank={k.rank} other={k.rank_other_view} /></td>
                </tr>
              ))}</tbody>
            </table>
          </Card>
          <Card title="Bridge accounts" sub="connect otherwise separate communities">
            <table className="tbl"><tbody>{(inf?.bridges ?? []).slice(0, 6).map((b: any) => (
              <tr key={b.account_id}><td className="mono" style={{ fontSize: 12 }}>{b.account_id}</td><td className="num">{b.communities_touched} communities</td><td className="num">{b.betweenness.toFixed(4)}</td></tr>
            ))}</tbody></table>
          </Card>
        </div>
      </div>

      <Card title="Spread over time" sub="cumulative reach of the most coordinated topic" style={{ marginTop: 16 }}>
        {(spread?.frames ?? []).length === 0 ? <Empty>No spread data.</Empty> : (
          <ChartOrTable
            chart={<>
              <Legend items={[{ label: 'Posts (cumulative)', color: 'var(--s1)' }, { label: 'Accounts reached (cumulative)', color: 'var(--s2)' }]} />
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
            table={<table className="tbl"><thead><tr><th>Hour (IST)</th><th className="num">Posts</th><th className="num">Accounts</th><th>Platforms</th></tr></thead>
              <tbody>{spread.frames.map((f: any) => <tr key={f.hour}><td>{ist(f.hour)}</td><td className="num">{f.posts}</td><td className="num">{f.accounts}</td><td>{Object.entries(f.platforms).map(([p, n]) => `${p}: ${n}`).join(' · ')}</td></tr>)}</tbody></table>} />
        )}
      </Card>
    </div>
  )
}
