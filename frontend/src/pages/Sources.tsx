import { useCollectors } from '../hooks/useApi'
import { Card, InfoPop, PageHead, StatusBadge } from '../components/ui'
import { PLATFORM_LABEL } from '../lib/viz'
import { ist, num } from '../lib/fmt'

function statusBadge(s: string) {
  if (s === 'ok' || s === 'done' || s === 'idle') return <StatusBadge status="good">{s === 'done' ? 'Replayed' : s === 'ok' ? 'Healthy' : 'Ready'}</StatusBadge>
  if (s === 'credentials_missing') return <StatusBadge status="warning">No credentials</StatusBadge>
  if (s === 'degraded') return <StatusBadge status="serious">Degraded</StatusBadge>
  if (s === 'circuit_open') return <StatusBadge status="critical">Circuit open</StatusBadge>
  if (s === 'import_only') return <span className="badge">Import only</span>
  if (s === 'running') return <StatusBadge status="warning">Running</StatusBadge>
  return <span className="badge">{s}</span>
}

const ORDER = ['x', 'telegram', 'instagram', 'facebook', 'reddit', 'youtube', 'replay']

export default function Sources() {
  const { data } = useCollectors()
  const c = data?.collectors ?? {}
  const names = ORDER.filter(n => c[n])
  return (
    <div>
      <PageHead code="PS · A" title="Sources & collectors"
        sub="Multi-platform collection into one append-only, time-stamped history. Every collector sits behind the same interface, with exponential backoff, jitter and a circuit breaker." />
      <Card title="Collectors" sub={`mode: ${data?.mode ?? '—'}`}
        actions={<InfoPop>X and Telegram are the PS "essential" platforms; Instagram and Facebook are "desirable" (import of official exports, since there is no free live API); Reddit and YouTube are "appreciable". The public demo runs on the replayed synthetic scenario.</InfoPop>}>
        <div className="table-wrap">
          <table className="tbl">
            <thead><tr><th>Platform</th><th>PS tier</th><th>Status</th><th className="num">Records in ledger</th><th>Last record</th><th className="num">Errors</th></tr></thead>
            <tbody>{names.map(n => {
              const s = c[n]
              return (
                <tr key={n}>
                  <td style={{ fontWeight: 560 }}>{PLATFORM_LABEL[n] ?? (n === 'replay' ? 'Replay (scenario)' : n)}</td>
                  <td><span className="chip">{s.tier}</span></td>
                  <td>{statusBadge(s.status)}{s.last_error && <div className="muted" style={{ fontSize: 11 }}>{s.last_error}</div>}</td>
                  <td className="num">{n === 'replay' ? num(s.ingested) : num(s.records)}</td>
                  <td>{s.last_record ? ist(s.last_record) : <span className="muted">—</span>}</td>
                  <td className="num">{s.errors ?? 0}</td>
                </tr>
              )
            })}</tbody>
          </table>
        </div>
      </Card>
      <div className="grid g-2" style={{ marginTop: 16 }}>
        <Card title="Live targets" sub="channels, handles, subreddits and videos polled in live mode">
          {(data?.targets ?? []).length === 0 ? <div className="muted">No live targets configured (the demo runs in replay mode).</div> : (
            <table className="tbl"><tbody>{data.targets.map((t: any) => <tr key={t.collector + t.target}><td>{PLATFORM_LABEL[t.collector] ?? t.collector}</td><td className="mono">{t.target}</td><td className="muted">{ist(t.added_at)}</td></tr>)}</tbody></table>
          )}
        </Card>
        <Card title="Honest limits">
          <ul style={{ margin: 0, paddingLeft: 18, color: 'var(--ink-2)', fontSize: 13 }}>
            <li>X is collected with a research tool (twscrape, burner-account cookies). Production should use licensed access.</li>
            <li>Telegram needs a one-time phone login; public channels only, no private chats.</li>
            <li>Instagram and Facebook are import-only (official exports).</li>
            <li>No posting, liking or messaging on any platform, ever.</li>
          </ul>
        </Card>
      </div>
    </div>
  )
}
