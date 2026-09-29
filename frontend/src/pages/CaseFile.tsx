import { useState } from 'react'
import { useAlerts } from '../hooks/useApi'
export default function CaseFile() {
  const { data } = useAlerts()
  const alerts = data?.alerts || []
  const [msg, setMsg] = useState('')
  const createCase = async (alertId: number, headline: string) => {
    const res = await fetch('/api/cases', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ alert_id: alertId, title: headline.slice(0,80) }) })
    const j = await res.json()
    setMsg(j.case_id ? 'Case #' + j.case_id + ' created: ' + j.brief_url + ' | ' + j.certificate_url : (j.detail || 'Error creating case'))
  }
  return (
    <div>
      <h1 style={{color:'white',fontSize:22,fontWeight:700,marginBottom:6}}>Case Files</h1>
      <p style={{color:'#6b7280',fontSize:13,marginBottom:16}}>Create a case from a Signal Card to auto-assemble a brief with evidence index, emotion timeline, lineage, and section 63 draft certificate.</p>
      {msg && <div style={{background:'rgba(34,197,94,0.1)',border:'1px solid #166534',borderRadius:8,padding:10,fontSize:12,color:'#86efac',marginBottom:16}}>{msg}</div>}
      {alerts.length === 0 ? <div style={{color:'#4b5563',fontSize:13}}>No alerts yet - run replay first</div> : alerts.map((a:any) => (
        <div key={a.alert_id} style={{background:'#0d1326',border:'1px solid #1e2740',borderRadius:12,padding:16,marginBottom:12}}>
          <div style={{color:'white',fontWeight:600,marginBottom:4}}>{a.headline}</div>
          <div style={{color:'#6b7280',fontSize:11,marginBottom:12}}>Priority {a.priority.toFixed(0)}/100</div>
          <button onClick={() => createCase(a.alert_id, a.headline)} style={{background:'#3b82f6',color:'white',border:'none',borderRadius:8,padding:'8px 16px',fontSize:12,cursor:'pointer',fontWeight:600}}>
            Create Case + S63 Draft
          </button>
        </div>
      ))}
    </div>
  )
}
