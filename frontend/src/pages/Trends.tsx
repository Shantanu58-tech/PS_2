import { useEffect, useMemo, useState } from 'react'
import { Area, CartesianGrid, ComposedChart, Line, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Sparkles } from 'lucide-react'
import { useSummarize, useSummary, useTopic, useTopicSeries, useTopics } from '../hooks/useApi'
import { Card, ChartOrTable, ChartTip, Empty, InfoPop, Legend, PageHead, Seg, StatusBadge } from '../components/ui'
import { AXIS_TICK, ORGANIC, PLATFORM_LABEL, PLATFORM_SLOT, RAW } from '../lib/viz'
import { ist, istShort, num, pct } from '../lib/fmt'

const FORECAST = 'var(--s7)'

function SummaryBox({ topicId }: { topicId: number }) {
  const { data } = useSummary(topicId)
  const summarize = useSummarize(topicId)
  if (data?.summary) {
    return (
      <div className="notice">
        <div className="row" style={{ marginBottom: 4 }}><Sparkles size={14} /><b style={{ color: 'var(--ink-1)' }}>LLM summary</b><span className="muted" style={{ fontSize: 11 }}>{data.model} · verify against the evidence</span></div>
        <div>{data.summary}</div>
        {data.key_claims?.length > 0 && <ul style={{ margin: '6px 0 0', paddingLeft: 18 }}>{data.key_claims.map((c: string, i: number) => <li key={i}>{c}</li>)}</ul>}
      </div>
    )
  }
  return (
    <div className="row-wrap">
      <button className="btn btn-sm" disabled={!data?.enabled || summarize.isPending} onClick={() => summarize.mutate()}>
        <Sparkles size={14} />{summarize.isPending ? 'Summarising…' : 'Summarise with Gemini'}
      </button>
      {!data?.enabled && <span className="muted" style={{ fontSize: 12 }}>LLM summaries are disabled (no API key).</span>}
      {summarize.isError && <span className="muted" style={{ fontSize: 12 }}>{String(summarize.error)}</span>}
      <InfoPop>Posts are treated as untrusted data: nonce-fenced input, a fixed JSON output schema, and grounding checks. Unsafe or ungrounded output is rejected.</InfoPop>
    </div>
  )
}

