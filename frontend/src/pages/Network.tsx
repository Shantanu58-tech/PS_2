import { useInfluencers, useClusters } from '../hooks/useApi'
export default function Network() {
  const { data: kols } = useInfluencers()
  const { data: clusters } = useClusters()
  return (
    <div>
      <h1 style={{color:'white',fontSize:22,fontWeight:700,marginBottom:20}}>Network and Influence</h1>
      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:20}}>
        <div>
          <h2 style={{color:'white',fontSize:15,fontWeight:600,marginBottom:12}}>Key Opinion Leaders</h2>
          <div style={{background:'#0d1326',border:'1px solid #1e2740',borderRadius:12,overflow:'hidden'}}>
            <table style={{width:'100%',borderCollapse:'collapse',fontSize:12}}>
              <thead><tr style={{background:'#111827'}}>
                <th style={{color:'#6b7280',textAlign:'left',padding:'10px 14px'}}>Account</th>
                <th style={{color:'#6b7280',textAlign:'right',padding:'10px 14px'}}>Edges</th>
              </tr></thead>
              <tbody>
                {(kols?.influencers||[]).map((k:any,i:number) => (
                  <tr key={i} style={{borderTop:'1px solid #1e2740'}}>
                    <td style={{padding:'9px 14px',color:'#9ca3af',fontFamily:'monospace'}}>{k.src_account?.slice(0,18)}...</td>
                    <td style={{padding:'9px 14px',color:'white',textAlign:'right'}}>{k.edge_count}</td>
                  </tr>
                ))}
                {!kols?.influencers?.length && <tr><td colSpan={2} style={{padding:'24px',textAlign:'center',color:'#4b5563'}}>No data</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
        <div>
          <h2 style={{color:'white',fontSize:15,fontWeight:600,marginBottom:12}}>Coordination Clusters</h2>
          {(clusters?.clusters||[]).map((c:any) => (
            <div key={c.cluster_id} style={{background:'#0d1326',border:'1px solid #7f1d1d',borderRadius:12,padding:14,marginBottom:10}}>
              <div style={{display:'flex',justifyContent:'space-between',marginBottom:8}}>
                <span style={{color:'#f87171',fontSize:11,fontWeight:600}}>CLUSTER #{c.cluster_id}</span>
                <span style={{color:'white',fontWeight:700}}>{(c.score*100).toFixed(0)}%</span>
              </div>
              <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:4,fontSize:11,color:'#6b7280'}}>
                <div>Accounts: <span style={{color:'white'}}>{c.n_accounts}</span></div>
                <div>Posts: <span style={{color:'white'}}>{c.n_posts}</span></div>
                <div>Entropy Hn: <span style={{color:'white'}}>{c.hn?.toFixed(2)}</span></div>
                <div>Sync: <span style={{color:'white'}}>{c.sync?.toFixed(2)}</span></div>
              </div>
              <div style={{marginTop:8,fontSize:10,color:'#4b5563',fontStyle:'italic'}}>Behaviour consistent with scripted amplification. Not an accusation.</div>
            </div>
          ))}
          {!clusters?.clusters?.length && <div style={{color:'#4b5563',fontSize:13}}>No clusters detected yet</div>}
        </div>
      </div>
    </div>
  )
}
