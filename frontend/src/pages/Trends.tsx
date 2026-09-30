import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Area, CartesianGrid, ComposedChart, Line, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Sparkles } from 'lucide-react'
import { useKeywords, useSituation, useSummarize, useSummary, useTopic, useTopicSeries, useTopics } from '../hooks/useApi'
import { Card, ChartOrTable, ChartTip, Empty, Legend, NextStep, PageHead, Seg, StatusBadge } from '../components/ui'
import { AXIS_TICK, ORGANIC, PLATFORM_LABEL, PLATFORM_SLOT, RAW } from '../lib/viz'
import { ist, istShort, num, pct } from '../lib/fmt'

const FORECAST = 'var(--s7)'

function SummaryBox({ topicId }: { topicId: number }) {
  const { data } = useSummary(topicId)
  const summarize = useSummarize(topicId)
  if (data?.summary) {
    return (
      <div className="notice">
        <div className="row" style={{ marginBottom: 4 }}><Sparkles size={14} /><b style={{ color: 'var(--ink-1)' }}>AI summary</b></div>
        <div>{data.summary}</div>
        <div className="sum-cols">
          {data.key_claims?.length > 0 && (
            <div><div className="sum-h claim">What is being claimed</div>
              <ul>{data.key_claims.map((c: string, i: number) => <li key={i}>{c}</li>)}</ul></div>
          )}
          {data.rebuttals?.length > 0 && (
            <div><div className="sum-h rebut">What pushes back</div>
              <ul>{data.rebuttals.map((c: string, i: number) => <li key={i}>{c}</li>)}</ul></div>
          )}
        </div>
        <div className="muted" style={{ fontSize: 11.5, marginTop: 6 }}>Claims are what posts say, not verified facts.</div>
      </div>
    )
  }
  return (
    <div className="row-wrap">
      <button className="btn btn-sm" disabled={!data?.enabled || summarize.isPending} onClick={() => summarize.mutate()}>
        <Sparkles size={14} />{summarize.isPending ? 'Summarising…' : 'Summarise with AI'}
      </button>
      {summarize.isError && <span className="muted" style={{ fontSize: 12 }}>{String(summarize.error)}</span>}
    </div>
  )
}

