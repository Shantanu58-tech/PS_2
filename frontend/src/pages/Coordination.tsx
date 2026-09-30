import { useEffect, useState } from 'react'
import { Gauge, MessageSquare, Users } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useCluster, useClusters } from '../hooks/useApi'
import { Card, ChartOrTable, ChartTip, Empty, InfoPop, Kpi, Legend, Meter, PageHead, StatusBadge } from '../components/ui'
import { AXIS_TICK, PLATFORM_LABEL, RAW } from '../lib/viz'
import { ist, istShort, num, pct } from '../lib/fmt'

const FLAGGED = 'var(--critical)'

// Each signal is shown as a 0–1 strength pointing toward "more scripted".
const SIGNALS: { key: string; label: string; strength: (v: number) => number; help: string }[] = [
  { key: 'sync', label: 'Posting in sync', strength: v => v, help: 'Share of posts followed by another post within a minute.' },
  { key: 'hn', label: 'Predictable timing', strength: v => 1 - v, help: 'How concentrated the gaps between posts are. Scheduled posting has very predictable gaps.' },
  { key: 'burstiness', label: 'Clock-like rhythm', strength: v => (1 - v) / 2, help: 'Humans post in irregular bursts; scripts post at a steady beat.' },
  { key: 'dup_ratio', label: 'Copy-paste text', strength: v => v, help: 'Share of posts with a near-identical copy written by a different account.' },
  { key: 'regular_share', label: 'Robotic cadence', strength: v => v, help: 'Share of posts from accounts whose own posting rhythm is machine-regular.' },
]

