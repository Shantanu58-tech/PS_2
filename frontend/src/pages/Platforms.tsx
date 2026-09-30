import { useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Database, FileUp, MessageSquare, MessagesSquare, Repeat2, Users } from 'lucide-react'
import { usePlatform, usePlatforms, useVolume } from '../hooks/useApi'
import LiveTelegram from '../components/LiveTelegram'
import { Card, ChartOrTable, ChartTip, Empty, InfoPop, Kpi, Legend, NextStep, PageHead, StatusBadge } from '../components/ui'
import { AXIS_TICK, EMOTIONS, EMOTION_LABEL, EMOTION_SLOT, ORGANIC, PLATFORMS, PLATFORM_LABEL, PLATFORM_SLOT, RAW } from '../lib/viz'
import { ist, istDay, istShort, num, pct } from '../lib/fmt'

const CONNECTION: Record<string, { live: boolean; label: string; help: string }> = {
  connected: { live: true, label: 'Connected', help: 'Signed in with a live session; new posts are collected automatically.' },
  ready: { live: true, label: 'API ready', help: 'API credentials are configured; live collection runs in live mode.' },
  import: { live: false, label: 'Official export', help: 'No free public API: posts come from the platform’s official data export (CSV), through the same pipeline.' },
  demo: { live: false, label: 'Sample data', help: 'Showing sample data; add API credentials to collect live.' },
}

function Connection({ c }: { c: string }) {
  const m = CONNECTION[c] ?? CONNECTION.demo
  return m.live
    ? <StatusBadge status="good" title={m.help}>{m.label}</StatusBadge>
    : <span className="badge" title={m.help}>{c === 'import' ? <FileUp size={12} /> : <Database size={12} />}{m.label}</span>
}

function PlatformPicker({ value, onChange, counts }: { value: string; onChange: (p: string) => void; counts: Record<string, number> }) {
  const items = ['all', ...PLATFORMS]
  return (
    <div className="row-wrap" role="tablist" aria-label="Platform" style={{ marginBottom: 24 }}>
      {items.map(p => (
        <button key={p} role="tab" aria-selected={value === p} className="btn" onClick={() => onChange(p)}
          style={value === p ? { background: 'var(--accent-soft)', color: 'var(--accent-ink)', borderColor: 'transparent' } : undefined}>
          {p !== 'all' && <span style={{ width: 9, height: 9, borderRadius: 3, background: PLATFORM_SLOT[p] }} />}
          {p === 'all' ? 'All platforms' : PLATFORM_LABEL[p]}
          {p !== 'all' && <span className="muted" style={{ fontWeight: 500 }}>{num(counts[p] ?? 0)}</span>}
        </button>
      ))}
    </div>
  )
}

