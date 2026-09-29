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
                {i === 0 ? 'earliest observed' : `+${minutesBetween(plats[0].first_seen, p.first_seen)} min`} · {num(p.n_posts)} posts{p.has_media ? ' · image' : ''}
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
      <PageHead code="V3" title="Narrative lineage"
        sub="Where a narrative was first seen and how it moved across platforms: text-claim clustering, repost and forward chains (Telegram forward headers), and perceptual image hashing." />
      {topics.length === 0 ? <Empty>No lineage yet.</Empty> : (
        <div className="stack">
          <div className="row-wrap">
            <Seg label="Narrative" value={sel} onChange={setSel}
              options={topics.slice(0, 4).map(t => ({ value: String(t.topic_id), label: t.label }))} />
          </div>
          {lin && (
            <div className="grid g-main">
              <Card title={lin.label} sub={`${num(lin.n_posts)} posts · ${pct(lin.coordinated_share)} from coordinated accounts`}
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
                <p className="muted" style={{ fontSize: 12, marginTop: 10, fontStyle: 'italic' }}>{lin.caveat}</p>
              </Card>
              <Card title="Origin candidate" sub={ist(lin.earliest_observed)}>
                {lin.origin_candidate && (
                  <div className="stack" style={{ gap: 8 }}>
                    <span className="badge"><span className="dot" style={{ background: PLATFORM_SLOT[lin.origin_candidate.platform] }} />{PLATFORM_LABEL[lin.origin_candidate.platform]}</span>
                    <blockquote style={{ margin: 0, paddingLeft: 12, borderLeft: '2px solid var(--axis)', color: 'var(--ink-1)' }}>{lin.origin_candidate.text}</blockquote>
                    <div className="muted mono" style={{ fontSize: 12 }}>{lin.origin_candidate.first_post_id} · author {lin.origin_candidate.author_id}</div>
                    <div className="muted" style={{ fontSize: 12 }}>{num((lin.chains ?? []).length)} explicit repost/forward links traced from here.</div>
                  </div>
                )}
              </Card>
            </div>
          )}
          <Card title="Image variants" sub="perceptual hash (pHash) matches: same picture after re-encoding, cropping or watermarking"
            actions={<InfoPop>64-bit pHash; a match is a Hamming distance ≤ threshold. On our 200-image transformation suite the chosen threshold gives the recall and false-positive rate shown on the PS 26152 &amp; Eval page.</InfoPop>}>
            {images.length === 0 ? <Empty>No image matches.</Empty> : (
              <table className="tbl">
                <thead><tr><th>First seen</th><th /><th>Variant</th><th className="num">Hamming</th><th className="num">Posts</th></tr></thead>
                <tbody>{images.map((m, i) => (
                  <tr key={i}>
                    <td><span className="row"><ImageIcon size={14} /><span className="mono" style={{ fontSize: 12 }}>{m.media_id_a}</span></span><div className="muted" style={{ fontSize: 11 }}>{PLATFORM_LABEL[m.platform_a]} · {ist(m.first_seen_a)}</div></td>
                    <td><ArrowRight size={14} /></td>
                    <td><span className="mono" style={{ fontSize: 12 }}>{m.media_id_b}</span><div className="muted" style={{ fontSize: 11 }}>{PLATFORM_LABEL[m.platform_b]} · {ist(m.first_seen_b)}</div></td>
                    <td className="num">{m.hamming} / {m.threshold}</td>
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
