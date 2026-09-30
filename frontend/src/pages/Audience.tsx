import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Lock } from 'lucide-react'
import { useDemographics } from '../hooks/useApi'
import { useAppStore } from '../store/app'
import { Card, ChartOrTable, ChartTip, Empty, InfoPop, NextStep, PageHead } from '../components/ui'
import { AXIS_TICK } from '../lib/viz'
import { num, titleCase } from '../lib/fmt'

const DIM_INFO: Record<string, string> = {
  geography: 'From the location people write on their profile, matched to Indian states and cities.',
  interests: 'From keywords in profile bios (student, tech, media, …).',
  age: 'Estimated from profile bios only ("B.Tech 2nd yr", "retired"). Minors are excluded.',
  language: "The language each account mostly posts in, including Hinglish.",
}
const ORDER = ['geography', 'language', 'interests', 'age']
const LANG: Record<string, string> = { en: 'English', hi: 'Hindi', 'hi-latn': 'Hinglish', 'hi latn': 'Hinglish', mr: 'Marathi', ta: 'Tamil', te: 'Telugu', bn: 'Bengali', ur: 'Urdu' }
const label = (dim: string, b: string) => {
  if (dim === 'language') return LANG[b.toLowerCase()] ?? LANG[b.toLowerCase().replace('_', '-')] ?? 'Other'
  if (dim === 'age') return b.replace('_', '–')
  return titleCase(b)
}

export default function Audience() {
  const { organicOnly } = useAppStore()
  const { data, isFetching } = useDemographics(organicOnly)
  const dims: Record<string, { buckets: { bucket: string; count: number }[]; suppressed_buckets: number }> = data?.dimensions ?? {}
  const keys = ORDER.filter(k => dims[k]).concat(Object.keys(dims).filter(k => !ORDER.includes(k)))

  return (
    <div>
      <PageHead title="Audience" sub={organicOnly ? 'Who is talking, organic accounts only.' : 'Who is talking about it, by region, language and interest.'}
        actions={<span className="badge"><Lock size={12} />Group counts only · no individual profiles
          <InfoPop>Groups smaller than {data?.k_anon ?? 10} accounts are hidden, and counts carry a little random noise so no single person can be singled out.</InfoPop></span>} />
      {keys.length === 0 ? <Empty>No demographic aggregates yet.</Empty> : (
        <div className={`grid g-2 ${isFetching ? 'loading-hold' : ''}`} style={{ alignItems: 'start' }}>
          {keys.map(k => {
            const d = dims[k]
            const merged = new Map<string, number>()
            for (const b of d.buckets) { const n = label(k, b.bucket); merged.set(n, (merged.get(n) ?? 0) + b.count) }
            const rows = [...merged.entries()].map(([name, count]) => ({ name, count })).sort((a, b) => (a.name === 'Unknown' || a.name === 'Other' ? 1 : 0) - (b.name === 'Unknown' || b.name === 'Other' ? 1 : 0) || b.count - a.count)
            const total = rows.reduce((s, r) => s + r.count, 0)
            return (
              <Card key={k} title={titleCase(k)} sub={d.suppressed_buckets > 0 ? `${num(d.suppressed_buckets)} small group${d.suppressed_buckets > 1 ? 's' : ''} hidden for privacy` : undefined}
                actions={<InfoPop>{DIM_INFO[k] ?? ''}</InfoPop>}>
                <ChartOrTable
                  chart={
                    <div style={{ height: Math.max(140, rows.length * 26 + 30) }}>
                      <ResponsiveContainer>
                        <BarChart data={rows} layout="vertical" margin={{ top: 0, right: 16, left: 4, bottom: 0 }} barCategoryGap={4}>
                          <CartesianGrid stroke="var(--hairline)" horizontal={false} />
                          <XAxis type="number" tick={AXIS_TICK} axisLine={false} tickLine={false} />
                          <YAxis type="category" dataKey="name" width={130} tick={{ ...AXIS_TICK, fill: 'var(--ink-2)' }} axisLine={{ stroke: 'var(--axis)' }} tickLine={false} />
                          <Tooltip content={<ChartTip fmtValue={(v: number) => `${num(v)} accounts (${((v / total) * 100).toFixed(1)}%)`} />} cursor={{ fill: 'var(--surface-2)' }} />
                          <Bar dataKey="count" name="Accounts" fill="var(--s1)" radius={[0, 4, 4, 0]} isAnimationActive={false} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  }
                  table={<table className="tbl"><thead><tr><th>Group</th><th className="num">Accounts</th><th className="num">Share</th></tr></thead>
                    <tbody>{rows.map(r => <tr key={r.name}><td>{r.name}</td><td className="num">{num(r.count)}</td><td className="num">{((r.count / total) * 100).toFixed(1)}%</td></tr>)}
                      {d.suppressed_buckets > 0 && <tr><td className="muted">{d.suppressed_buckets} small group(s) hidden</td><td /><td /></tr>}</tbody></table>}
                />
              </Card>
            )
          })}
        </div>
      )}
      <NextStep />
    </div>
  )
}