function Keywords() {
  const { data } = useKeywords()
  const [view, setView] = useState<'viral' | 'top'>('viral')
  const rows: any[] = data?.[view] ?? []
  return (
    <Card title="Viral hashtags" sub={view === 'viral' ? 'biggest spikes: busiest hour compared with the usual hourly rate' : 'most used over the whole period'}
      style={{ marginTop: 20 }}
      actions={<Seg<'viral' | 'top'> label="Hashtag ranking" value={view} onChange={setView} options={[{ value: 'viral', label: 'Viral spikes' }, { value: 'top', label: 'Most used' }]} />}>
      {rows.length === 0 ? <Empty>No hashtags yet.</Empty> : (
        <div className="table-wrap">
          <table className="tbl">
            <thead><tr><th>#</th><th>Hashtag</th><th>Peak hour</th><th className="num">Posts at peak</th><th className="num">Spike</th><th className="num">All time</th><th>Where</th></tr></thead>
            <tbody>{rows.map((k, i) => (
              <tr key={k.keyword}>
                <td className="muted tnum">{i + 1}</td>
                <td style={{ fontWeight: 600 }}>{k.keyword}</td>
                <td className="muted">{istShort(k.peak_at)}</td>
                <td className="num">{num(k.peak_per_hour)}</td>
                <td className="num" style={{ fontWeight: 600 }}>{k.spike.toFixed(0)}×</td>
                <td className="num">{num(k.posts)}</td>
                <td className="muted">{k.platforms.map((p: string) => PLATFORM_LABEL[p] ?? p).join(' · ')}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
    </Card>
  )
}

export default function Trends() {
  const [params, setParams] = useSearchParams()
  const sector = params.get('sector') ?? ''
  const [sort, setSort] = useState<'rising' | 'volume' | 'coordinated'>((params.get('sort') as any) || 'rising')
  const { data } = useTopics(sort, sector ? 200 : 40)
  const { data: sit } = useSituation()
  const topics: any[] = (data?.topics ?? []).filter((t: any) => !sector || sit?.topic_sectors?.[String(t.topic_id)] === sector)
  const [sel, setSel] = useState<number | undefined>(params.get('topic') ? Number(params.get('topic')) : undefined)
  useEffect(() => { const t = params.get('topic'); if (t) setSel(Number(t)) }, [params])
  useEffect(() => { if (sel == null && topics.length) setSel(topics[0].topic_id) }, [topics, sel])
  const clearSector = () => { const p = new URLSearchParams(params); p.delete('sector'); setParams(p); setSel(undefined) }
  const { data: topic } = useTopic(sel)
  const { data: s } = useTopicSeries(sel)

  const chart = useMemo(() => {
    const rows: any[] = (s?.series ?? []).map((r: any) => ({ t: r.bucket_start, raw: r.count_all, organic: r.count_organic }))
    const fc = s?.forecast ?? []
    const byT = new Map<string, any>()
    for (const f of fc) {
      const e = byT.get(f.bucket_start) ?? { t: f.bucket_start }
      if (f.model === 'gbr') { e.gbr = f.predicted; e.band = [f.lower ?? f.predicted, f.upper ?? f.predicted] }
      if (f.model === 'hawkes') e.hawkes = f.predicted
      byT.set(f.bucket_start, e)
    }
    if (rows.length && byT.size) { // join the forecast to the last observed point
      const last = rows[rows.length - 1]
      last.gbr = last.raw; last.hawkes = last.raw; last.band = [last.raw, last.raw]
    }
    return [...rows, ...[...byT.values()].sort((a, b) => a.t.localeCompare(b.t))]
  }, [s])
  const bursts: any[] = (s?.bursts ?? []).filter((b: any) => b.level >= 1)
  const snap = (iso: string) => { // bursts are exact times; the x-axis is hourly buckets
    const d = new Date(iso); d.setUTCMinutes(0, 0, 0)
    return d.toISOString().replace('.000Z', 'Z')
  }

  return (
    <div>
      <PageHead title="Trends" sub="Every topic people are talking about, and whether its growth is genuine."
        actions={sector && <span className="badge" style={{ fontSize: 13, padding: '6px 10px' }}>Sector: {sit?.sector_names?.[sector] ?? sector}
          <button className="btn btn-ghost btn-sm" style={{ padding: '0 4px' }} aria-label="Clear sector filter" onClick={clearSector}>✕</button></span>} />
      <div className="grid" style={{ gridTemplateColumns: 'minmax(260px, 360px) minmax(0, 1fr)' }}>
        <Card title="Topics" actions={<Seg label="Sort" value={sort} onChange={v => { setSort(v); setSel(undefined) }} options={[
          { value: 'rising', label: 'Rising' }, { value: 'volume', label: 'Volume' }, { value: 'coordinated', label: 'Coordinated' }]} />}>
          {topics.length === 0 ? <Empty>No topics yet.</Empty> : (
            <div className="stack" style={{ gap: 4, maxHeight: 640, overflowY: 'auto' }}>
              {topics.map(t => (
                <button key={t.topic_id} onClick={() => setSel(t.topic_id)} className="btn btn-ghost"
                  style={{ justifyContent: 'space-between', textAlign: 'left', borderRadius: 12, background: sel === t.topic_id ? 'var(--accent-soft)' : undefined }}>
                  <span style={{ minWidth: 0 }}>
                    <span style={{ display: 'block', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', textTransform: 'capitalize' }}>{t.label}</span>
                    <span className="muted" style={{ fontSize: 12, fontWeight: 400 }}>{num(t.n_posts)} posts</span>
                  </span>
                  {t.nature === 'manufactured' ? <StatusBadge status="critical">Likely coordinated</StatusBadge> : <StatusBadge status="good">Organic</StatusBadge>}
                </button>
              ))}
            </div>
          )}
        </Card>

        {topic ? (
          <div className="stack">
            <Card title={<span style={{ textTransform: 'capitalize' }}>{topic.label}</span>}
              sub={<>first seen {ist(topic.first_seen)} · {pct(topic.coordinated_share)} from coordinated accounts</>}
              actions={topic.nature === 'manufactured'
                ? <StatusBadge status="critical" title="30% or more of posts from coordinated accounts">Likely coordinated</StatusBadge>
                : <StatusBadge status="good">Organic</StatusBadge>}>
              <ChartOrTable
                chart={<>
                  <Legend items={[{ label: 'Organic', color: ORGANIC }, { label: 'All activity', color: RAW }, { label: 'Forecast', color: FORECAST }, { label: 'Burst', color: 'color-mix(in srgb, var(--serious) 40%, transparent)' }]} />
                  <div style={{ height: 300, marginTop: 8 }}>
                    <ResponsiveContainer>
                      <ComposedChart data={chart} margin={{ top: 8, right: 12, left: -16, bottom: 0 }}>
                        <CartesianGrid stroke="var(--hairline)" vertical={false} />
                        <XAxis dataKey="t" tick={AXIS_TICK} tickFormatter={v => istShort(v)} minTickGap={100} axisLine={{ stroke: 'var(--axis)' }} tickLine={false} />
                        <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} width={44} allowDecimals={false} />
                        <Tooltip content={<ChartTip fmtLabel={(l: string) => ist(l)} fmtValue={(v: any) => Array.isArray(v) ? `${v[0].toFixed(1)}–${v[1].toFixed(1)}` : typeof v === 'number' ? v.toFixed(1) : v} />} />
                        {bursts.map((b, i) => <ReferenceArea key={i} x1={snap(b.start)} x2={snap(b.end)} fill="var(--serious)" fillOpacity={0.12} stroke="none" ifOverflow="extendDomain" />)}
                        <Area dataKey="band" name="Forecast range" stroke="none" fill={FORECAST} fillOpacity={0.15} isAnimationActive={false} />
                        <Line dataKey="raw" name="All activity" stroke={RAW} strokeWidth={2} dot={false} isAnimationActive={false} />
                        <Line dataKey="organic" name="Organic" stroke={ORGANIC} strokeWidth={2} dot={false} isAnimationActive={false} />
                        <Line dataKey="gbr" name="Forecast" stroke={FORECAST} strokeWidth={2} strokeDasharray="5 4" dot={false} isAnimationActive={false} connectNulls />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                </>}
                table={<table className="tbl"><thead><tr><th>Hour</th><th className="num">All activity</th><th className="num">Organic</th><th className="num">Forecast</th></tr></thead>
                  <tbody>{chart.map(r => <tr key={r.t}><td>{ist(r.t)}</td><td className="num">{r.raw ?? ''}</td><td className="num">{r.organic ?? ''}</td><td className="num">{r.gbr?.toFixed?.(1) ?? ''}</td></tr>)}</tbody></table>} />
            </Card>
            <div className="grid g-2">
              <Card title="Top posts">
                <div className="stack" style={{ gap: 8 }}>
                  {(topic.representative_posts ?? []).map((p: any) => (
                    <div key={p.platform + p.post_id} className="row" style={{ alignItems: 'flex-start' }}>
                      <span className="badge"><span className="dot" style={{ background: PLATFORM_SLOT[p.platform] ?? 'var(--ink-3)' }} />{PLATFORM_LABEL[p.platform] ?? p.platform}</span>
                      <span style={{ fontSize: 13.5 }}>{p.text}<div className="muted" style={{ fontSize: 12 }}>{ist(p.created_at)}</div></span>
                    </div>
                  ))}
                </div>
              </Card>
              <Card title="Where it is discussed">
                <table className="tbl"><tbody>{(topic.platforms ?? []).map((p: any) => (
                  <tr key={p.platform}><td><span className="dot" style={{ width: 8, height: 8, borderRadius: 2, background: PLATFORM_SLOT[p.platform], display: 'inline-block', marginRight: 6 }} />{PLATFORM_LABEL[p.platform] ?? p.platform}</td><td className="num">{num(p.n)}</td></tr>
                ))}</tbody></table>
                <div className="divider" />
                <SummaryBox topicId={topic.topic_id} />
              </Card>
            </div>
          </div>
        ) : <Empty>Select a topic.</Empty>}
      </div>
      <Keywords />
      <NextStep />
    </div>
  )
}
