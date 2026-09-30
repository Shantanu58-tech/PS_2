import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ArrowRight, Clock, Copy, Gauge, MessageSquare, Users } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useCluster, useClusters } from '../hooks/useApi'
import { Card, ChartOrTable, ChartTip, Empty, InfoPop, Kpi, Legend, Loading, Meter, NextStep, PageHead, StatusBadge } from '../components/ui'
import { AXIS_TICK, PLATFORM_LABEL, RAW } from '../lib/viz'
import { ist, istShort, num, pct } from '../lib/fmt'

const FLAGGED = 'var(--critical)'

// Each signal is shown as a 0–1 strength pointing toward "more scripted".
const SIGNALS: { key: string; label: string; strength: (v: number) => number; help: string }[] = [
  { key: 'sync', label: 'Posting in sync', strength: v => v, help: 'How often a post is followed by another account\'s post within a minute.' },
  { key: 'hn', label: 'Predictable timing', strength: v => 1 - v, help: 'Scheduled posting leaves very regular gaps between posts; people do not.' },
  { key: 'burstiness', label: 'Clock-like rhythm', strength: v => (1 - v) / 2, help: 'People post in irregular bursts; scripts post at a steady beat.' },
  { key: 'dup_ratio', label: 'Copy-paste text', strength: v => v, help: 'Share of posts with a near-identical copy written by a different account.' },
  { key: 'regular_share', label: 'Machine-regular accounts', strength: v => v, help: 'Share of posts from accounts whose own posting rhythm is machine-regular.' },
]

/** One row per account, one tick per post: coordinated accounts line up vertically. */
function Fingerprint({ fp }: { fp: any }) {
  const t0 = new Date(fp.start).getTime() - 5 * 60_000
  const t1 = new Date(fp.end).getTime() + 5 * 60_000
  const x = (iso: string) => ((new Date(iso).getTime() - t0) / Math.max(1, t1 - t0)) * 100
  const inRange = (iso: string) => { const v = new Date(iso).getTime(); return v >= t0 && v <= t1 }
  const Row = ({ r, color }: { r: any; color: string }) => (
    <div className="fp-row">
      <span className="fp-name">@{r.account_id}</span>
      <div className="fp-track">
        {r.times.filter(inRange).map((t: string, i: number) => (
          <span key={i} className="fp-tick" style={{ left: `${x(t)}%`, background: color }} title={ist(t)} />
        ))}
      </div>
    </div>
  )
  const organicInWindow = fp.organic.filter((r: any) => r.times.some(inRange))
  return (
    <div>
      <div className="fp-group-label" style={{ color: 'var(--critical)' }}>Accounts in this group</div>
      {fp.flagged.map((r: any) => <Row key={r.account_id} r={r} color={FLAGGED} />)}
      {organicInWindow.length > 0 && <>
        <div className="fp-group-label" style={{ marginTop: 12 }}>Ordinary accounts on the same topic, same window</div>
        {organicInWindow.map((r: any) => <Row key={r.account_id} r={r} color="var(--neutral-series)" />)}
      </>}
      <div className="spread muted" style={{ fontSize: 11.5, marginTop: 6, paddingLeft: 150 }}>
        <span>{istShort(new Date(t0).toISOString())}</span><span>{istShort(new Date(t1).toISOString())}</span>
      </div>
    </div>
  )
}

