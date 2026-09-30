import { useState } from 'react'
import { ExternalLink, Radio } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { getJSON } from '../hooks/useApi'
import { Card, Meter, Seg } from './ui'
import { istShort, num, pct } from '../lib/fmt'
import { PLATFORM_LABEL, PLATFORM_SLOT } from '../lib/viz'

export const LIVE_PLATFORMS = ['x', 'telegram', 'youtube', 'reddit'] as const
const opts = { refetchInterval: 300_000, staleTime: 240_000 }

/** One platform's live feed, or every live platform merged ('all'). */
export const useLive = (platform: string = 'all') =>
  useQuery<any>({ queryKey: ['live', platform], queryFn: () => getJSON(platform === 'all' ? '/api/live' : `/api/live/${platform}`), ...opts })

const SOURCES: Record<string, string> = {
  x: 'public accounts (PIB, PIB Fact Check, NDMA, ANI)',
  telegram: 'public news channels',
  youtube: 'news channels: new videos and what viewers say under them',
  reddit: 'public Indian subreddits',
  all: 'X, Telegram, YouTube and Reddit',
}

export function ago(iso?: string) {
  if (!iso) return ''
  const m = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000))
  if (m < 60) return `${m} min ago`
  if (m < 60 * 24) return `${Math.round(m / 60)} h ago`
  return istShort(iso)
}

const short = (s: string) => s.replace(/\s*[-–|].*$/, '').trim()

function Post({ p, compact, showPlatform }: { p: any; compact: boolean; showPlatform: boolean }) {
  const m = p.metrics ?? {}
  return (
    <div style={{ padding: '9px 0', borderBottom: '1px solid var(--hairline)' }}>
      <div className="spread" style={{ gap: 8 }}>
        <span className="row" style={{ gap: 6, fontSize: 12, fontWeight: 700, color: 'var(--ink-2)', minWidth: 0 }}>
          {showPlatform && <span className="dot" style={{ background: PLATFORM_SLOT[p.platform] }} title={PLATFORM_LABEL[p.platform]} />}
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{short(p.source_title)}</span>
          {p.kind === 'comment' && <span className="muted" style={{ fontWeight: 500 }}>· viewer comment</span>}
          {p.kind === 'video' && <span className="muted" style={{ fontWeight: 500 }}>· new video</span>}
        </span>
        <span className="row" style={{ gap: 6, flexShrink: 0 }}>
          {p.sector !== 'other' && <span className="chip">{p.sector_name}</span>}
          <span className="muted tnum" style={{ fontSize: 11.5, whiteSpace: 'nowrap' }}>{ago(p.date)}</span>
        </span>
      </div>
      <div style={{ fontSize: 13.5, marginTop: 3, display: '-webkit-box', WebkitLineClamp: compact ? 2 : 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{p.text}</div>
      {p.on && !compact && <div className="muted" style={{ fontSize: 12, marginTop: 2 }}>on “{p.on}”</div>}
      <div className="row-wrap" style={{ gap: 12, marginTop: 4, fontSize: 11.5, color: 'var(--ink-3)' }}>
        {m.views != null && <span>{num(m.views)} views</span>}
        {m.likes != null && <span>{num(m.likes)} likes</span>}
        {m.reposts != null && <span>{num(m.reposts)} reposts</span>}
        {m.forwards != null && <span>{num(m.forwards)} forwards</span>}
        {p.emotions?.anxiety > 0 && <span className="row" style={{ gap: 4 }}>anxiety <span style={{ width: 40 }}><Meter value={p.emotions.anxiety} color="var(--s1)" label="anxiety" /></span></span>}
        <a href={p.link} target="_blank" rel="noreferrer" className="row" style={{ gap: 3, marginLeft: 'auto' }}>open<ExternalLink size={11} /></a>
      </div>
    </div>
  )
}

/** Real posts fetched now from a fixed allowlist of public sources. `platform='all'` merges every live app
 * and lets the reader narrow to one. */
export default function LiveFeed({ platform = 'all', compact = false }: { platform?: string; compact?: boolean }) {
  const [pick, setPick] = useState<string>('all')
  const current = platform === 'all' ? pick : platform
  const { data, isLoading } = useLive(current)
  const posts: any[] = data?.posts ?? []
  const connected = current === 'all' ? (data?.platforms ?? []).some((x: any) => x.connected) : data?.connected
  const label = current === 'all' ? 'Live from social media' : `Live from ${PLATFORM_LABEL[current] ?? current}`
  const title = (
    <span className="row" style={{ gap: 8 }}>
      <Radio size={16} color="var(--critical)" />{label}
      {connected && <span className="live-pill">LIVE</span>}
    </span>
  )
  const picker = platform === 'all' && !compact ? (
    <Seg label="Platform" value={pick} onChange={setPick}
      options={[{ value: 'all', label: 'All' }, ...LIVE_PLATFORMS.map(p => ({ value: p, label: PLATFORM_LABEL[p] }))]} />
  ) : undefined
  if (!isLoading && !connected) {
    return compact ? null : (
      <Card title={title} actions={picker} sub={SOURCES[current] ?? ''}>
        <div className="muted" style={{ fontSize: 13 }}>{data?.reason ?? 'Not connected right now.'}</div>
      </Card>
    )
  }
  const srcs: any[] = data?.channels ?? []
  const sub = !data ? 'connecting…' : current === 'all'
    ? `${num(posts.length)} real posts from ${(data.platforms ?? []).filter((x: any) => x.posts).map((x: any) => PLATFORM_LABEL[x.platform]).join(', ')}`
    : `${num(posts.length)} real posts from ${srcs.filter(c => c.posts).map(c => short(c.title)).join(', ')} · updated ${ago(data.fetched_at)}`
  return (
    <Card title={title} sub={sub} actions={picker}>
      {isLoading ? <div className="muted">Fetching…</div> : (
        <>
          {!compact && data?.summary && (
            <div className="grid g-3" style={{ marginBottom: 14 }}>
              <div className="kv" style={{ gridTemplateColumns: '1fr' }}><div><div className="k">Posts in the feed</div><div className="v">{num(data.summary.posts)}</div></div></div>
              <div className="kv" style={{ gridTemplateColumns: '1fr' }}><div><div className="k">Average anxiety</div><div className="v">{pct(data.summary.anxiety, 0)}</div></div></div>
              <div className="kv" style={{ gridTemplateColumns: '1fr' }}><div><div className="k">Talked about</div><div className="v" style={{ fontSize: 13 }}>{(data.summary.top_terms ?? []).slice(0, 5).join(' · ')}</div></div></div>
            </div>
          )}
          <div className="stack" style={{ gap: 0 }}>
            {posts.slice(0, compact ? 6 : 24).map(p => <Post key={p.platform + p.id} p={p} compact={compact} showPlatform={current === 'all'} />)}
          </div>
          {!compact && <div className="muted" style={{ fontSize: 12, marginTop: 10 }}>
            Fetched live from a fixed list of {SOURCES[current] ?? 'public sources'}, scored with the fast lexicon model, refreshed every 10 minutes. Shown here, not stored.
          </div>}
        </>
      )}
    </Card>
  )
}
