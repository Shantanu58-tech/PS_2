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
      <PageHead title="Network"
        sub={organicOnly ? 'Showing organic accounts only: rankings recomputed without coordinated accounts.' : 'Who influences whom. Switch to Organic only to see who really drives the conversation.'} />
      <div className="grid g-main">
        <Card title="Interaction map" sub={g ? `${num(data.nodes.length)} most-connected accounts` : ''}>
          <Legend items={[
            { label: 'Group 1', color: 'var(--s1)' },
            { label: 'Group 2', color: 'var(--s2)' },
            { label: 'Group 3', color: 'var(--s3)' },
            { label: 'Other', color: 'var(--neutral-series)' },
            { label: 'Red ring: in sync', color: 'var(--critical)' },
          ]} />
          <div ref={box} className={isFetching ? 'loading-hold' : ''} style={{ height: 460, marginTop: 10, borderRadius: 12, overflow: 'hidden', background: 'var(--surface-1)', position: 'relative' }}>
            {data.nodes.length === 0 ? <Empty>No interactions yet.</Empty> : (
              <ForceGraph2D
                width={width} height={460} graphData={data} backgroundColor={colors.bg}
                nodeId="id" cooldownTicks={120} d3VelocityDecay={0.35}
                linkColor={() => colors.link} linkWidth={(l: any) => Math.min(3, 0.5 + l.weight / 4)}
                linkDirectionalArrowLength={2.5} linkDirectionalArrowRelPos={1}
                nodeLabel={(n: any) => `@${n.id}${n.coordinated ? ' · in sync' : ''}`}
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
                <div className="t">@{hover.id}</div>
                <div className="r"><span>Interactions</span><span className="tnum">{hover.degree}</span></div>
                <div className="r"><span>Coordination</span><span className="tnum">{Math.round(hover.coord_score * 100)}%</span></div>
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
                  <td>@{k.account_id}
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
              <tr key={b.account_id}><td>@{b.account_id}</td><td className="num muted">{b.communities_touched} groups</td></tr>
            ))}</tbody></table>
          </Card>
        </div>
      </div>

      <Card title="How it spread" sub="cumulative reach of the most-pushed narrative" style={{ marginTop: 20 }}>
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
    </div>
  )
}
