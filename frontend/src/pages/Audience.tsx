import { useState } from 'react'
import {
  Bar, BarChart, CartesianGrid, Cell, Label, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { Lock } from 'lucide-react'
import { useDemographics, useTopics } from '../hooks/useApi'
import { useAppStore } from '../store/app'
import IndiaMap from '../components/IndiaMap'
import { Card, ChartOrTable, ChartTip, Empty, InfoPop, NextStep, PageHead } from '../components/ui'
import { AXIS_TICK } from '../lib/viz'
import { istDay, num, titleCase } from '../lib/fmt'

const DIM_INFO: Record<string, string> = {
  geography: 'From the location people write on their profile, matched to Indian states and cities.',
  interests: 'From keywords in profile bios (student, tech, media, …).',
  age: 'Estimated from profile bios only ("B.Tech 2nd yr", "retired"). Minors are excluded.',
  language: 'The language each account mostly posts in, including Hinglish.',
}
const LANG: Record<string, string> = { en: 'English', hi: 'Hindi', 'hi-latn': 'Hinglish', mr: 'Marathi', ta: 'Tamil', te: 'Telugu', bn: 'Bengali', ur: 'Urdu' }
const MIN_POSTS = 60  // a story this size usually has 30+ distinct accounts
const SERIES = ['var(--s1)', 'var(--s2)', 'var(--s3)', 'var(--s4)', 'var(--s5)', 'var(--s7)']
const OTHER_FILL = 'var(--surface-3)'

type Row = { name: string; count: number }
type Dim = { buckets: { bucket: string; count: number }[]; suppressed_buckets: number }

/** Merges buckets that share a display name and splits off the "don't know" group,
 * which is reported as a note instead of competing with real groups in the chart. */
function prepare(dim: string, d?: Dim): { rows: Row[]; unknown: number; total: number } {
  const merged = new Map<string, number>()
  let unknown = 0
  for (const b of d?.buckets ?? []) {
    const key = b.bucket.toLowerCase().replace('_', '-')
    if (key === 'unknown') { unknown += b.count; continue }
    const name = dim === 'language' ? (LANG[key] ?? 'Other') : dim === 'age' ? b.bucket.replace('_', '–').replace('-', '–') : titleCase(b.bucket)
    merged.set(name, (merged.get(name) ?? 0) + b.count)
  }
  let rows = [...merged.entries()].map(([name, count]) => ({ name, count }))
  rows = dim === 'age'
    ? rows.sort((a, b) => parseInt(a.name) - parseInt(b.name))       // natural age order
    : rows.sort((a, b) => (a.name === 'Other' ? 1 : 0) - (b.name === 'Other' ? 1 : 0) || b.count - a.count)
  return { rows, unknown, total: rows.reduce((s, r) => s + r.count, 0) + unknown }
}

const pct = (v: number, t: number) => (t ? `${((v / t) * 100).toFixed(1)}%` : '—')

function Table({ rows, total, unknown, suppressed, unknownLabel }: { rows: Row[]; total: number; unknown: number; suppressed: number; unknownLabel: string }) {
  return (
    <table className="tbl"><thead><tr><th>Group</th><th className="num">Accounts</th><th className="num">Share</th></tr></thead>
      <tbody>{rows.map(r => <tr key={r.name}><td>{r.name}</td><td className="num">{num(r.count)}</td><td className="num">{pct(r.count, total)}</td></tr>)}
        {unknown > 0 && <tr><td className="muted">{unknownLabel}</td><td className="num">{num(unknown)}</td><td className="num">{pct(unknown, total)}</td></tr>}
        {suppressed > 0 && <tr><td className="muted">{suppressed} small group(s) hidden</td><td /><td /></tr>}</tbody></table>
  )
}

function Note({ unknown, total, what, suppressed }: { unknown: number; total: number; what: string; suppressed: number }) {
  const parts = []
  if (unknown > 0) parts.push(`${num(unknown)} accounts (${pct(unknown, total)}) ${what}, so they are not shown.`)
  if (suppressed > 0) parts.push(`${suppressed} small group${suppressed > 1 ? 's' : ''} hidden for privacy.`)
  return parts.length ? <p className="muted small" style={{ margin: '8px 0 0' }}>{parts.join(' ')}</p> : null
}

export default function Audience() {
  const { organicOnly } = useAppStore()
  const { data: topicsData } = useTopics('volume', 60)
  // only stories with enough people to report on (smaller groups would be hidden for privacy anyway);
  // likely coordinated ones first, then by size
  const topics: any[] = (topicsData?.topics ?? topicsData ?? [])
    .filter((t: any) => (t.n_posts ?? 0) >= MIN_POSTS)
    .sort((a: any, b: any) => (b.nature === 'manufactured' ? 1 : 0) - (a.nature === 'manufactured' ? 1 : 0) || b.n_posts - a.n_posts)
    .slice(0, 12)
  const [scope, setScope] = useState('live')
  const { data, isFetching, isPlaceholderData } = useDemographics(organicOnly, scope)
  const switching = isPlaceholderData && isFetching  // still showing the previous selection
  const tooSmall = data && !switching && data.coverage?.accounts == null
  const dims: Record<string, Dim> = data?.dimensions ?? {}
  const cov = data?.coverage
  const geo = prepare('geography', dims.geography)
  const lang = prepare('language', dims.language)
  const age = prepare('age', dims.age)
  const intr = prepare('interests', dims.interests)
  const topicName = topics.find(t => `topic:${t.topic_id}` === scope)?.label

  const subtitle = cov
    ? `Based on ${cov.accounts != null ? `about ${num(cov.accounts)}` : 'fewer than ' + (data?.k_anon ?? 10)} accounts · ${cov.states} state${cov.states === 1 ? '' : 's'}${cov.from ? ` · ${istDay(cov.from)} – ${istDay(cov.to)}` : ''}`
    : 'Counting…'

  return (
    <div>
      <PageHead title="Audience"
        sub={`Who is talking${topicName ? ` about “${topicName}”` : ''}${organicOnly ? ', ordinary accounts only' : ''}. Each account is counted once, not each post.`}
        actions={<span className="badge"><Lock size={12} />Group counts only · no individual profiles
          <InfoPop>Groups smaller than {data?.k_anon ?? 10} accounts are hidden, and counts carry a little random noise so no single person can be singled out.</InfoPop></span>} />

      <div className="card aud-scope">
        <label className="row-wrap" style={{ gap: 10 }}>
          <b>Whose audience?</b>
          <select value={scope} onChange={e => setScope(e.target.value)} aria-label="Audience scope">
            <option value="live">Everyone in the monitored conversation</option>
            {topics.map(t => <option key={t.topic_id} value={`topic:${t.topic_id}`}>{t.nature === 'manufactured' ? '⚠ ' : ''}{t.label} ({num(t.n_posts)} posts)</option>)}
          </select>
        </label>
        <span className="muted" aria-live="polite">{switching ? 'Counting the people in this story…' : subtitle}</span>
      </div>

      {!data ? <Empty>Counting the audience…</Empty> : tooSmall ? (
        <Empty>Fewer than {data.k_anon ?? 10} people took part in this story, too few to describe without risking identifying them. Pick a bigger story.</Empty>
      ) : (
        <div className={`aud-grid ${switching ? 'loading-hold' : ''}`} aria-busy={switching}>
          <Card title="Where they are" sub="Accounts per state, from the location on their profile" actions={<InfoPop>{DIM_INFO.geography}</InfoPop>}>
            <ChartOrTable
              chart={geo.rows.length ? <IndiaMap states={geo.rows.map(r => ({ state: r.name.toLowerCase(), released: true, posts: r.count }))} metric="posts" onSelect={() => {}} />
                : <Empty>No state has enough accounts to report.</Empty>}
              table={<Table {...geo} suppressed={dims.geography?.suppressed_buckets ?? 0} unknownLabel="Location not given" />} />
            <Note unknown={geo.unknown} total={geo.total} what="give no usable location" suppressed={dims.geography?.suppressed_buckets ?? 0} />
          </Card>

          <Card title="Language they post in" sub="Share of accounts by main posting language" actions={<InfoPop>{DIM_INFO.language}</InfoPop>}>
            <ChartOrTable
              chart={
                <div className="aud-donut">
                  <div style={{ height: 220 }}>
                    <ResponsiveContainer>
                      <PieChart>
                        <Pie data={lang.rows} dataKey="count" nameKey="name" innerRadius="58%" outerRadius="88%" paddingAngle={1.5} isAnimationActive={false} stroke="var(--surface-1)">
                          {lang.rows.map((r, i) => <Cell key={r.name} fill={r.name === 'Other' ? OTHER_FILL : SERIES[i % SERIES.length]} />)}
                          <Label position="center" content={() => (
                            <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 13, fill: 'var(--ink-3)' }}>
                              <tspan x="50%" dy="-0.4em" style={{ fontSize: 20, fontWeight: 800, fill: 'var(--ink-1)' }}>{lang.rows[0]?.name ?? ''}</tspan>
                              <tspan x="50%" dy="1.5em">{lang.rows[0] ? pct(lang.rows[0].count, lang.total - lang.unknown) : ''}</tspan>
                            </text>
                          )} />
                        </Pie>
                        <Tooltip content={<ChartTip fmtValue={(v: number) => `${num(v)} accounts (${pct(v, lang.total - lang.unknown)})`} />} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <ul className="aud-legend">
                    {lang.rows.map((r, i) => (
                      <li key={r.name}><i style={{ background: r.name === 'Other' ? OTHER_FILL : SERIES[i % SERIES.length] }} />{r.name}<b>{pct(r.count, lang.total - lang.unknown)}</b></li>
                    ))}
                  </ul>
                </div>
              }
              table={<Table {...lang} suppressed={dims.language?.suppressed_buckets ?? 0} unknownLabel="Language not detected" />} />
            <Note unknown={lang.unknown} total={lang.total} what="had no detectable language" suppressed={dims.language?.suppressed_buckets ?? 0} />
          </Card>

          <Card title="Age group" sub="Only accounts whose bio states an age or year of study" actions={<InfoPop>{DIM_INFO.age}</InfoPop>}>
            <ChartOrTable
              chart={age.rows.length ? (
                <div style={{ height: 230 }}>
                  <ResponsiveContainer>
                    <BarChart data={age.rows} margin={{ top: 8, right: 8, left: 8, bottom: 18 }}>
                      <CartesianGrid stroke="var(--hairline)" vertical={false} />
                      <XAxis dataKey="name" tick={{ ...AXIS_TICK, fill: 'var(--ink-2)' }} axisLine={{ stroke: 'var(--axis)' }} tickLine={false}>
                        <Label value="Age (years)" position="insideBottom" offset={-12} style={{ fontSize: 12, fill: 'var(--ink-3)' }} />
                      </XAxis>
                      <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} width={44}>
                        <Label value="Accounts" angle={-90} position="insideLeft" style={{ fontSize: 12, fill: 'var(--ink-3)', textAnchor: 'middle' }} />
                      </YAxis>
                      <Tooltip content={<ChartTip fmtValue={(v: number) => `${num(v)} accounts`} />} cursor={{ fill: 'var(--surface-2)' }} />
                      <Bar dataKey="count" name="Accounts" fill="var(--s7)" radius={[4, 4, 0, 0]} isAnimationActive={false} maxBarSize={64} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : <Empty>Too few accounts state their age to report any group.</Empty>}
              table={<Table {...age} suppressed={dims.age?.suppressed_buckets ?? 0} unknownLabel="Age not stated" />} />
            <Note unknown={0} total={age.total} what="" suppressed={dims.age?.suppressed_buckets ?? 0} />
          </Card>

          <Card title="Interests" sub="From keywords in profile bios" actions={<InfoPop>{DIM_INFO.interests}</InfoPop>}>
            <ChartOrTable
              chart={
                <div style={{ height: Math.max(160, intr.rows.length * 28 + 40) }}>
                  <ResponsiveContainer>
                    <BarChart data={intr.rows} layout="vertical" margin={{ top: 0, right: 16, left: 4, bottom: 16 }} barCategoryGap={5}>
                      <CartesianGrid stroke="var(--hairline)" horizontal={false} />
                      <XAxis type="number" tick={AXIS_TICK} axisLine={false} tickLine={false}>
                        <Label value="Accounts" position="insideBottom" offset={-10} style={{ fontSize: 12, fill: 'var(--ink-3)' }} />
                      </XAxis>
                      <YAxis type="category" dataKey="name" width={110} tick={{ ...AXIS_TICK, fill: 'var(--ink-2)' }} axisLine={{ stroke: 'var(--axis)' }} tickLine={false} />
                      <Tooltip content={<ChartTip fmtValue={(v: number) => `${num(v)} accounts (${pct(v, intr.total)})`} />} cursor={{ fill: 'var(--surface-2)' }} />
                      <Bar dataKey="count" name="Accounts" radius={[0, 4, 4, 0]} isAnimationActive={false}>
                        {intr.rows.map(r => <Cell key={r.name} fill={r.name === 'Other' ? OTHER_FILL : 'var(--s1)'} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              }
              table={<Table {...intr} suppressed={dims.interests?.suppressed_buckets ?? 0} unknownLabel="No interest keywords" />} />
            <Note unknown={0} total={intr.total} what="" suppressed={dims.interests?.suppressed_buckets ?? 0} />
          </Card>
        </div>
      )}
      <NextStep />
    </div>
  )
}
