import { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useBehaviour, useCluster, useClusters } from '../hooks/useApi'
import { Card, ChartOrTable, ChartTip, Empty, InfoPop, Kpi, Legend, Meter, PageHead, StatusBadge } from '../components/ui'
import { AXIS_TICK, PLATFORM_LABEL, RAW } from '../lib/viz'
import { ist, istShort, num, pct } from '../lib/fmt'

const FLAGGED = 'var(--critical)'

const SIGNALS: { key: string; label: string; fmt: (v: number) => string; help: string }[] = [
  { key: 'sync', label: 'Synchrony S', fmt: v => v.toFixed(2), help: 'Share of posts followed by another post within 60 s.' },
  { key: 'hn', label: 'Normalised entropy Hn', fmt: v => v.toFixed(2), help: 'Entropy of inter-post gaps over 12 log-spaced bins (1 s–24 h), divided by log₂12. Low = gaps concentrated at a few scales (scheduled).' },
  { key: 'burstiness', label: 'Burstiness B', fmt: v => v.toFixed(2), help: 'Goh–Barabási B = (σ−μ)/(σ+μ) of the gaps: −1 clock-like, 0 random, +1 very bursty.' },
  { key: 'dup_ratio', label: 'Cross-account duplicates', fmt: v => pct(v), help: 'Share of posts with a near-duplicate (cosine ≥ 0.90) written by a different account.' },
  { key: 'regular_share', label: 'Scripted-cadence share', fmt: v => pct(v), help: "Share of posts from accounts whose own gaps are regular (B ≤ −0.5)." },
]

