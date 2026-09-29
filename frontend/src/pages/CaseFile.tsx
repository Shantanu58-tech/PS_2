import { useEffect, useState } from 'react'
import { ExternalLink, FilePlus2, Scale } from 'lucide-react'
import { useAlerts, useCases, useCreateCase, useHealth } from '../hooks/useApi'
import { Card, Empty, PageHead, StatusBadge } from '../components/ui'
import { ist, num } from '../lib/fmt'

export default function CaseFile() {
  const { data: health } = useHealth()
  const { data: alertsData } = useAlerts()
  const { data: casesData } = useCases()
  const createCase = useCreateCase()
  const cases: any[] = casesData?.cases ?? []
  const alerts: any[] = alertsData?.alerts ?? []
  const [sel, setSel] = useState<number | undefined>()
  useEffect(() => { if (sel == null && cases.length) setSel(cases[0].case_id) }, [cases, sel])

  return (
    <div>
      <PageHead code="CASE" title="Case files"
        sub="A case turns a Signal Card into an evidence pack: summary, lineage, raw-vs-organic affect, coordination statistics, an evidence index with ledger sequence numbers and record hashes, and a draft BSA §63 certificate." />
      {health?.demo_readonly && <div className="notice" style={{ marginBottom: 16 }}>Public demo: cases you create are kept until the server restarts, then the demo resets.</div>}
      <div className="grid" style={{ gridTemplateColumns: 'minmax(260px, 360px) minmax(0, 1fr)' }}>
        <div className="stack">
          <Card title="Open a case from a signal">
            {alerts.length === 0 ? <Empty>No signals.</Empty> : (
              <div className="stack" style={{ gap: 8 }}>
                {alerts.slice(0, 6).map(a => (
                  <div key={a.alert_id} className="spread" style={{ alignItems: 'flex-start' }}>
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 560 }}>{a.topic_label ?? 'Topic'}</div>
                      <div className="muted" style={{ fontSize: 12 }}>P {a.priority.toFixed(0)} · {a.status}</div>
                    </div>
                    <button className="btn btn-sm" disabled={createCase.isPending}
                      onClick={() => createCase.mutate({ alert_id: a.alert_id, title: (a.topic_label ?? a.headline).slice(0, 80) },
                        { onSuccess: (r: any) => setSel(r.case_id) })}>
                      <FilePlus2 size={14} />Open
                    </button>
                  </div>
                ))}
                {createCase.isError && <div className="notice crit">{String(createCase.error)}</div>}
              </div>
            )}
          </Card>
          <Card title="Cases" sub={`${num(cases.length)} in this session`}>
            {cases.length === 0 ? <div className="muted">No cases yet. Open one from a signal above.</div> : (
              <div className="stack" style={{ gap: 4 }}>
                {cases.map(c => (
                  <button key={c.case_id} className="btn btn-ghost" onClick={() => setSel(c.case_id)}
                    style={{ justifyContent: 'space-between', textAlign: 'left', background: sel === c.case_id ? 'var(--surface-2)' : undefined }}>
                    <span>Case #{c.case_id} · {c.title}<div className="muted" style={{ fontSize: 11 }}>{ist(c.created_at)}</div></span>
                    {c.n_certificates > 0 && <StatusBadge status="warning">§63 draft</StatusBadge>}
                  </button>
                ))}
              </div>
            )}
          </Card>
        </div>
        {sel != null ? (
          <Card title={`Case #${sel} brief`} sub="auto-assembled; every figure links back to ledger records"
            actions={<>
              <a className="btn btn-sm" href={`/api/cases/${sel}/brief`} target="_blank" rel="noreferrer"><ExternalLink size={14} />Open brief</a>
              <a className="btn btn-sm" href={`/api/cases/${sel}/certificate`} target="_blank" rel="noreferrer"><Scale size={14} />§63 draft certificate</a>
            </>}>
            <div className="notice warn" style={{ marginBottom: 10 }}>The §63 certificate is a DRAFT for review and signature. It is not a legal opinion, and no admissibility is claimed.</div>
            <iframe title={`Case ${sel} brief`} src={`/api/cases/${sel}/brief`} style={{ width: '100%', height: 640, border: '1px solid var(--ring)', borderRadius: 8, background: '#fff' }} />
          </Card>
        ) : <Empty>Open a case to see its brief.</Empty>}
      </div>
    </div>
  )
}
