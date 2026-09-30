import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ExternalLink, FilePlus2, Scale } from 'lucide-react'
import { useAlerts, useCases, useCreateCase } from '../hooks/useApi'
import { Card, Empty, NextStep, PageHead } from '../components/ui'
import { ist } from '../lib/fmt'

export default function CaseFile() {
  const { data: alertsData } = useAlerts()
  const { data: casesData } = useCases()
  const createCase = useCreateCase()
  const cases: any[] = casesData?.cases ?? []
  const alerts: any[] = alertsData?.alerts ?? []
  const [params] = useSearchParams()
  const [sel, setSel] = useState<number | undefined>(params.get('case') ? Number(params.get('case')) : undefined)
  useEffect(() => { const c = params.get('case'); if (c) setSel(Number(c)) }, [params])
  useEffect(() => { if (sel == null && cases.length) setSel(cases[0].case_id) }, [cases, sel])

  return (
    <div>
      <PageHead title="Cases" sub="Turn a signal into a ready-to-share evidence pack." />
      <div className="grid" style={{ gridTemplateColumns: 'minmax(260px, 360px) minmax(0, 1fr)' }}>
        <div className="stack">
          <Card title="Start a case">
            {alerts.length === 0 ? <Empty>No signals.</Empty> : (
              <div className="stack" style={{ gap: 8 }}>
                {alerts.slice(0, 6).map(a => (
                  <div key={a.alert_id} className="spread" style={{ alignItems: 'flex-start' }}>
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontSize: 13.5, fontWeight: 600, textTransform: 'capitalize' }}>{a.topic_label ?? 'Topic'}</div>
                      <div className="muted" style={{ fontSize: 12 }}>priority {a.priority.toFixed(0)}</div>
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
          <Card title="Your cases">
            {cases.length === 0 ? <div className="muted">No cases yet. Start one above.</div> : (
              <div className="stack" style={{ gap: 4 }}>
                {cases.map(c => (
                  <button key={c.case_id} className="btn btn-ghost" onClick={() => setSel(c.case_id)}
                    style={{ justifyContent: 'space-between', textAlign: 'left', borderRadius: 12, background: sel === c.case_id ? 'var(--accent-soft)' : undefined }}>
                    <span style={{ textTransform: 'capitalize' }}>{c.title}<div className="muted" style={{ fontSize: 12, fontWeight: 400 }}>Case #{c.case_id} · {ist(c.created_at)}</div></span>
                  </button>
                ))}
              </div>
            )}
          </Card>
        </div>
        {sel != null ? (
          <Card title={`Case #${sel}`} sub="evidence pack, assembled automatically"
            actions={<>
              <a className="btn btn-sm" href={`/api/cases/${sel}/brief`} target="_blank" rel="noreferrer"><ExternalLink size={14} />Open brief</a>
              <a className="btn btn-sm" href={`/api/cases/${sel}/certificate`} target="_blank" rel="noreferrer" title="Draft BSA §63 certificate for legal review"><Scale size={14} />Certificate (draft)</a>
            </>}>
            <iframe title={`Case ${sel} brief`} src={`/api/cases/${sel}/brief`} style={{ width: '100%', height: 640, border: '1px solid var(--ring)', borderRadius: 12, background: '#fff' }} />
          </Card>
        ) : <Empty>Start a case to see its evidence pack.</Empty>}
      </div>
      <NextStep />
    </div>
  )
}
