import { useAlerts, useLedgerStatus, useTopics } from '../hooks/useApi'
import { useAppStore } from '../store/app'
import { useState } from 'react'

function SignalCard({ alert, onCase }: { alert: any; onCase: (id: number) => void }) {
  const ev = (() => { try { return JSON.parse(alert.evidence_json) } catch { return {} } })()
  const high = alert.priority >= 70
  return (
    <div style={{background:'#0d1326',border:`1px solid ${high?'#7f1d1d':'#1e2740'}`,borderRadius:12,padding:16,marginBottom:12}}>
      <div style={{fontSize:10,color:high?'#f87171':'#3b82f6',fontFamily:'monospace',marginBottom:4}}>
        PRIORITY {alert.priority.toFixed(0)}/100
      </div>
      <div style={{color:'white',fontWeight:600,fontSize:13,marginBottom:8}}>{alert.headline}</div>
      {ev.coordinated_share !== undefined && (
        <div style={{fontSize:11,color:'#9ca3af',marginBottom:8}}>
          Coordinated: {(ev.coordinated_share*100).toFixed(0)}% · Burst level: {ev.burst_level}
        </div>
      )}
      <button onClick={() => onCase(alert.alert_id)}
        style={{background:'#3b82f6',color:'white',border:'none',borderRadius:6,padding:'6px 12px',fontSize:12,cursor:'pointer'}}>
        Open Case
      </button>
    </div>
  )
}

export default function CommandCenter() {
  const { organicOnly } = useAppStore()
  const { data: alertsData } = useAlerts(organicOnly)
  const { data: ledger } = useLedgerStatus()
  const { data: topicsData } = useTopics()
  const [replayMsg, setReplayMsg] = useState('')
  const alerts = alertsData?.alerts || []
  const topics = topicsData?.topics || []

  const startReplay = async () => {
    const res = await fetch('/api/replay/start', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({speed:60}) })
    const j = await res.json()
    setReplayMsg(j.ok ? 'Replay started — scenario is loading (~40k posts)' : 'Error starting replay')
  }

  return (
    <div>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:24}}>
        <div>
          <h1 style={{color:'white',fontSize:24,fontWeight:700,margin:0}}>Command Center</h1>
          <p style={{color:'#6b7280',fontSize:13,margin:'4px 0 0'}}>
            {organicOnly ? '🌿 Organic only — coordinated accounts excluded' : '⚡ Raw mode — all accounts'}
          </p>
        </div>
        <button onClick={startReplay} style={{background:'#1e2740',color:'#9ca3af',border:'1px solid #253454',borderRadius:8,padding:'8px 16px',fontSize:12,cursor:'pointer'}}>
          ▶ Start Replay
        </button>
      </div>
      {replayMsg && <div style={{background:'rgba(59,130,246,0.1)',border:'1px solid #1d4ed8',borderRadius:8,padding:10,fontSize:12,color:'#93c5fd',marginBottom:16}}>{replayMsg}</div>}
      <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:12,marginBottom:24}}>
        {[
          { label:'Records Ingested', value: (ledger?.record_count||0).toLocaleString() },
          { label:'Active Alerts', value: alerts.filter((a:any)=>a.status==='new').length, color:'#ef4444' },
          { label:'Topics Tracked', value: topics.length },
          { label:'Ledger', value: ledger?.last_checkpoint ? 'VERIFIED ✓' : 'EMPTY', color:'#22c55e' },
        ].map(m => (
          <div key={m.label} style={{background:'#0d1326',border:'1px solid #1e2740',borderRadius:12,padding:16}}>
            <div style={{color:'#6b7280',fontSize:11,marginBottom:4}}>{m.label}</div>
            <div style={{fontSize:22,fontWeight:700,color:m.color||'white'}}>{m.value}</div>
          </div>
        ))}
      </div>
      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:20}}>
        <div>
          <h2 style={{color:'white',fontSize:16,fontWeight:600,marginBottom:12}}>Signal Cards</h2>
          {alerts.length === 0 ? (
            <div style={{background:'#0d1326',border:'1px solid #1e2740',borderRadius:12,padding:32,textAlign:'center',color:'#4b5563',fontSize:13}}>
              No active alerts · Start replay to generate scenario
            </div>
          ) : alerts.map((a:any) => <SignalCard key={a.alert_id} alert={a} onCase={() => {}} />)}
        </div>
        <div>
          <h2 style={{color:'white',fontSize:16,fontWeight:600,marginBottom:12}}>Rising Topics</h2>
          {topics.length === 0 ? (
            <div style={{color:'#4b5563',fontSize:13}}>No topics yet — run replay scenario</div>
          ) : topics.slice(0,8).map((t:any) => (
            <div key={t.topic_id} style={{background:'#0d1326',border:'1px solid #1e2740',borderRadius:10,padding:12,marginBottom:8}}>
              <div style={{color:'white',fontSize:13,fontWeight:500}}>{t.label}</div>
              <div style={{color:'#6b7280',fontSize:11,marginTop:2}}>{t.keywords}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