export default function Coordination() {
  const { data } = useClusters()
  const clusters: any[] = data?.clusters ?? []
  const [sel, setSel] = useState<number | undefined>()
  useEffect(() => { if (sel == null && clusters.length) setSel(clusters[0].cluster_id) }, [clusters, sel])
  const { data: detail } = useCluster(sel)
  const c = detail?.cluster
  const accounts: any[] = detail?.accounts ?? []
  const flagged = accounts.filter(a => a.score >= 0.7)

  return (
    <div>
      <PageHead title="Coordination" sub="Groups of accounts posting the same thing at the same time." />
      {clusters.length === 0 ? <Empty>No coordinated groups found.</Empty> : (
        <>
          <div className="grid g-3" style={{ marginBottom: 24 }}>
            <Kpi icon={<Users size={20} />} label="Accounts acting in sync" value={num(flagged.length)} foot={`of ${num(accounts.length)} in this group`} />
            <Kpi icon={<Gauge size={20} />} label="Coordination score" value={c ? `${Math.round(c.score * 100)}%` : '—'} foot="how scripted the group looks" />
            <Kpi icon={<MessageSquare size={20} />} label="Posts pushed" value={num(c?.n_posts)} foot={c?.topic_label ? <span style={{ textTransform: 'capitalize' }}>{c.topic_label}</span> : ''} />
          </div>

          <div className="grid" style={{ gridTemplateColumns: 'minmax(220px, 300px) minmax(0, 1fr)' }}>
            <Card title="Groups" style={{ alignSelf: 'start' }}>
              <div className="stack" style={{ gap: 4 }}>
                {clusters.map(cl => (
                  <button key={cl.cluster_id} className="btn btn-ghost" onClick={() => setSel(cl.cluster_id)}
                    style={{ justifyContent: 'space-between', borderRadius: 12, background: sel === cl.cluster_id ? 'var(--accent-soft)' : undefined }}>
                    <span style={{ textAlign: 'left', textTransform: 'capitalize' }}>{cl.topic_label ?? `Group ${cl.cluster_id}`}<div className="muted" style={{ fontSize: 12, fontWeight: 400, textTransform: 'none' }}>{num(cl.n_coordinated)} accounts · {num(cl.n_posts)} posts</div></span>
                    <span className="tnum">{Math.round(cl.score * 100)}%</span>
                  </button>
                ))}
              </div>
            </Card>

            {c ? (
              <div className="stack">
                <Card title="Why this group was flagged" sub="a signal for review, not an accusation">
                  <table className="tbl">
                    <tbody>{SIGNALS.map(s => (
                      <tr key={s.key}>
                        <td style={{ width: '38%' }}>{s.label} <InfoPop>{s.help}</InfoPop></td>
                        <td>{c[s.key] != null && <Meter value={s.strength(c[s.key])} color="var(--serious)" label={s.label} />}</td>
                        <td className="num" style={{ width: 70 }}>{c[s.key] != null ? pct(Math.max(0, Math.min(1, s.strength(c[s.key]))), 0) : '—'}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                </Card>

                <Card title="Timing" sub="posts per minute: accounts in sync vs everyone else">
                  <ChartOrTable
                    chart={<>
                      <Legend items={[{ label: 'In sync', color: FLAGGED }, { label: 'Everyone else', color: RAW }]} />
                      <div style={{ height: 200, marginTop: 8 }}>
                        <ResponsiveContainer>
                          <BarChart data={detail?.timing ?? []} margin={{ top: 6, right: 8, left: 0, bottom: 0 }} barCategoryGap={1}>
                            <CartesianGrid stroke="var(--hairline)" vertical={false} />
                            <XAxis dataKey="minute" tick={AXIS_TICK} tickFormatter={v => istShort(v).slice(-5)} minTickGap={36} axisLine={{ stroke: 'var(--axis)' }} tickLine={false} />
                            <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} allowDecimals={false} width={32} />
                            <Tooltip content={<ChartTip fmtLabel={(l: string) => ist(l)} />} cursor={{ fill: 'var(--surface-2)' }} />
                            <Bar dataKey="coordinated" name="In sync" stackId="a" fill={FLAGGED} isAnimationActive={false} />
                            <Bar dataKey="other" name="Everyone else" stackId="a" fill={RAW} radius={[4, 4, 0, 0]} isAnimationActive={false} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </>}
                    table={<table className="tbl"><thead><tr><th>Minute</th><th className="num">In sync</th><th className="num">Everyone else</th></tr></thead>
                      <tbody>{(detail?.timing ?? []).map((r: any) => <tr key={r.minute}><td>{ist(r.minute)}</td><td className="num">{r.coordinated}</td><td className="num">{r.other}</td></tr>)}</tbody></table>} />
                </Card>

                <Card title="Accounts">
                  <div className="table-wrap" style={{ maxHeight: 360, overflowY: 'auto' }}>
                    <table className="tbl">
                      <thead><tr><th>Account</th><th /><th className="num">Score</th><th className="num">Posts</th></tr></thead>
                      <tbody>{accounts.map(a => (
                        <tr key={a.account_id}>
                          <td>@{a.account_id}<div className="muted" style={{ fontSize: 12 }}>{String(a.platforms).split(',').map((p: string) => PLATFORM_LABEL[p] ?? p).join(', ')}</div></td>
                          <td>{a.score >= 0.7 ? <StatusBadge status="critical">In sync</StatusBadge> : null}</td>
                          <td className="num">{Math.round(a.score * 100)}%</td>
                          <td className="num">{a.reasons?.n_posts ?? '—'}</td>
                        </tr>
                      ))}</tbody>
                    </table>
                  </div>
                </Card>

                <Card title="Sample posts" sub="from accounts in sync">
                  <table className="tbl">
                    <thead><tr><th>Time</th><th>Account</th><th>Post</th></tr></thead>
                    <tbody>{(detail?.evidence_posts ?? []).slice(0, 8).map((p: any) => (
                      <tr key={p.platform + p.post_id}><td style={{ whiteSpace: 'nowrap' }}>{istShort(p.created_at)}</td><td>@{p.author_id}</td><td>{p.text}</td></tr>
                    ))}</tbody>
                  </table>
                </Card>
              </div>
            ) : <Empty>Select a cluster.</Empty>}
          </div>
        </>
      )}

    </div>
  )
}
