import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Lock } from 'lucide-react'
import { useDemographics } from '../hooks/useApi'
import { useAppStore } from '../store/app'
import { Card, ChartOrTable, ChartTip, Empty, InfoPop, PageHead } from '../components/ui'
import { AXIS_TICK } from '../lib/viz'
import { ist, num, titleCase } from '../lib/fmt'

const DIM_INFO: Record<string, string> = {
  geography: 'Whole-word match of location text against a 36-state/UT gazetteer (cities and aliases). "Unknown" = no match.',
  interests: 'Keyword taxonomy over profile bios (student, IT/tech, journalist/media, …).',
  age: 'Experimental: bio cues only ("B.Tech 2nd yr", "retired", "born 1990"). Minors are excluded. Low coverage.',
  language: "Each account's dominant post language (script rules + Hinglish lexicon + langdetect).",
}
const ORDER = ['geography', 'language', 'interests', 'age']

export default function Audience() {
  const { organicOnly } = useAppStore()
  const { data, isFetching } = useDemographics(organicOnly)
  const dims: Record<string, { buckets: { bucket: string; count: number }[]; suppressed_buckets: number }> = data?.dimensions ?? {}
  const keys = ORDER.filter(k => dims[k]).concat(Object.keys(dims).filter(k => !ORDER.includes(k)))

  return (
    <div>
      <PageHead code="PS · C" title="Audience (aggregate only)"
        sub={organicOnly ? 'Cohort estimates for organic accounts only (coordinated accounts removed).' : 'Cohort estimates for every account in the dataset.'} />
      <div className="notice" style={{ marginBottom: 16 }}>
        <span className="row"><Lock size={14} /><b style={{ color: 'var(--ink-1)' }}>Privacy by design.</b></span>
        Only cohort counts leave the server. Any bucket with fewer than k = {data?.k_anon ?? 10} accounts is withheld.
        Released counts carry Laplace noise (ε = {data?.dp_epsilon ?? 1}) and are floored at k. No endpoint returns an individual's inferred attributes.
        {data?.computed_at && <span className="muted"> Computed {ist(data.computed_at)}.</span>}
      </div>
      {keys.length === 0 ? <Empty>No demographic aggregates yet.</Empty> : (
        <div className={`grid g-2 ${isFetching ? 'loading-hold' : ''}`}>
          {keys.map(k => {
            const d = dims[k]
            const rows = d.buckets.map(b => ({ name: titleCase(b.bucket), count: b.count }))
            const total = rows.reduce((s, r) => s + r.count, 0)
            return (
              <Card key={k} title={titleCase(k)} sub={`${num(rows.length)} released buckets · ${num(d.suppressed_buckets)} withheld (< k)`}
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
                  table={<table className="tbl"><thead><tr><th>Bucket</th><th className="num">Accounts (noised)</th><th className="num">Share</th></tr></thead>
                    <tbody>{rows.map(r => <tr key={r.name}><td>{r.name}</td><td className="num">{num(r.count)}</td><td className="num">{((r.count / total) * 100).toFixed(1)}%</td></tr>)}
                      {d.suppressed_buckets > 0 && <tr><td className="muted">{d.suppressed_buckets} bucket(s) withheld</td><td className="num muted">&lt; k</td><td /></tr>}</tbody></table>}
                />
              </Card>
            )
          })}
        </div>
      )}
      <p className="muted" style={{ fontSize: 12, marginTop: 12 }}>{data?.method}</p>
    </div>
  )
}
