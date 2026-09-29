import { useState } from 'react'
export default function Search() {
  const [q, setQ] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const search = async () => { if(!q.trim()) return; setLoading(true); const r = await fetch(`/api/search?q=${encodeURIComponent(q)}`); const d = await r.json(); setResults(d.results||[]); setLoading(false) }
  return (
    <div>
      <h1 style={{color:'white',fontSize:22,fontWeight:700,marginBottom:20}}>Search</h1>
      <div style={{display:'flex',gap:10,marginBottom:20}}>
        <input value={q} onChange={e=>setQ(e.target.value)} onKeyDown={e=>e.key==='Enter'&&search()} placeholder="Search posts (SQLite FTS5)..." style={{flex:1,background:'#0d1326',border:'1px solid #1e2740',borderRadius:8,padding:'10px 14px',color:'white',fontSize:13,outline:'none'}} />
        <button onClick={search} disabled={loading} style={{background:'#3b82f6',color:'white',border:'none',borderRadius:8,padding:'10px 20px',fontSize:13,cursor:'pointer'}}>Search</button>
      </div>
      {results.map((r:any,i:number) => (
        <div key={i} style={{background:'#0d1326',border:'1px solid #1e2740',borderRadius:10,padding:14,marginBottom:8,display:'flex',gap:10}}>
          <span style={{fontSize:10,padding:'3px 8px',borderRadius:4,background:'#1e3a8a',color:'#93c5fd',fontFamily:'monospace',flexShrink:0}}>{r.platform}</span>
          <div>
            <div style={{color:'white',fontSize:13}}>{r.text}</div>
            <div style={{color:'#4b5563',fontSize:11,marginTop:4}}>{r.created_at}</div>
          </div>
        </div>
      ))}
      {results.length===0&&q&&!loading&&<div style={{color:'#4b5563',fontSize:13}}>No results for "{q}"</div>}
    </div>
  )
}
