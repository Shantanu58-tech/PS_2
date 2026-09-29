import { useState } from 'react'
import { useLedgerStatus } from '../hooks/useApi'
export default function Ledger() {
  const { data: status } = useLedgerStatus()
  const [verifyResult, setVerifyResult] = useState<any>(null)
  const [tamperResult, setTamperResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const verify = async () => { setLoading(true); const r = await fetch('/api/ledger/verify',{method:'POST'}); setVerifyResult(await r.json()); setLoading(false) }
  const tamper = async () => { setLoading(true); const r = await fetch('/api/ledger/tamper-sim',{method:'POST'}); setTamperResult(await r.json()); setLoading(false) }
  return (
    <div>
      <h1 style={{color:'white',fontSize:22,fontWeight:700,marginBottom:6}}>Evidence Ledger</h1>
      <p style={{color:'#6b7280',fontSize:13,marginBottom:20}}>Every collected record is SHA-256 hash-chained. Hourly Merkle checkpoints signed with Ed25519. Tamper-evident append-only storage.</p>
      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:12,marginBottom:20}}>
        <div style={{background:'#0d1326',border:'1px solid #1e2740',borderRadius:12,padding:16}}>
          <div style={{color:'#6b7280',fontSize:11,marginBottom:4}}>Total Records</div>
          <div style={{fontSize:28,fontWeight:700,color:'white'}}>{(status?.record_count||0).toLocaleString()}</div>
        </div>
        <div style={{background:'#0d1326',border:'1px solid #1e2740',borderRadius:12,padding:16}}>
          <div style={{color:'#6b7280',fontSize:11,marginBottom:4}}>Last Merkle Root</div>
          <div style={{fontSize:11,fontFamily:'monospace',color:'#9ca3af',wordBreak:'break-all'}}>{status?.last_checkpoint?.merkle_root?.slice(0,32)||'No checkpoint yet'}</div>
        </div>
      </div>
      <div style={{display:'flex',gap:12,marginBottom:20}}>
        <button onClick={verify} disabled={loading} style={{background:'#166534',color:'white',border:'none',borderRadius:8,padding:'10px 20px',fontSize:13,fontWeight:600,cursor:'pointer'}}>
          {loading?'Verifying...':'Verify Integrity'}
        </button>
        <button onClick={tamper} disabled={loading} style={{background:'#7f1d1d',color:'white',border:'none',borderRadius:8,padding:'10px 20px',fontSize:13,fontWeight:600,cursor:'pointer'}}>
          Tamper Simulation (scratch copy only)
        </button>
      </div>
      {verifyResult && (
        <div style={{background:verifyResult.status==='PASS'?'rgba(20,83,45,0.2)':'rgba(127,29,29,0.2)',border:`1px solid ${verifyResult.status==='PASS'?'#166534':'#7f1d1d'}`,borderRadius:12,padding:16,marginBottom:12}}>
          <div style={{fontWeight:700,marginBottom:8,color:verifyResult.status==='PASS'?'#86efac':'#f87171'}}>
            {verifyResult.status==='PASS'?'VERIFICATION PASSED':'VERIFICATION FAILED'}
          </div>
          <pre style={{fontSize:11,fontFamily:'monospace',color:'#9ca3af',overflow:'auto'}}>{JSON.stringify(verifyResult,null,2)}</pre>
        </div>
      )}
      {tamperResult && (
        <div style={{background:'rgba(127,29,29,0.2)',border:'1px solid #7f1d1d',borderRadius:12,padding:16}}>
          <div style={{fontWeight:700,color:'#f87171',marginBottom:8}}>Tamper Demo Result</div>
          <div style={{color:'#9ca3af',fontSize:13,marginBottom:8}}>Mutated seq {tamperResult.tampered_seq} in scratch copy.</div>
          <div style={{color:tamperResult.verify_result?.status==='FAIL'?'#f87171':'#9ca3af',fontWeight:600,fontSize:13}}>
            Verify: {tamperResult.verify_result?.status}
          </div>
          <p style={{color:'#4b5563',fontSize:11,marginTop:8,fontStyle:'italic'}}>Original DB unchanged. Simulation ran on a scratch copy.</p>
        </div>
      )}
    </div>
  )
}
