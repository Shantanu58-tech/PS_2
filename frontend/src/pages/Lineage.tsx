import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { API, useLineage, useSituation } from '../hooks/useApi'
import { Card, Empty, InfoPop, NextStep, PageHead, Seg, StatusBadge } from '../components/ui'
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

const STANCE: { key: string; label: string; color: string; help: string }[] = [
  { key: 'spreading', label: 'Spreading it', color: 'var(--s8)', help: 'repeats or forwards the claim' },
  { key: 'questioning', label: 'Questioning it', color: 'var(--s4)', help: 'asks whether it is true' },
  { key: 'debunking', label: 'Debunking it', color: 'var(--s3)', help: 'says it is false or cites an official denial' },
  { key: 'reacting', label: 'Just reacting', color: 'var(--surface-3)', help: 'an emotion with no position' },
]

/** How the posts on this story relate to the claim. Only "spreading" posts are traced as spread. */
function StanceBar({ counts }: { counts?: Record<string, number> }) {
  if (!counts) return null
  const total = Object.values(counts).reduce((a, b) => a + b, 0)
  if (!total) return null
  return (
    <div className="stack" style={{ gap: 8 }}>
      <div className="stance-bar" role="img" aria-label={STANCE.map(s => `${s.label} ${counts[s.key] ?? 0}`).join(', ')}>
        {STANCE.map(s => (counts[s.key] ?? 0) > 0 && <span key={s.key} style={{ flex: counts[s.key], background: s.color }} />)}
      </div>
      <div className="row-wrap" style={{ gap: 14, fontSize: 13 }}>
        {STANCE.map(s => (
          <span key={s.key} className="row" title={s.help}>
            <i className="sw" style={{ background: s.color }} />{s.label}<b>{num(counts[s.key] ?? 0)}</b>
          </span>
        ))}
      </div>
    </div>
  )
}

const Thumb = ({ id, alt }: { id: string; alt: string }) => (
  <img className="img-thumb" src={`${API}/media/${encodeURIComponent(id)}`} alt={alt} loading="lazy"
    onError={e => { (e.currentTarget as HTMLImageElement).style.visibility = 'hidden' }} />
)

export default function Lineage() {
  const { data } = useLineage()
  const topics: any[] = data?.topics ?? []
  const families: any[] = data?.image_families ?? []
  const [params] = useSearchParams()
  const [sel, setSel] = useState<string>(params.get('topic') ?? '')
  useEffect(() => { const t = params.get('topic'); if (t) setSel(t) }, [params])
  const { data: sit } = useSituation()
  const flagged = sit?.kpis?.top_alert?.topic_id
  // open on the story the Situation Room flagged, else the most coordinated one
  useEffect(() => {
    if (!topics.length || !sit || topics.some(t => String(t.topic_id) === sel)) return
    const f = topics.find(t => t.topic_id === flagged)
    setSel(String((f ?? topics[0]).topic_id))
  }, [topics, sel, flagged, sit])
  const lin = topics.find(t => String(t.topic_id) === sel)
  const ordered = [...topics].sort((a, b) => (b.topic_id === flagged ? 1 : 0) - (a.topic_id === flagged ? 1 : 0))
  const shown = [...ordered.slice(0, 4), ...ordered.filter((t, i) => i >= 4 && String(t.topic_id) === sel)]

  return (
    <div>
      <PageHead title="Origin & spread" sub="Where a story started and how it moved across platforms." />
      {topics.length === 0 ? <Empty>No lineage yet.</Empty> : (
        <div className="stack">
          <div className="row-wrap">
            <Seg label="Narrative" value={sel} onChange={setSel}
              options={shown.map(t => ({ value: String(t.topic_id), label: <span style={{ textTransform: 'capitalize' }}>{t.label}</span> }))} />
          </div>
          {lin && (
            <div className="grid g-main">
              <Card title={<span style={{ textTransform: 'capitalize' }}>{lin.label}</span>} sub={`${num(lin.n_posts)} posts · ${pct(lin.coordinated_share)} from coordinated accounts`}
                actions={lin.nature === 'manufactured' ? <StatusBadge status="critical">Likely coordinated</StatusBadge> : <StatusBadge status="good">Organic</StatusBadge>}>
                <Swimlanes lin={lin} />
                <div className="divider" />
                <div className="muted" style={{ fontSize: 12.5, marginBottom: 6 }}>What the {num(lin.n_posts)} posts do with the claim. Only the posts spreading it are traced across platforms.</div>
                <StanceBar counts={lin.stance_counts} />
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
                    <div className="muted" style={{ fontSize: 12.5 }}>by @{lin.origin_candidate.handle ?? lin.origin_candidate.author_id} · {num(lin.n_spreading ?? (lin.chains ?? []).length)} posts spreading it traced from here</div>
                  </div>
                )}
              </Card>
            </div>
          )}
          <Card title="Image copies" sub="The same picture found again after cropping, re-compressing or watermarking"
            actions={<InfoPop>Each image gets a visual fingerprint. Two images match when their fingerprints are nearly identical, even after edits. Similarity is measured against the first copy seen.</InfoPop>}>
            {families.length === 0 ? <Empty>No image copies found.</Empty> : (
              <div className="stack">
                {families.map(f => (
                  <div key={f.original.media_id} className="img-family">
                    <figure>
                      <Thumb id={f.original.media_id} alt="First copy seen" />
                      <figcaption><b>First seen</b> · {PLATFORM_LABEL[f.original.platform] ?? f.original.platform}<br /><span className="muted">{ist(f.original.first_seen)}</span></figcaption>
                    </figure>
                    <ArrowRight size={18} className="muted img-arrow" />
                    <div className="img-copies">
                      {f.copies.map((c: any) => (
                        <figure key={c.media_id}>
                          <Thumb id={c.media_id} alt={`Copy on ${PLATFORM_LABEL[c.platform] ?? c.platform}`} />
                          <figcaption>{PLATFORM_LABEL[c.platform] ?? c.platform} · {c.hamming != null ? `${Math.round((1 - c.hamming / 64) * 100)}% alike` : 'match'}
                            <br /><span className="muted">{num(c.posts)} post{c.posts === 1 ? '' : 's'} · +{minutesBetween(f.original.first_seen, c.first_seen)} min</span></figcaption>
                        </figure>
                      ))}
                    </div>
                    <div className="muted img-sum">{f.copies.length + 1} versions · {num(f.total_posts)} posts · {f.platforms.map((p: string) => PLATFORM_LABEL[p] ?? p).join(', ')}</div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}
      <NextStep />
    </div>
  )
}
