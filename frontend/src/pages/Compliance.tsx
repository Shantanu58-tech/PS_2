import { useTraceability, useEvalSummary } from '../hooks/useApi'
export default function Compliance() {
  const { data: tr } = useTraceability()
  const { data: ev } = useEvalSummary()
  const reqs = tr?.requirements || []
  return (
    <div>
      <h1 style={{color:'white',fontSize:22,fontWeight:700,marginBottom:6}}>PS 26152 Compliance</h1>
      <p style={{color:'#6b7280',fontSize:13,marginBottom:20}}>SIH 2026 - Problem Statement 26152 (NTRO, Social Media Analytics) - every requirement mapped to implementation with measured metrics.</p>
      <div style={{background:'#0d1326',border:'1px solid #1e2740',borderRadius:12,overflow:'hidden',marginBottom:20}}>
        <table style={{width:'100%',borderCollapse:'collapse',fontSize:12}}>
          <thead><tr style={{background:'#111827'}}>
            {['PS Req.','Component','Module','Measured metric','Status'].map(h=><th key={h} style={{color:'#6b7280',textAlign:'left',padding:'10px 14px'}}>{h}</th>)}
          </tr></thead>
          <tbody>
            {reqs.map((r:any,i:number) => (
              <tr key={i} style={{borderTop:'1px solid #1e2740'}}>
                <td style={{padding:'10px 14px',fontWeight:700,color:'#3b82f6'}}>{r.ps}</td>
                <td style={{padding:'10px 14px',color:'white'}}>{r.component}</td>
                <td style={{padding:'10px 14px',color:'#6b7280',fontFamily:'monospace',fontSize:10}}>{r.module}</td>
                <td style={{padding:'10px 14px',color:'#9ca3af',fontFamily:'monospace',fontSize:10}}>{r.metric_name}: {typeof r.metric_value==='object'?JSON.stringify(r.metric_value):String(r.metric_value)}</td>
                <td style={{padding:'10px 14px'}}>
                  <span style={{fontSize:10,padding:'3px 8px',borderRadius:999,fontWeight:600,background:r.status==='built'?'rgba(20,83,45,0.4)':'rgba(161,108,0,0.3)',color:r.status==='built'?'#86efac':'#fcd34d',border:`1px solid ${r.status==='built'?'#166534':'#78350f'}`}}>
                    {r.status==='built'?'Built':r.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:16}}>
        <div style={{background:'#0d1326',border:'1px solid #1e2740',borderRadius:12,padding:16}}>
          <h3 style={{color:'white',fontWeight:600,marginBottom:12}}>Differentiators</h3>
          {['Coordination-adjusted analytics (organic/raw toggle)','Statistical null model (burstiness + entropy)','Coordinated cluster detection with held-out F1 evaluation','pHash cross-platform image lineage','Hash-chain + Ed25519 tamper-evident ledger','Section 63 draft certificate template','Hinglish-aware NLP pipeline','k-anonymity + DP aggregate-only demographics','Zero per-account demographic endpoint (tested)'].map((d,i) => (
            <div key={i} style={{display:'flex',gap:6,marginBottom:6,fontSize:12,color:'#9ca3af'}}>
              <span style={{color:'#22c55e'}}>v</span>{d}
            </div>
          ))}
        </div>
        <div style={{background:'#0d1326',border:'1px solid #1e2740',borderRadius:12,padding:16}}>
          <h3 style={{color:'white',fontWeight:600,marginBottom:12}}>Honest Limitations</h3>
          {['Age inference experimental (bio-cue only, low coverage)','Sarcasm detection English-biased; Hinglish harder','Lineage says earliest observed, not true origin','Section 63 certificate is a draft - legal review required','X and Telegram connectors live-capable; demo runs on replay','Instagram and Facebook import-only (no live connector)'].map((l,i) => (
            <div key={i} style={{display:'flex',gap:6,marginBottom:6,fontSize:12,color:'#9ca3af'}}>
              <span style={{color:'#eab308'}}>!</span>{l}
            </div>
          ))}
        </div>
      </div>
      {ev && ev.status !== 'not_yet_measured' && (
        <div style={{background:'#0d1326',border:'1px solid #1e2740',borderRadius:12,padding:16,marginTop:16}}>
          <h3 style={{color:'white',fontWeight:600,marginBottom:8}}>Measured Metrics</h3>
          <pre style={{fontSize:11,fontFamily:'monospace',color:'#9ca3af',overflow:'auto'}}>{JSON.stringify(ev,null,2)}</pre>
        </div>
      )}
    </div>
  )
}
