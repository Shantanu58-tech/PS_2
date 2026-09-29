import { useTopics } from '../hooks/useApi'
export default function Trends() {
  const { data } = useTopics()
  const topics = data?.topics || []
  return (
    <div>
      <h1 style={{color:'white',fontSize:22,fontWeight:700,marginBottom:20}}>Trends and Topic Detection</h1>
      {topics.length === 0 ? <div style={{color:'#4b5563'}}>No topics yet — run replay scenario</div> : topics.map((t:any) => (
        <div key={t.topic_id} style={{background:'#0d1326',border:'1px solid #1e2740',borderRadius:12,padding:16,marginBottom:10,display:'flex',justifyContent:'space-between',alignItems:'flex-start'}}>
          <div>
            <div style={{color:'white',fontWeight:600}}>{t.label}</div>
            <div style={{color:'#6b7280',fontSize:12,marginTop:4}}>{(t.keywords||[]).join(' · ')} · {t.n_posts} posts · coordinated share {((t.coordinated_share||0)*100).toFixed(0)}%</div>
            <div style={{color:'#4b5563',fontSize:11,marginTop:4}}>First: {t.first_seen} · Last: {t.last_seen}</div>
          </div>
          <span style={{fontSize:11,padding:'4px 10px',borderRadius:999,fontWeight:600,background:t.nature==='manufactured'?'rgba(127,29,29,0.4)':'rgba(20,83,45,0.4)',color:t.nature==='manufactured'?'#f87171':'#86efac',border:`1px solid ${t.nature==='manufactured'?'#7f1d1d':'#166534'}`}}>
            {t.nature==='manufactured'?'Manufactured trend':'Organic'}
          </span>
        </div>
      ))}
    </div>
  )
}