export default function Coordination() {
  const { data } = useClusters()
  const clusters: any[] = data?.clusters ?? []
  const [sel, setSel] = useState<number | undefined>()
  useEffect(() => { if (sel == null && clusters.length) setSel(clusters[0].cluster_id) }, [clusters, sel])
  const { data: detail } = useCluster(sel)
  const { data: beh } = useBehaviour()
  const c = detail?.cluster
  const accounts: any[] = detail?.accounts ?? []
  const flagged = accounts.filter(a => a.score >= 0.7)

  return (
    <div>
      <PageHead code="V2" title="Coordination detector"
        sub="Narrative clusters are posts linked by near-identical text (same hour), a shared hashtag (same 30 minutes) or a repost chain. Clusters that look scripted are scored; each account inside is then scored on its own behaviour." />
      <div className="notice" style={{ marginBottom: 16 }}>
        Wording is deliberate: <b style={{ color: 'var(--ink-1)' }}>behaviour consistent with scripted amplification</b>. This is a statistical signal for analyst review, not an accusation, and never a "bot" label. Legitimate fan clubs or news desks can look coordinated.
      </div>
      {clusters.length === 0 ? <Empty>No coordinated clusters detected.</Empty> : (
        <>
          <div className="grid g-4" style={{ marginBottom: 16 }}>
            <Kpi label="Clusters flagged" value={num(clusters.length)} foot="cluster score ≥ 0.70" />
            <Kpi label="Accounts flagged in this cluster" value={num(flagged.length)} foot={`of ${num(accounts.length)} participating`} />
            <Kpi label="Cluster score" value={c ? c.score.toFixed(2) : '—'} foot={c?.topic_label ? `topic: ${c.topic_label}` : ''}
              info={<>score = σ(2·S + 2·(1−Hn) + 1·max(0,−B) + 1.5·dup + 3·scripted − 4). Weights were set on scenario seed 7 and evaluated on held-out seed 11.</>} />
            <Kpi label="Posts in cluster" value={num(c?.n_posts)} foot={c ? `${num(c.n_accounts)} accounts` : ''} />
          </div>

          <div className="grid" style={{ gridTemplateColumns: 'minmax(220px, 300px) minmax(0, 1fr)' }}>
            <Card title="Clusters">
              <div className="stack" style={{ gap: 4 }}>
                {clusters.map(cl => (
                  <button key={cl.cluster_id} className="btn btn-ghost" onClick={() => setSel(cl.cluster_id)}
                    style={{ justifyContent: 'space-between', background: sel === cl.cluster_id ? 'var(--surface-2)' : undefined, boxShadow: sel === cl.cluster_id ? 'inset 2px 0 0 var(--critical)' : undefined }}>
                    <span style={{ textAlign: 'left' }}>#{cl.cluster_id} {cl.topic_label ?? ''}<div className="muted" style={{ fontSize: 11 }}>{num(cl.n_coordinated)} flagged · {num(cl.n_posts)} posts</div></span>
                    <span className="tnum">{cl.score.toFixed(2)}</span>
                  </button>
                ))}
              </div>
            </Card>

            {c ? (
              <div className="stack">
                <Card title="Why this cluster was flagged" sub="the five signals behind the cluster score">
                  <table className="tbl">
                    <tbody>{SIGNALS.map(s => (
                      <tr key={s.key}>
                        <td style={{ width: '40%' }}>{s.label} <InfoPop>{s.help}</InfoPop></td>
                        <td className="num" style={{ width: 90 }}>{c[s.key] != null ? s.fmt(c[s.key]) : '—'}</td>
                        <td>{c[s.key] != null && <Meter value={s.key === 'burstiness' ? (1 - c[s.key]) / 2 : s.key === 'hn' ? 1 - c[s.key] : c[s.key]} color="var(--serious)" label={s.label} />}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                  <div className="muted" style={{ fontSize: 12, marginTop: 6 }}>Meters point toward "more scripted" (entropy and burstiness are inverted).</div>
                </Card>

                <Card title="Timing" sub="posts per minute in the cluster's topic: flagged accounts vs everyone else">
                  <ChartOrTable
                    chart={<>
                      <Legend items={[{ label: 'Flagged accounts', color: FLAGGED }, { label: 'Other accounts', color: RAW }]} />
                      <div style={{ height: 200, marginTop: 8 }}>
                        <ResponsiveContainer>
                          <BarChart data={detail?.timing ?? []} margin={{ top: 6, right: 8, left: 0, bottom: 0 }} barCategoryGap={1}>
                            <CartesianGrid stroke="var(--hairline)" vertical={false} />
                            <XAxis dataKey="minute" tick={AXIS_TICK} tickFormatter={v => istShort(v).slice(-5)} minTickGap={36} axisLine={{ stroke: 'var(--axis)' }} tickLine={false} />
                            <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} allowDecimals={false} width={32} />
                            <Tooltip content={<ChartTip fmtLabel={(l: string) => ist(l)} />} cursor={{ fill: 'var(--surface-2)' }} />
                            <Bar dataKey="coordinated" name="Flagged" stackId="a" fill={FLAGGED} isAnimationActive={false} />
                            <Bar dataKey="other" name="Other" stackId="a" fill={RAW} radius={[4, 4, 0, 0]} isAnimationActive={false} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </>}
                    table={<table className="tbl"><thead><tr><th>Minute (IST)</th><th className="num">Flagged</th><th className="num">Other</th></tr></thead>
                      <tbody>{(detail?.timing ?? []).map((r: any) => <tr key={r.minute}><td>{ist(r.minute)}</td><td className="num">{r.coordinated}</td><td className="num">{r.other}</td></tr>)}</tbody></table>} />
                </Card>

                <Card title="Accounts" sub="per-account score and the behaviour behind it">
                  <div className="table-wrap" style={{ maxHeight: 360, overflowY: 'auto' }}>
                    <table className="tbl">
                      <thead><tr><th>Account</th><th>Status</th><th className="num">Score</th><th className="num">Co-posting</th><th className="num">Regularity</th><th className="num">Posts</th></tr></thead>
                      <tbody>{accounts.map(a => (
                        <tr key={a.account_id}>
                          <td className="mono" style={{ fontSize: 12 }}>{a.account_id}<div className="muted" style={{ fontSize: 11 }}>{String(a.platforms).split(',').map((p: string) => PLATFORM_LABEL[p] ?? p).join(', ')}</div></td>
                          <td>{a.score >= 0.7 ? <StatusBadge status="critical">Scripted pattern</StatusBadge> : <span className="muted">below threshold</span>}</td>
                          <td className="num">{a.score.toFixed(2)}</td>
                          <td className="num">{pct(a.reasons?.co_sync)}</td>
                          <td className="num">{a.reasons?.regularity?.toFixed(2) ?? '—'}</td>
                          <td className="num">{a.reasons?.n_posts ?? '—'}</td>
                        </tr>
                      ))}</tbody>
                    </table>
                  </div>
                </Card>

                <Card title="Evidence posts" sub="from flagged accounts, with their ledger sequence numbers">
                  <table className="tbl">
                    <thead><tr><th>Time (IST)</th><th>Account</th><th>Text</th><th className="num">Ledger seq</th></tr></thead>
                    <tbody>{(detail?.evidence_posts ?? []).slice(0, 12).map((p: any) => (
                      <tr key={p.platform + p.post_id}><td style={{ whiteSpace: 'nowrap' }}>{istShort(p.created_at)}</td><td className="mono" style={{ fontSize: 12 }}>{p.author_id}</td><td>{p.text}</td><td className="num mono">{p.ledger_seq}</td></tr>
                    ))}</tbody>
                  </table>
                </Card>
              </div>
            ) : <Empty>Select a cluster.</Empty>}
          </div>
        </>
      )}

      <Card title="Experimental behaviour likelihood" sub={beh?.caveat} style={{ marginTop: 16 }}>
        <table className="tbl">
          <thead><tr><th>Account</th><th className="num">Likelihood</th><th className="num">Regularity</th><th className="num">Template reuse</th><th className="num">Night share</th><th className="num">Posts</th></tr></thead>
          <tbody>{(beh?.accounts ?? []).slice(0, 12).map((a: any) => (
            <tr key={a.platform + a.account_id}>
              <td className="mono" style={{ fontSize: 12 }}>{a.account_id}</td>
              <td className="num">{a.likelihood.toFixed(2)}</td>
              <td className="num">{a.features?.regularity?.toFixed(2)}</td>
              <td className="num">{pct(a.features?.template)}</td>
              <td className="num">{pct(a.features?.night_share)}</td>
              <td className="num">{a.features?.n_posts}</td>
            </tr>
          ))}</tbody>
        </table>
      </Card>
    </div>
  )
}
