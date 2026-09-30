import { ExternalLink, Radio } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { getJSON } from '../hooks/useApi'
import { Card, Meter } from './ui'
import { istShort, num, pct } from '../lib/fmt'

export const useLiveTelegram = () =>
  useQuery<any>({ queryKey: ['live-telegram'], queryFn: () => getJSON('/api/live/telegram'), refetchInterval: 300_000, staleTime: 240_000 })

function ago(iso?: string) {
  if (!iso) return ''
  const m = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000))
  if (m < 60) return `${m} min ago`
  if (m < 60 * 24) return `${Math.round(m / 60)} h ago`
  return istShort(iso)
}

/** Real posts fetched now from public Telegram news channels through the connected account. */
export default function LiveTelegram({ compact = false }: { compact?: boolean }) {
  const { data, isLoading } = useLiveTelegram()
  const posts: any[] = data?.posts ?? []
  const title = (
    <span className="row" style={{ gap: 8 }}>
      <Radio size={16} color="var(--critical)" />Live from Telegram
      {data?.connected && <span className="live-pill">LIVE</span>}
    </span>
  )
  if (!isLoading && !data?.connected) {
    return compact ? null : (
      <Card title={title} sub="public news channels, fetched through the connected account">
        <div className="muted" style={{ fontSize: 13 }}>{data?.reason ?? 'Telegram is not connected.'}</div>
      </Card>
    )
  }
  const chans: any[] = data?.channels ?? []
  return (
    <Card title={title}
      sub={data ? `${num(posts.length)} real posts from ${chans.filter(c => c.posts).map(c => c.title.replace(/[-–].*$/, '').trim()).join(', ')} · updated ${ago(data.fetched_at)}` : 'connecting…'}>
      {isLoading ? <div className="muted">Fetching from Telegram…</div> : (
        <>
          {!compact && data?.summary && (
            <div className="grid g-3" style={{ marginBottom: 14 }}>
              <div className="kv" style={{ gridTemplateColumns: '1fr' }}><div><div className="k">Posts in the feed</div><div className="v">{num(data.summary.posts)}</div></div></div>
              <div className="kv" style={{ gridTemplateColumns: '1fr' }}><div><div className="k">Average anxiety</div><div className="v">{pct(data.summary.anxiety, 0)}</div></div></div>
              <div className="kv" style={{ gridTemplateColumns: '1fr' }}><div><div className="k">Talked about</div><div className="v" style={{ fontSize: 13 }}>{(data.summary.top_terms ?? []).slice(0, 5).join(' · ')}</div></div></div>
            </div>
          )}
          <div className="stack" style={{ gap: 0 }}>
            {posts.slice(0, compact ? 5 : 20).map(p => (
              <div key={p.link} style={{ padding: '9px 0', borderBottom: '1px solid var(--hairline)' }}>
                <div className="spread" style={{ gap: 8 }}>
                  <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--ink-2)' }}>{p.channel_title.replace(/[-–].*$/, '').trim()}</span>
                  <span className="row" style={{ gap: 6 }}>
                    {p.sector !== 'other' && <span className="chip">{p.sector_name}</span>}
                    <span className="muted tnum" style={{ fontSize: 11.5, whiteSpace: 'nowrap' }}>{ago(p.date)}</span>
                  </span>
                </div>
                <div style={{ fontSize: 13.5, marginTop: 3, display: '-webkit-box', WebkitLineClamp: compact ? 2 : 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{p.text}</div>
                <div className="row" style={{ gap: 12, marginTop: 4, fontSize: 11.5, color: 'var(--ink-3)' }}>
                  {p.views != null && <span>{num(p.views)} views</span>}
                  {p.forwards != null && <span>{num(p.forwards)} forwards</span>}
                  {p.emotions?.anxiety > 0 && <span className="row" style={{ gap: 4 }}>anxiety <span style={{ width: 40 }}><Meter value={p.emotions.anxiety} color="var(--s1)" label="anxiety" /></span></span>}
                  <a href={p.link} target="_blank" rel="noreferrer" className="row" style={{ gap: 3, marginLeft: 'auto' }}>open<ExternalLink size={11} /></a>
                </div>
              </div>
            ))}
          </div>
          {!compact && <div className="muted" style={{ fontSize: 12, marginTop: 10 }}>
            Fetched live from a fixed list of public news channels and scored with the fast lexicon model; refreshed every few minutes.
          </div>}
        </>
      )}
    </Card>
  )
}
