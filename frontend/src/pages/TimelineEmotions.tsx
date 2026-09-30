import { useMemo, useState } from 'react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useCompare, useEmotions, useTopics } from '../hooks/useApi'
import { Card, ChartTip, Empty, InfoPop, Legend, PageHead, Seg } from '../components/ui'
import { AXIS_TICK, EMOTIONS, EMOTION_LABEL, EMOTION_SLOT, RAW, type Emotion } from '../lib/viz'
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
            <LineChart data={data} margin={{ top: 6, right: 8, left: -8, bottom: 0 }}>
              <CartesianGrid stroke="var(--hairline)" vertical={false} />
              <XAxis dataKey="bucket" tick={AXIS_TICK} tickFormatter={v => (bucket === '1d' ? istDay(v) : istShort(v).slice(0, 6))} minTickGap={36} axisLine={{ stroke: 'var(--axis)' }} tickLine={false} />
              <YAxis tick={AXIS_TICK} domain={[0, 1]} ticks={[0, 0.5, 1]} axisLine={false} tickLine={false} width={32} />
              <Tooltip content={<ChartTip fmtLabel={(l: string) => ist(l)} fmtValue={(v: number) => v?.toFixed(2)} />} />
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
  const [topicId, setTopicId] = useState<number | undefined>(undefined)
  const { data: raw } = useEmotions(false, bucket, topicId)
  const { data: org } = useEmotions(true, bucket, topicId)
  const { data: topicsData } = useTopics('coordinated', 30)
  const { data: cmp } = useCompare(topicId)

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

  return (
    <div>
      <PageHead title="Emotions"
        sub="How people feel about it over time: all activity in gray, organic accounts in colour."
        actions={<>
          <select className="input" value={topicId ?? ''} onChange={e => setTopicId(e.target.value ? Number(e.target.value) : undefined)} aria-label="Topic filter">
            <option value="">All topics</option>
            {topics.map(t => <option key={t.topic_id} value={t.topic_id}>{t.nature === 'manufactured' ? '⚠ ' : ''}{t.label}</option>)}
          </select>
          <Seg<'1h' | '1d'> label="Bucket" value={bucket} onChange={setBucket} options={[{ value: '1h', label: 'Hourly' }, { value: '1d', label: 'Daily' }]} />
        </>} />


      {merged.length === 0 ? <Empty>No emotion data yet.</Empty> : (
        <>
          <div className="grid g-3" style={{ marginBottom: 20, alignItems: 'start' }}>
            {EMOTIONS.map(e => <Panel key={e} emotion={e} data={merged} bucket={bucket} />)}
            <Card title="All activity vs organic" sub={topicId ? 'selected topic, whole period' : 'whole period'}
              actions={<InfoPop>Average score over every post. The difference shows how much coordinated accounts shift the mood.</InfoPop>}>
              <table className="tbl">
                <thead><tr><th>Emotion</th><th className="num">All</th><th className="num">Organic</th><th className="num">Shift</th></tr></thead>
                <tbody>{EMOTIONS.map(e => {
                  const r = cmp?.raw?.[e], o = cmp?.organic?.[e]
                  return (
                    <tr key={e}>
                      <td><span className="sw" style={{ width: 8, height: 8, borderRadius: 2, background: EMOTION_SLOT[e], display: 'inline-block', marginRight: 6 }} />{EMOTION_LABEL[e]}</td>
                      <td className="num">{pct(r)}</td><td className="num">{pct(o)}</td>
                      <td className="num" style={{ whiteSpace: 'nowrap' }}>{r != null && o != null ? `${o - r >= 0 ? '+' : '−'}${Math.abs((o - r) * 100).toFixed(1)}` : '—'}</td>
                    </tr>
                  )
                })}</tbody>
              </table>
              <div className="muted" style={{ fontSize: 12, marginTop: 8 }}>{cmp?.raw?.n ?? 0} posts · {cmp?.organic?.n ?? 0} organic</div>
            </Card>
          </div>
          <details className="card" style={{ padding: '14px 20px' }}>
            <summary style={{ cursor: 'pointer', fontWeight: 600 }}>Show data table</summary>
            <div className="table-wrap" style={{ maxHeight: 360, overflowY: 'auto', marginTop: 10 }}>
              <table className="tbl">
                <thead><tr><th>Time</th>{EMOTIONS.map(e => <th key={e} className="num">{EMOTION_LABEL[e]} all / org</th>)}<th className="num">Posts all / org</th></tr></thead>
                <tbody>{merged.map(r => (
                  <tr key={r.bucket}><td>{ist(r.bucket)}</td>
                    {EMOTIONS.map(e => <td key={e} className="num">{r[`raw_${e}`]?.toFixed(2) ?? '—'} / {r[`org_${e}`]?.toFixed(2) ?? '—'}</td>)}
                    <td className="num">{r.n_raw ?? 0} / {r.n_org ?? 0}</td></tr>
                ))}</tbody>
              </table>
            </div>
          </details>
        </>
      )}
    </div>
  )
}