export default function Trends() {
  const [sort, setSort] = useState<'rising' | 'volume' | 'coordinated'>('rising')
  const { data } = useTopics(sort, 40)
  const topics: any[] = data?.topics ?? []
  const [sel, setSel] = useState<number | undefined>()
  useEffect(() => { if (sel == null && topics.length) setSel(topics[0].topic_id) }, [topics, sel])
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
      <PageHead code="PS · D" title="Trends & topic detection"
        sub="Topics are clustered per 24-hour window with multilingual embeddings and kept stable across windows by centroid matching. Bursts use Kleinberg's model; forecasts use gradient boosting and a Hawkes process." />
      <div className="grid" style={{ gridTemplateColumns: 'minmax(260px, 360px) minmax(0, 1fr)' }}>
        <Card title="Topics" actions={<Seg label="Sort" value={sort} onChange={v => { setSort(v); setSel(undefined) }} options={[
          { value: 'rising', label: 'Rising' }, { value: 'volume', label: 'Volume' }, { value: 'coordinated', label: 'Coordinated' }]} />}>
          {topics.length === 0 ? <Empty>No topics yet.</Empty> : (
            <div className="stack" style={{ gap: 4, maxHeight: 640, overflowY: 'auto' }}>
              {topics.map(t => (
                <button key={t.topic_id} onClick={() => setSel(t.topic_id)} className="btn btn-ghost"
                  style={{ justifyContent: 'space-between', textAlign: 'left', background: sel === t.topic_id ? 'var(--surface-2)' : undefined, boxShadow: sel === t.topic_id ? 'inset 2px 0 0 var(--accent)' : undefined }}>
                  <span style={{ minWidth: 0 }}>
                    <span style={{ display: 'block', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{t.label}</span>
                    <span className="muted" style={{ fontSize: 11 }}>{num(t.n_posts)} posts{t.max_burst_level ? ` · burst L${t.max_burst_level}` : ''}{t.rise != null ? ` · rise ${t.rise.toFixed(2)}` : ''}</span>
                  </span>
                  {t.nature === 'manufactured' ? <StatusBadge status="critical">Manufactured</StatusBadge> : <StatusBadge status="good">Organic</StatusBadge>}
                </button>
              ))}
            </div>
          )}
        </Card>

        {topic ? (
          <div className="stack">
            <Card title={topic.label}
              sub={<>{(topic.keywords ?? []).join(' · ')} · first seen {ist(topic.first_seen)} · coordinated share {pct(topic.coordinated_share)}</>}
              actions={topic.nature === 'manufactured'
                ? <StatusBadge status="critical" title="≥ 30% of posts from coordinated accounts">Manufactured trend</StatusBadge>
                : <StatusBadge status="good">Organic surge</StatusBadge>}>
              <ChartOrTable
                chart={<>
                  <Legend items={[{ label: 'Organic', color: ORGANIC }, { label: 'Raw', color: RAW }, { label: 'Forecast (GBR, 80% band)', color: FORECAST }, { label: 'Hawkes forecast (dashed)', color: FORECAST }, { label: 'Burst window', color: 'color-mix(in srgb, var(--serious) 40%, transparent)' }]} />
                  <div style={{ height: 300, marginTop: 8 }}>
                    <ResponsiveContainer>
                      <ComposedChart data={chart} margin={{ top: 8, right: 12, left: -16, bottom: 0 }}>
                        <CartesianGrid stroke="var(--hairline)" vertical={false} />
                        <XAxis dataKey="t" tick={AXIS_TICK} tickFormatter={v => istShort(v)} minTickGap={70} axisLine={{ stroke: 'var(--axis)' }} tickLine={false} />
                        <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} width={44} allowDecimals={false} />
                        <Tooltip content={<ChartTip fmtLabel={(l: string) => ist(l)} fmtValue={(v: any) => Array.isArray(v) ? `${v[0].toFixed(1)}–${v[1].toFixed(1)}` : typeof v === 'number' ? v.toFixed(1) : v} />} />
                        {bursts.map((b, i) => <ReferenceArea key={i} x1={snap(b.start)} x2={snap(b.end)} fill="var(--serious)" fillOpacity={0.12} stroke="none" ifOverflow="extendDomain" />)}
                        <Area dataKey="band" name="Forecast band" stroke="none" fill={FORECAST} fillOpacity={0.15} isAnimationActive={false} />
                        <Line dataKey="raw" name="Raw" stroke={RAW} strokeWidth={2} dot={false} isAnimationActive={false} />
                        <Line dataKey="organic" name="Organic" stroke={ORGANIC} strokeWidth={2} dot={false} isAnimationActive={false} />
                        <Line dataKey="gbr" name="Forecast (GBR)" stroke={FORECAST} strokeWidth={2} dot={false} isAnimationActive={false} connectNulls />
                        <Line dataKey="hawkes" name="Forecast (Hawkes)" stroke={FORECAST} strokeWidth={2} strokeDasharray="5 4" dot={false} isAnimationActive={false} connectNulls />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                </>}
                table={<table className="tbl"><thead><tr><th>Hour (IST)</th><th className="num">Raw</th><th className="num">Organic</th><th className="num">GBR</th><th className="num">Hawkes</th></tr></thead>
                  <tbody>{chart.map(r => <tr key={r.t}><td>{ist(r.t)}</td><td className="num">{r.raw ?? ''}</td><td className="num">{r.organic ?? ''}</td><td className="num">{r.gbr?.toFixed?.(1) ?? ''}</td><td className="num">{r.hawkes?.toFixed?.(1) ?? ''}</td></tr>)}</tbody></table>} />
              {bursts.length > 0 && (
                <div className="muted" style={{ fontSize: 12, marginTop: 8 }}>
                  {bursts.length} Kleinberg burst window{bursts.length > 1 ? 's' : ''}; strongest level {Math.max(...bursts.map(b => b.level))}.
                  <InfoPop>States i with rate αᵢ = sⁱ/ĝ; moving up costs (j−i)·γ·ln n (γ = 1). The Viterbi path's runs in state ≥ 1 are bursts. Larger γ means fewer false alarms.</InfoPop>
                </div>
              )}
            </Card>
            <div className="grid g-2">
              <Card title="Representative posts" sub="closest to the topic centroid">
                <div className="stack" style={{ gap: 8 }}>
                  {(topic.representative_posts ?? []).map((p: any) => (
                    <div key={p.platform + p.post_id} className="row" style={{ alignItems: 'flex-start' }}>
                      <span className="badge"><span className="dot" style={{ background: PLATFORM_SLOT[p.platform] ?? 'var(--ink-3)' }} />{PLATFORM_LABEL[p.platform] ?? p.platform}</span>
                      <span style={{ fontSize: 13 }}>{p.text}<div className="muted" style={{ fontSize: 11 }}>{ist(p.created_at)}</div></span>
                    </div>
                  ))}
                </div>
              </Card>
              <Card title="Where it is discussed" sub="posts per platform">
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
    </div>
  )
}