function AllPlatforms({ rows }: { rows: any[] }) {
  const { data: vol } = useVolume('1d')
  const daily = useMemo(() => {
    const m = new Map<string, any>()
    for (const r of vol?.buckets ?? []) {
      const e = m.get(r.bucket) ?? { bucket: r.bucket }
      e[r.platform] = (e[r.platform] ?? 0) + r.n
      m.set(r.bucket, e)
    }
    // drop a trailing partial day (the scenario ends at midnight)
    const total = (d: any) => PLATFORMS.reduce((s, p) => s + (d[p] ?? 0), 0)
    return [...m.values()].filter(d => total(d) >= 50)
  }, [vol])
  const present = PLATFORMS.filter(p => rows.find(r => r.platform === p)?.posts)
  return (
    <div className="stack">
      <Card title="Posts per day by platform">
        <ChartOrTable
          chart={<>
            <Legend items={present.map(p => ({ label: PLATFORM_LABEL[p], color: PLATFORM_SLOT[p] }))} />
            <div style={{ height: 260, marginTop: 10 }}>
              <ResponsiveContainer>
                <LineChart data={daily} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                  <CartesianGrid stroke="var(--hairline)" vertical={false} />
                  <XAxis dataKey="bucket" tick={AXIS_TICK} tickFormatter={istDay} axisLine={{ stroke: 'var(--axis)' }} tickLine={false} />
                  <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} width={48} />
                  <Tooltip content={<ChartTip fmtLabel={(l: string) => istDay(l)} />} />
                  {present.map(p => <Line key={p} dataKey={p} name={PLATFORM_LABEL[p]} stroke={PLATFORM_SLOT[p]} strokeWidth={2} dot={{ r: 4, strokeWidth: 0, fill: PLATFORM_SLOT[p] }} isAnimationActive={false} />)}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </>}
          table={<table className="tbl"><thead><tr><th>Day</th>{present.map(p => <th key={p} className="num">{PLATFORM_LABEL[p]}</th>)}</tr></thead>
            <tbody>{daily.map(d => <tr key={d.bucket}><td>{istDay(d.bucket)}</td>{present.map(p => <td key={p} className="num">{num(d[p] ?? 0)}</td>)}</tr>)}</tbody></table>} />
      </Card>
      <Card title="Coverage" actions={<InfoPop>X and Telegram are the essential sources; Instagram and Facebook arrive through their official data exports; Reddit and YouTube comments add extra context.</InfoPop>}>
        <div className="table-wrap">
          <table className="tbl">
            <thead><tr><th>Platform</th><th>Source</th><th className="num">Posts</th><th className="num">Accounts</th><th className="num">Comments</th><th className="num">From coordinated accounts</th></tr></thead>
            <tbody>{rows.map(r => (
              <tr key={r.platform}>
                <td><span className="row"><span style={{ width: 9, height: 9, borderRadius: 3, background: PLATFORM_SLOT[r.platform] }} /><b>{PLATFORM_LABEL[r.platform]}</b></span></td>
                <td><Connection c={r.connection} /></td>
                <td className="num">{num(r.posts)}</td>
                <td className="num">{num(r.accounts)}</td>
                <td className="num">{num(r.comments)}</td>
                <td className="num">{pct(r.coordinated_share, 1)}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}

function OnePlatform({ p, row }: { p: string; row: any }) {
  const { data: d } = usePlatform(p)
  const { data: vol } = useVolume('1h', p)
  const series = (vol?.buckets ?? []).map((r: any) => ({ bucket: r.bucket, raw: r.n, organic: r.n - (r.coordinated ?? 0) }))
  const emo = EMOTIONS.map(e => ({ name: EMOTION_LABEL[e], key: e, value: d?.emotions?.[e] ?? 0 }))
  if (!row?.posts) return <Empty>No posts from {PLATFORM_LABEL[p]} yet.</Empty>
  return (
    <div className="stack">
      {p === 'telegram' && <LiveTelegram />}
      <div className="grid g-4">
        <Kpi icon={<MessageSquare size={20} />} label="Posts" value={num(row.posts)} foot={`${istDay(row.first_post)} – ${istDay(row.last_post)}`} />
        <Kpi icon={<Users size={20} />} label="Accounts" value={num(row.accounts)} foot="active in this period" />
        <Kpi icon={<MessagesSquare size={20} />} label="Comments & replies" value={num(row.comments)} foot={`${pct(row.comments / Math.max(1, row.posts), 0)} of all posts`} />
        <Kpi icon={<Repeat2 size={20} />} label="From coordinated accounts" value={pct(row.coordinated_share, 1)} foot={`${num(row.reposts)} reposts / shares`} />
      </div>
      <div className="grid g-main">
        <Card title="Activity" sub="posts per hour">
          <ChartOrTable
            chart={<>
              <Legend items={[{ label: 'Organic', color: ORGANIC }, { label: 'All activity', color: RAW }]} />
              <div style={{ height: 230, marginTop: 10 }}>
                <ResponsiveContainer>
                  <AreaChart data={series} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                    <CartesianGrid stroke="var(--hairline)" vertical={false} />
                    <XAxis dataKey="bucket" tick={AXIS_TICK} tickFormatter={istShort} minTickGap={70} axisLine={{ stroke: 'var(--axis)' }} tickLine={false} />
                    <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} width={40} allowDecimals={false} />
                    <Tooltip content={<ChartTip fmtLabel={(l: string) => ist(l)} />} />
                    <Area type="monotone" dataKey="raw" name="All activity" stroke={RAW} fill={RAW} fillOpacity={0.18} strokeWidth={2} isAnimationActive={false} />
                    <Area type="monotone" dataKey="organic" name="Organic" stroke={ORGANIC} fill={ORGANIC} fillOpacity={0.22} strokeWidth={2} isAnimationActive={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </>}
            table={<table className="tbl"><thead><tr><th>Hour</th><th className="num">All</th><th className="num">Organic</th></tr></thead>
              <tbody>{series.map((r: any) => <tr key={r.bucket}><td>{ist(r.bucket)}</td><td className="num">{r.raw}</td><td className="num">{r.organic}</td></tr>)}</tbody></table>} />
        </Card>
        <Card title="Mood on this platform" sub="average emotion score">
          <ChartOrTable
            chart={
              <div style={{ height: 230 }}>
                <ResponsiveContainer>
                  <BarChart data={emo} layout="vertical" margin={{ top: 0, right: 16, left: 4, bottom: 0 }} barCategoryGap={6}>
                    <CartesianGrid stroke="var(--hairline)" horizontal={false} />
                    <XAxis type="number" domain={[0, 1]} ticks={[0, 0.5, 1]} tick={AXIS_TICK} axisLine={false} tickLine={false} />
                    <YAxis type="category" dataKey="name" width={110} tick={{ ...AXIS_TICK, fill: 'var(--ink-2)' }} axisLine={{ stroke: 'var(--axis)' }} tickLine={false} />
                    <Tooltip content={<ChartTip fmtValue={(v: number) => v.toFixed(2)} />} cursor={{ fill: 'var(--surface-2)' }} />
                    <Bar dataKey="value" name="Score" radius={[0, 4, 4, 0]} isAnimationActive={false} fill="var(--s1)"
                      shape={(props: any) => <rect x={props.x} y={props.y} width={props.width} height={props.height} rx={4} fill={EMOTION_SLOT[props.payload.key as keyof typeof EMOTION_SLOT]} />} />
                  </BarChart>
                </ResponsiveContainer>
              </div>}
            table={<table className="tbl"><tbody>{emo.map(e => <tr key={e.key}><td>{e.name}</td><td className="num">{e.value.toFixed(2)}</td></tr>)}</tbody></table>} />
        </Card>
      </div>
      <div className="grid g-3" style={{ alignItems: 'start' }}>
        <Card title="Top topics here">
          <table className="tbl"><tbody>{(d?.topics ?? []).map((t: any) => (
            <tr key={t.topic_id}>
              <td style={{ textTransform: 'capitalize' }}>{t.label}</td>
              <td>{t.nature === 'manufactured' ? <StatusBadge status="critical">Manufactured</StatusBadge> : null}</td>
              <td className="num">{num(t.n)}</td>
            </tr>
          ))}</tbody></table>
        </Card>
        <Card title="Most active accounts">
          <table className="tbl">
            <thead><tr><th>Account</th><th className="num">Posts</th><th className="num">Replies got</th></tr></thead>
            <tbody>{(d?.accounts ?? []).map((a: any) => (
              <tr key={a.account_id}>
                <td>@{a.account_id}{a.coordinated && <div style={{ marginTop: 3 }}><StatusBadge status="critical">In sync</StatusBadge></div>}</td>
                <td className="num">{num(a.posts)}</td>
                <td className="num">{num(a.replies_received)}</td>
              </tr>
            ))}</tbody>
          </table>
        </Card>
        <Card title="Latest posts">
          <div className="stack" style={{ gap: 12 }}>
            {(d?.recent ?? []).map((r: any) => (
              <div key={r.post_id}>
                <div style={{ fontSize: 13.5 }}>{r.text}</div>
                <div className="muted" style={{ fontSize: 12 }}>@{r.author_id} · {r.kind} · {istShort(r.created_at)}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}

export default function Platforms() {
  const [params, setParams] = useSearchParams()
  const sel = params.get('p') ?? 'all'
  const { data } = usePlatforms()
  const rows: any[] = data?.platforms ?? []
  const counts = Object.fromEntries(rows.map(r => [r.platform, r.posts]))
  const row = rows.find(r => r.platform === sel)
  return (
    <div>
      <PageHead title="Platforms" sub="Every source in one place: X, Telegram, Instagram, Facebook, Reddit and YouTube."
        actions={row && <Connection c={row.connection} />} />
      <PlatformPicker value={sel} onChange={p => setParams(p === 'all' ? {} : { p })} counts={counts} />
      {rows.length === 0 ? <Empty>No data yet.</Empty> : sel === 'all' ? <AllPlatforms rows={rows} /> : <OnePlatform p={sel} row={row} />}
      <NextStep />
    </div>
  )
}
