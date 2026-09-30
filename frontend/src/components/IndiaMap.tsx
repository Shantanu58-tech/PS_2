import { useMemo } from 'react'

/** India as an equal-area tile grid: every state and UT is one tile placed roughly where it
 * sits on the map, so small states stay visible and clickable. (row, col) on an 8×7 grid. */
export const TILES: { code: string; name: string; r: number; c: number }[] = [
  { code: 'JK', name: 'jammu and kashmir', r: 0, c: 2 }, { code: 'LA', name: 'ladakh', r: 0, c: 3 },
  { code: 'CH', name: 'chandigarh', r: 1, c: 0 }, { code: 'PB', name: 'punjab', r: 1, c: 1 },
  { code: 'HP', name: 'himachal pradesh', r: 1, c: 2 }, { code: 'UK', name: 'uttarakhand', r: 1, c: 3 },
  { code: 'RJ', name: 'rajasthan', r: 2, c: 0 }, { code: 'HR', name: 'haryana', r: 2, c: 1 },
  { code: 'DL', name: 'delhi', r: 2, c: 2 }, { code: 'UP', name: 'uttar pradesh', r: 2, c: 3 },
  { code: 'BR', name: 'bihar', r: 2, c: 4 }, { code: 'SK', name: 'sikkim', r: 2, c: 5 },
  { code: 'AS', name: 'assam', r: 2, c: 6 }, { code: 'AR', name: 'arunachal pradesh', r: 2, c: 7 },
  { code: 'GJ', name: 'gujarat', r: 3, c: 0 }, { code: 'MP', name: 'madhya pradesh', r: 3, c: 1 },
  { code: 'CG', name: 'chhattisgarh', r: 3, c: 2 }, { code: 'JH', name: 'jharkhand', r: 3, c: 3 },
  { code: 'WB', name: 'west bengal', r: 3, c: 4 }, { code: 'ML', name: 'meghalaya', r: 3, c: 5 },
  { code: 'NL', name: 'nagaland', r: 3, c: 6 }, { code: 'MN', name: 'manipur', r: 3, c: 7 },
  { code: 'DD', name: 'dadra and nagar haveli and daman and diu', r: 4, c: 0 }, { code: 'MH', name: 'maharashtra', r: 4, c: 1 },
  { code: 'TG', name: 'telangana', r: 4, c: 2 }, { code: 'OD', name: 'odisha', r: 4, c: 3 },
  { code: 'TR', name: 'tripura', r: 4, c: 5 }, { code: 'MZ', name: 'mizoram', r: 4, c: 6 },
  { code: 'GA', name: 'goa', r: 5, c: 0 }, { code: 'KA', name: 'karnataka', r: 5, c: 1 },
  { code: 'AP', name: 'andhra pradesh', r: 5, c: 2 }, { code: 'AN', name: 'andaman and nicobar islands', r: 5, c: 4 },
  { code: 'LD', name: 'lakshadweep', r: 6, c: 0 }, { code: 'KL', name: 'kerala', r: 6, c: 1 },
  { code: 'TN', name: 'tamil nadu', r: 6, c: 2 }, { code: 'PY', name: 'puducherry', r: 6, c: 3 },
]
const ALIAS: Record<string, string> = { jammu: 'jammu and kashmir', kashmir: 'jammu and kashmir', orissa: 'odisha', pondicherry: 'puducherry' }
export const canonState = (s: string) => ALIAS[s] ?? s

export type Metric = 'exposure' | 'anxiety' | 'posts'
// Sequential single-hue ramps (light -> dark), one per metric.
const RAMPS: Record<Metric, [string, string]> = {
  exposure: ['#FBE9E4', '#A1281C'],
  anxiety: ['#FCEFD9', '#A85A12'],
  posts: ['#F1E8DE', '#5F4837'],
}
function mix(a: string, b: string, t: number) {
  const p = (h: string) => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16))
  const [x, y] = [p(a), p(b)]
  return '#' + x.map((v, i) => Math.round(v + (y[i] - v) * t).toString(16).padStart(2, '0')).join('')
}
export const rampCss = (m: Metric) => `linear-gradient(90deg, ${RAMPS[m][0]}, ${RAMPS[m][1]})`

export function valueOf(s: any, m: Metric): number | null {
  if (!s?.released) return null
  return m === 'exposure' ? s.manufactured_share : m === 'anxiety' ? s.anxiety : s.posts
}

export default function IndiaMap({ states, metric, selected, onSelect }: {
  states: any[]; metric: Metric; selected?: string | null; onSelect: (state: string) => void
}) {
  const byName = useMemo(() => {
    const m = new Map<string, any>()
    for (const s of states) m.set(canonState(s.state), s)
    return m
  }, [states])
  const vals = states.map(s => valueOf(s, metric)).filter((v): v is number => v != null)
  const lo = Math.min(...vals), hi = Math.max(...vals)
  const fmt = (v: number) => metric === 'posts' ? (v >= 1000 ? `${(v / 1000).toFixed(1)}k` : String(v))
    : metric === 'exposure' ? `${(v * 100).toFixed(1)}%` : `${Math.round(v * 100)}%`
  return (
    <div className="tilemap" role="group" aria-label="India states" style={{ gridTemplateColumns: 'repeat(8, minmax(0, 1fr))' }}>
      {TILES.map(t => {
        const s = byName.get(t.name)
        const v = valueOf(s, metric)
        const style: React.CSSProperties = { gridRow: t.r + 1, gridColumn: t.c + 1 }
        if (v == null) {
          return <div key={t.code} className="tile nodata" style={style} title={`${t.name}: ${s ? 'withheld (fewer than k accounts)' : 'no data'}`}>{t.code}</div>
        }
        const k = hi > lo ? (v - lo) / (hi - lo) : 0.5
        const bg = mix(RAMPS[metric][0], RAMPS[metric][1], 0.12 + 0.88 * k)
        return (
          <button key={t.code} className={`tile ${selected && canonState(selected) === t.name ? 'sel' : ''}`}
            style={{ ...style, background: bg, color: k > 0.5 ? '#fff' : '#3E342F' }}
            onClick={() => onSelect(s.state)} title={`${t.name} · ${fmt(v)}`} aria-label={`${t.name}: ${fmt(v)}`}>
            {t.code}<small>{fmt(v)}</small>
          </button>
        )
      })}
    </div>
  )
}
