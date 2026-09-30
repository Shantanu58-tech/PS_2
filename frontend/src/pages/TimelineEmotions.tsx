import { useEffect, useMemo, useState } from 'react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useCompare, useEmotions, useSituation, useTopics } from '../hooks/useApi'
import { Card, ChartTip, Empty, InfoPop, Legend, NextStep, PageHead, Seg } from '../components/ui'
import { AXIS_TICK, EMOTIONS, EMOTION_LABEL, EMOTION_SLOT, PLATFORMS, PLATFORM_LABEL, RAW, type Emotion } from '../lib/viz'
import { ist, istDay, istShort, pct } from '../lib/fmt'

function Panel({ emotion, data, bucket }: { emotion: Emotion; data: any[]; bucket: string }) {
  const color = EMOTION_SLOT[emotion]
  return (
    <section className="card">
      <div className="card-head">
        <h2 className="card-title">{EMOTION_LABEL[emotion]}</h2>
        <Legend items={[{ label: 'Organic', color }, { label: 'All activity', color: RAW }]} />
      </div>
      <div className="card-body">
        <div style={{ height: 150 }}>
          <ResponsiveContainer>
            <LineChart data={data} margin={{ top: 6, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="var(--hairline)" vertical={false} />
              <XAxis dataKey="bucket" tick={AXIS_TICK} tickFormatter={v => (bucket === '1d' ? istDay(v) : istShort(v).slice(0, 6))} minTickGap={36} axisLine={{ stroke: 'var(--axis)' }} tickLine={false} />
              <YAxis tick={AXIS_TICK} domain={[0, 1]} ticks={[0, 0.5, 1]} tickFormatter={v => `${Math.round(v * 100)}%`} axisLine={false} tickLine={false} width={44} />
              <Tooltip content={<ChartTip fmtLabel={(l: string) => ist(l)} fmtValue={(v: number) => pct(v, 1)} />} />
              <Line type="monotone" dataKey={`raw_${emotion}`} name="All activity" stroke={RAW} strokeWidth={2} dot={false} isAnimationActive={false} connectNulls />
              <Line type="monotone" dataKey={`org_${emotion}`} name="Organic" stroke={color} strokeWidth={2} dot={false} isAnimationActive={false} connectNulls />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  )
}

export default function TimelineEmotions() {
  const [bucket, setBucket] = useState<'1h' | '1d'>('1d')
  const [topicId, setTopicIdRaw] = useState<number | undefined>(undefined)
  const [picked, setPicked] = useState(false)
  const setTopicId = (t: number | undefined) => { setPicked(true); setTopicIdRaw(t) }
  const { data: sit } = useSituation()
  // Open on the story the Situation Room flagged, so the first view answers "how does it make people feel?"
  const flagged: number | undefined = sit?.kpis?.top_alert?.topic_id
  // a flagged story lives for hours, not days, so it opens in hourly buckets
  useEffect(() => { if (!picked && flagged != null) { setTopicIdRaw(flagged); setBucket('1h') } }, [flagged, picked])
  const [platform, setPlatform] = useState('')
  const [kind, setKind] = useState<'all' | 'posts' | 'comments'>('all')
  const { data: raw } = useEmotions(false, bucket, topicId, platform, kind)
  const { data: org } = useEmotions(true, bucket, topicId, platform, kind)
  const { data: topicsData } = useTopics('coordinated', 30)
  const { data: cmp } = useCompare(topicId, platform, kind)
  const { data: base } = useCompare(undefined, platform, kind)

  const merged = useMemo(() => {
    const m = new Map<string, any>()
    for (const r of raw?.buckets ?? []) m.set(r.bucket, { bucket: r.bucket, n_raw: r.n, ...Object.fromEntries(EMOTIONS.map(e => [`raw_${e}`, r[e]])) })
    for (const r of org?.buckets ?? []) {
      const e0 = m.get(r.bucket) ?? { bucket: r.bucket }
      m.set(r.bucket, { ...e0, n_org: r.n, ...Object.fromEntries(EMOTIONS.map(e => [`org_${e}`, r[e]])) })
    }
    return [...m.values()].sort((a, b) => a.bucket.localeCompare(b.bucket))
  }, [raw, org])

  const topics: any[] = topicsData?.topics ?? []
  const topicLabel = topics.find(t => t.topic_id === topicId)?.label ?? sit?.kpis?.top_alert?.label
  const pts = (d: number) => `${d >= 0 ? '+' : '−'}${Math.abs(d * 100).toFixed(1)} pts`
  // the emotion this story moves furthest from the everyday level
  const lead = topicId != null && cmp?.raw && base?.raw
    ? EMOTIONS.map(e => ({ e, d: (cmp.raw[e] ?? 0) - (base.raw[e] ?? 0) })).sort((a, b) => Math.abs(b.d) - Math.abs(a.d))[0]
    : null

  return (
    <div>
      <PageHead title="Emotions"
        sub={topicId != null ? `How people feel about “${topicLabel ?? 'this story'}”: all activity in gray, ordinary accounts in colour.` : 'How people feel over time: all activity in gray, ordinary accounts in colour.'}
        actions={<>
          <select className="input" value={platform} onChange={e => setPlatform(e.target.value)} aria-label="Platform filter">
            <option value="">All platforms</option>
            {PLATFORMS.map(p => <option key={p} value={p}>{PLATFORM_LABEL[p]}</option>)}
          </select>
          <Seg<'all' | 'posts' | 'comments'> label="Post type" value={kind} onChange={setKind} options={[
            { value: 'all', label: 'All' }, { value: 'posts', label: 'Posts' }, { value: 'comments', label: 'Comments' }]} />
          <select className="input" value={topicId ?? ''} onChange={e => setTopicId(e.target.value ? Number(e.target.value) : undefined)} aria-label="Topic filter">
            <option value="">All topics (everyday level)</option>
            {topics.map(t => <option key={t.topic_id} value={t.topic_id}>{t.nature === 'manufactured' ? '⚠ ' : ''}{t.label}</option>)}
          </select>
          <Seg<'1h' | '1d'> label="Bucket" value={bucket} onChange={setBucket} options={[{ value: '1h', label: 'Hourly' }, { value: '1d', label: 'Daily' }]} />
        </>} />


      {lead && Math.abs(lead.d) >= 0.02 && (
        <div className="callout" style={{ marginBottom: 16 }}>
          <b>{EMOTION_LABEL[lead.e]}</b> on “{topicLabel}” is <b>{pts(lead.d)}</b> {lead.d >= 0 ? 'above' : 'below'} the everyday level
          {cmp?.organic?.[lead.e] != null && <> ({pct(cmp.raw[lead.e], 1)} overall, {pct(cmp.organic[lead.e], 1)} among ordinary accounts)</>}.
        </div>
      )}
      {merged.length === 0 ? <Empty>No posts match these filters.</Empty> : (
        <>
          <Card style={{ marginBottom: 20 }} title={topicId != null ? 'This story vs the everyday level' : 'All activity vs organic'}
            sub={topicId != null ? 'average score, whole period · everyday = all topics' : 'average score, whole period'}
            actions={<InfoPop>Each post gets a score from 0 to 100% per emotion. "Everyday" is the average over every topic. "Organic" leaves out the coordinated accounts, so the gap between the two shows how much the campaign shifts the mood. Differences are in percentage points.</InfoPop>}>
            <table className="tbl">
              <thead><tr><th>Emotion</th>{topicId != null && <th className="num">Everyday</th>}<th className="num">{topicId != null ? 'This story' : 'All'}</th><th className="num">Organic</th>
                {topicId != null && <th className="num">vs everyday</th>}</tr></thead>
              <tbody>{EMOTIONS.map(e => {
                const r = cmp?.raw?.[e], o = cmp?.organic?.[e], b = base?.raw?.[e]
                return (
                  <tr key={e}>
                    <td><span className="sw" style={{ width: 8, height: 8, borderRadius: 2, background: EMOTION_SLOT[e], display: 'inline-block', marginRight: 6 }} />{EMOTION_LABEL[e]}</td>
                    {topicId != null && <td className="num muted">{pct(b, 1)}</td>}
                    <td className="num">{pct(r, 1)}</td><td className="num">{pct(o, 1)}</td>
                    {topicId != null && <td className="num" style={{ whiteSpace: 'nowrap', fontWeight: 600 }}>{r != null && b != null ? pts(r - b) : '—'}</td>}
                  </tr>
                )
              })}</tbody>
            </table>
            <div className="muted" style={{ fontSize: 12, marginTop: 8 }}>{(cmp?.raw?.n ?? 0).toLocaleString('en-IN')} posts · {(cmp?.organic?.n ?? 0).toLocaleString('en-IN')} from ordinary accounts</div>
          </Card>
          <div className="grid g-3" style={{ marginBottom: 20, alignItems: 'start' }}>
            {EMOTIONS.map(e => <Panel key={e} emotion={e} data={merged} bucket={bucket} />)}
          </div>
          <details className="card" style={{ padding: '14px 20px' }}>
            <summary style={{ cursor: 'pointer', fontWeight: 600 }}>Show data table</summary>
            <div className="table-wrap" style={{ maxHeight: 360, overflowY: 'auto', marginTop: 10 }}>
              <table className="tbl">
                <thead><tr><th>Time</th>{EMOTIONS.map(e => <th key={e} className="num">{EMOTION_LABEL[e]} all / org</th>)}<th className="num">Posts all / org</th></tr></thead>
                <tbody>{merged.map(r => (
                  <tr key={r.bucket}><td>{ist(r.bucket)}</td>
                    {EMOTIONS.map(e => <td key={e} className="num">{pct(r[`raw_${e}`], 1)} / {pct(r[`org_${e}`], 1)}</td>)}
                    <td className="num">{r.n_raw ?? 0} / {r.n_org ?? 0}</td></tr>
                ))}</tbody>
              </table>
            </div>
          </details>
        </>
      )}
      <NextStep />
    </div>
  )
}