export default function Coordination() {
  const { data } = useClusters()
  const clusters: any[] = data?.clusters ?? []
  const [params] = useSearchParams()
  const [sel, setSel] = useState<number | undefined>()
  const [showAll, setShowAll] = useState(false)
  useEffect(() => {
    if (!clusters.length) return
    const t = params.get('topic')
    const byTopic = t ? clusters.find(c => String(c.topic_id) === t) : undefined
    if (byTopic) setSel(byTopic.cluster_id)
    else if (sel == null) setSel(clusters[0].cluster_id)
  }, [clusters, params]) // eslint-disable-line react-hooks/exhaustive-deps
  const { data: detail, isLoading } = useCluster(sel)
  const c = detail?.cluster
  const accounts: any[] = detail?.accounts ?? []
  const flagged = accounts.filter(a => a.score >= 0.7)
  const fp = detail?.fingerprint
  const cmp = fp?.compare
  const spanMin = useMemo(() => fp?.start ? Math.round((new Date(fp.end).getTime() - new Date(fp.start).getTime()) / 60000) : null, [fp])

  return (
    <div>
      <PageHead title="Coordination" sub="Groups of accounts posting the same thing at the same time, and the evidence that it is not natural." />
      {clusters.length === 0 ? <Empty>No coordinated groups found.</Empty> : (
        <>
          {clusters.length > 1 && (
            <div className="row-wrap" style={{ marginBottom: 16 }} role="tablist" aria-label="Coordinated groups">
              {clusters.map(cl => (
                <button key={cl.cluster_id} role="tab" aria-selected={sel === cl.cluster_id} className="btn btn-sm" onClick={() => setSel(cl.cluster_id)}
                  style={sel === cl.cluster_id ? { background: 'var(--accent-soft)', borderColor: 'var(--accent)', color: 'var(--accent-ink)' } : undefined}>
                  {cl.topic_label ?? `Group ${cl.cluster_id}`} · {num(cl.n_accounts ?? cl.n_coordinated)} accounts
                </button>
              ))}
            </div>
          )}
          {!c ? <Loading label="Loading the group" /> : (
            <>
              <div className="grid g-4" style={{ marginBottom: 20 }}>
                <Kpi icon={<Users size={20} />} label="Accounts in the group" value={num(accounts.length)} foot={`${num(flagged.length)} of them score as strongly in sync`} />
                <Kpi icon={<Gauge size={20} />} label="Coordination score" value={`${Math.round(c.score * 100)}%`} foot="how scripted the group's posting looks" />
                <Kpi icon={<MessageSquare size={20} />} label="Posts by this group" value={num(c.n_posts)} foot={c.topic_label ? <span>on “{c.topic_label}”</span> : ''} />
                <Kpi icon={<Clock size={20} />} label="All within" value={spanMin != null ? `${spanMin} min` : '—'} foot={fp?.start ? `from ${istShort(fp.start)}` : ''} />
              </div>

              <div className="grid g-2" style={{ alignItems: 'start' }}>
                <Card title="Why this group was flagged" sub="a signal for review, not an accusation">
                  <table className="tbl">
                    <tbody>{SIGNALS.map(s => (
                      <tr key={s.key}>
                        <td style={{ width: '42%' }}>{s.label} <InfoPop>{s.help}</InfoPop></td>
                        <td>{c[s.key] != null && <Meter value={s.strength(c[s.key])} color="var(--serious)" label={s.label} />}</td>
                        <td className="num" style={{ width: 60 }}>{c[s.key] != null ? pct(Math.max(0, Math.min(1, s.strength(c[s.key]))), 0) : '—'}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                </Card>
                <Card title="Compared with ordinary users" sub="same topic, same time window">
                  {cmp ? (
                    <table className="tbl">
                      <thead><tr><th /><th className="num" style={{ color: 'var(--critical)' }}>This group</th><th className="num">Ordinary users</th></tr></thead>
                      <tbody>
                        <tr><td>Posts landing within a minute of another account</td><td className="num"><b>{pct(cmp.flagged.within_minute, 0)}</b></td><td className="num">{pct(cmp.organic.within_minute, 0)}</td></tr>
                        <tr><td>Typical gap between one account's posts</td><td className="num"><b>{cmp.flagged.median_gap_s != null ? `${cmp.flagged.median_gap_s} s` : '—'}</b></td><td className="num">{cmp.organic.median_gap_s != null ? `${Math.round(cmp.organic.median_gap_s / 60)} min` : 'one post each'}</td></tr>
                        <tr><td>Posts per account</td><td className="num"><b>{(cmp.flagged.posts / Math.max(1, cmp.flagged.accounts)).toFixed(1)}</b></td><td className="num">{(cmp.organic.posts / Math.max(1, cmp.organic.accounts)).toFixed(1)}</td></tr>
                        <tr><td>Copy-paste text</td><td className="num"><b>{pct(c.dup_ratio, 0)}</b></td><td className="num">—</td></tr>
                      </tbody>
                    </table>
                  ) : <Loading />}
                  <p className="muted" style={{ fontSize: 12.5, margin: '10px 0 0' }}>Real people react at their own pace. A script fires on a timer, from many accounts at once.</p>
                </Card>
              </div>

              <Card title="Synchrony fingerprint" style={{ marginTop: 18 }}
                sub="one row per account, one tick per post. Ticks lining up vertically mean accounts posting in lock-step."
                actions={<InfoPop>The group's accounts post within seconds of each other, again and again. Ordinary accounts posting on the same topic at the same time are scattered.</InfoPop>}>
                {fp?.flagged?.length ? <Fingerprint fp={fp} /> : isLoading ? <Loading /> : <Empty>No timing data.</Empty>}
              </Card>

              <Card title="Posting timeline" sub="posts per minute on this topic: accounts in sync vs everyone else" style={{ marginTop: 18 }}>
                <ChartOrTable
                  chart={<>
                    <Legend items={[{ label: 'Accounts in sync', color: FLAGGED }, { label: 'Everyone else', color: RAW }]} />
                    <div style={{ height: 220, marginTop: 8 }}>
                      <ResponsiveContainer>
                        <BarChart data={detail?.timing ?? []} margin={{ top: 6, right: 8, left: 0, bottom: 0 }} barCategoryGap={1}>
                          <CartesianGrid stroke="var(--hairline)" vertical={false} />
                          <XAxis dataKey="minute" tick={AXIS_TICK} tickFormatter={v => istShort(v).slice(-5)} minTickGap={36} axisLine={{ stroke: 'var(--axis)' }} tickLine={false} />
                          <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} allowDecimals={false} width={32} label={{ value: 'posts / min', angle: -90, position: 'insideLeft', fill: 'var(--ink-3)', fontSize: 11 }} />
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

              <div className="grid g-2" style={{ marginTop: 18, alignItems: 'start' }}>
                <Card title="Accounts" sub={`${num(accounts.length)} accounts · click one to see it in the network`}>
                  <table className="tbl">
                    <thead><tr><th>Account</th><th /><th className="num">Score</th><th className="num">Posts</th></tr></thead>
                    <tbody>{(showAll ? accounts : accounts.slice(0, 10)).map(a => (
                      <tr key={a.account_id}>
                        <td><Link to={`/network?account=${encodeURIComponent(a.account_id)}`}>@{a.account_id}</Link>
                          <div className="muted" style={{ fontSize: 12 }}>{String(a.platforms).split(',').filter((v, i, arr) => arr.indexOf(v) === i).map((p: string) => PLATFORM_LABEL[p] ?? p).join(', ')}</div></td>
                        <td>{a.score >= 0.7 ? <StatusBadge status="critical">In sync</StatusBadge> : null}</td>
                        <td className="num">{Math.round(a.score * 100)}%</td>
                        <td className="num">{a.reasons?.n_posts ?? '—'}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                  {accounts.length > 10 && <button className="btn btn-sm btn-ghost" style={{ marginTop: 8 }} onClick={() => setShowAll(!showAll)}>{showAll ? 'Show fewer' : `Show all ${accounts.length}`}</button>}
                </Card>
                <Card title="Sample posts" sub="from accounts in sync" actions={<Copy size={15} color="var(--ink-3)" />}>
                  <div className="stack" style={{ gap: 0 }}>
                    {(detail?.evidence_posts ?? []).slice(0, 8).map((p: any) => (
                      <div key={p.platform + p.post_id} style={{ padding: '9px 0', borderBottom: '1px solid var(--hairline)' }}>
                        <div style={{ fontSize: 13.5 }}>{p.text}</div>
                        <div className="muted" style={{ fontSize: 12 }}>@{p.author_id} · {PLATFORM_LABEL[p.platform] ?? p.platform} · {istShort(p.created_at)}</div>
                      </div>
                    ))}
                  </div>
                  <Link className="btn btn-sm" style={{ marginTop: 10 }} to="/network">See this group in the network<ArrowRight size={13} /></Link>
                </Card>
              </div>
            </>
          )}
        </>
      )}
      <NextStep />
    </div>
  )
}
