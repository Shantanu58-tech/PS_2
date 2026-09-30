import { useEffect, useState } from 'react'
import { ArrowRight, ImageIcon } from 'lucide-react'
import { useLineage } from '../hooks/useApi'
import { Card, Empty, InfoPop, PageHead, Seg, StatusBadge } from '../components/ui'
import { PLATFORM_LABEL, PLATFORM_SLOT } from '../lib/viz'
import { ist, minutesBetween, num, pct } from '../lib/fmt'

function Swimlanes({ lin }: { lin: any }) {
  const plats: any[] = lin.platforms ?? []
  const t0 = plats.length ? new Date(plats[0].first_seen).getTime() : 0
  const t1 = plats.length ? Math.max(...plats.map(p => new Date(p.first_seen).getTime())) : 0
  const span = Math.max(1, t1 - t0)
  return (
    <div className="stack" style={{ gap: 6 }}>
      {plats.map((p, i) => {
        const x = 4 + 88 * ((new Date(p.first_seen).getTime() - t0) / span)
        return (
          <div key={p.platform} className="lane">
            <span className="row" style={{ fontSize: 13 }}>
              <span style={{ width: 10, height: 10, borderRadius: 3, background: PLATFORM_SLOT[p.platform] ?? 'var(--ink-3)', display: 'inline-block' }} />
              {PLATFORM_LABEL[p.platform] ?? p.platform}
            </span>
            <div className="lane-track">
              <span className="lane-dot" style={{ left: `${x}%`, background: PLATFORM_SLOT[p.platform] ?? 'var(--ink-3)' }} title={ist(p.first_seen)} />
              <span className="muted" style={{ position: 'absolute', ...(x > 50 ? { right: `calc(${100 - x}% + 12px)` } : { left: `calc(${x}% + 12px)` }), top: 4, fontSize: 12, whiteSpace: 'nowrap' }}>
                {i === 0 ? 'first seen' : `+${minutesBetween(plats[0].first_seen, p.first_seen)} min`} · {num(p.n_posts)} post{p.n_posts === 1 ? '' : 's'}
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default function Lineage() {
  const { data } = useLineage()
  const topics: any[] = data?.topics ?? []
  const images: any[] = data?.image_matches ?? []
  const [sel, setSel] = useState<string>('')
  useEffect(() => { if (!sel && topics.length) setSel(String(topics[0].topic_id)) }, [topics, sel])
  const lin = topics.find(t => String(t.topic_id) === sel)

  return (
    <div>
      <PageHead title="Lineage" sub="Where a story started and how it moved across platforms." />
      {topics.length === 0 ? <Empty>No lineage yet.</Empty> : (
        <div className="stack">
          <div className="row-wrap">
            <Seg label="Narrative" value={sel} onChange={setSel}
              options={topics.slice(0, 4).map(t => ({ value: String(t.topic_id), label: <span style={{ textTransform: 'capitalize' }}>{t.label}</span> }))} />
          </div>
          {lin && (
            <div className="grid g-main">
              <Card title={<span style={{ textTransform: 'capitalize' }}>{lin.label}</span>} sub={`${num(lin.n_posts)} posts · ${pct(lin.coordinated_share)} from coordinated accounts`}
                actions={lin.nature === 'manufactured' ? <StatusBadge status="critical">Manufactured</StatusBadge> : <StatusBadge status="good">Organic</StatusBadge>}>
                <Swimlanes lin={lin} />
                <div className="divider" />
                <div className="row-wrap" style={{ fontSize: 13 }}>
                  {(lin.hops ?? []).map((h: any, i: number) => (
                    <span key={i} className="row">
                      <span className="chip">{PLATFORM_LABEL[h.from] ?? h.from}</span><ArrowRight size={13} /><span className="chip">{PLATFORM_LABEL[h.to] ?? h.to}</span>
                      <span className="muted">in {minutesBetween(h.from_ts, h.to_ts)} min</span>
                    </span>
                  ))}
                </div>
              </Card>
              <Card title="First seen" sub={ist(lin.earliest_observed)}>
                {lin.origin_candidate && (
                  <div className="stack" style={{ gap: 8 }}>
                    <span className="badge"><span className="dot" style={{ background: PLATFORM_SLOT[lin.origin_candidate.platform] }} />{PLATFORM_LABEL[lin.origin_candidate.platform]}</span>
                    <blockquote style={{ margin: 0, padding: '10px 14px', borderRadius: 12, background: 'var(--surface-2)', color: 'var(--ink-1)' }}>{lin.origin_candidate.text}</blockquote>
                    <div className="muted" style={{ fontSize: 12.5 }}>by @{lin.origin_candidate.author_id} · {num((lin.chains ?? []).length)} reposts and forwards traced from here</div>
                  </div>
                )}
              </Card>
            </div>
          )}
          <Card title="Image copies" sub="the same picture found again after cropping, re-compressing or watermarking"
            actions={<InfoPop>Each image gets a visual fingerprint. Two images match when their fingerprints are nearly identical, even after edits.</InfoPop>}>
            {images.length === 0 ? <Empty>No image matches.</Empty> : (
              <table className="tbl">
                <thead><tr><th>Original</th><th /><th>Copy</th><th className="num">Similarity</th><th className="num">Posts</th></tr></thead>
                <tbody>{images.map((m, i) => (
                  <tr key={i}>
                    <td><span className="row"><ImageIcon size={14} />{PLATFORM_LABEL[m.platform_a]}</span><div className="muted" style={{ fontSize: 12 }}>{ist(m.first_seen_a)}</div></td>
                    <td><ArrowRight size={14} /></td>
                    <td>{PLATFORM_LABEL[m.platform_b]}<div className="muted" style={{ fontSize: 12 }}>{ist(m.first_seen_b)}</div></td>
                    <td className="num">{Math.round((1 - m.hamming / 64) * 100)}%</td>
                    <td className="num">{m.posts_b}</td>
                  </tr>
                ))}</tbody>
              </table>
            )}
          </Card>
        </div>
      )}
    </div>
  )
}
