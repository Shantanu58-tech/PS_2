import { useState } from 'react'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { Search as SearchIcon } from 'lucide-react'
import { getJSON } from '../hooks/useApi'
import { Card, PageHead } from '../components/ui'
import { PLATFORM_LABEL, PLATFORM_SLOT } from '../lib/viz'
import { ist } from '../lib/fmt'

const EXAMPLES = ['varunapur dam', 'evacuate', 'bhago', 'cricket', 'बांध']

export default function Search() {
  const [q, setQ] = useState('')
  const [submitted, setSubmitted] = useState('')
  const { data, isFetching } = useQuery<any>({
    queryKey: ['search', submitted], queryFn: () => getJSON(`/api/search?q=${encodeURIComponent(submitted)}&limit=50`),
    enabled: !!submitted, placeholderData: keepPreviousData,
  })
  const results: any[] = data?.results ?? []
  const go = (v: string) => { setQ(v); setSubmitted(v.trim()) }

  return (
    <div>
      <PageHead code="FTS" title="Search" sub="Full-text search over every collected post (SQLite FTS5, ranked by BM25). Each result carries its ledger sequence number." />
      <form className="row" onSubmit={e => { e.preventDefault(); go(q) }} style={{ marginBottom: 12 }}>
        <input className="input" style={{ flex: 1 }} value={q} onChange={e => setQ(e.target.value)} placeholder="Search posts, e.g. varunapur dam" aria-label="Search query" />
        <button className="btn btn-primary" type="submit"><SearchIcon size={14} />Search</button>
      </form>
      <div className="row-wrap" style={{ marginBottom: 16 }}>
        <span className="muted" style={{ fontSize: 12 }}>Try:</span>
        {EXAMPLES.map(e => <button key={e} className="btn btn-sm btn-ghost" onClick={() => go(e)}>{e}</button>)}
      </div>
      {submitted && (
        <Card title={`${results.length} result${results.length === 1 ? '' : 's'} for "${submitted}"`} className={isFetching ? 'loading-hold' : ''}>
          {results.length === 0 ? <div className="muted">No matches.</div> : (
            <table className="tbl">
              <thead><tr><th>Platform</th><th>Post</th><th>Time</th><th className="num">Ledger seq</th></tr></thead>
              <tbody>{results.map(r => (
                <tr key={r.platform + r.post_id}>
                  <td><span className="badge"><span className="dot" style={{ background: PLATFORM_SLOT[r.platform] ?? 'var(--ink-3)' }} />{PLATFORM_LABEL[r.platform] ?? r.platform}</span></td>
                  <td>{r.text}<div className="muted mono" style={{ fontSize: 11 }}>{r.author_id} · {r.lang ?? ''}</div></td>
                  <td style={{ whiteSpace: 'nowrap' }}>{ist(r.created_at)}</td>
                  <td className="num mono">{r.ledger_seq}</td>
                </tr>
              ))}</tbody>
            </table>
          )}
        </Card>
      )}
    </div>
  )
}
