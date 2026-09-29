import { useQuery } from '@tanstack/react-query'

const PLATFORM_STYLE: Record<string, { bg: string; fg: string }> = {
  telegram: { bg: '#1e3a8a', fg: '#93c5fd' },
  x: { bg: '#0c4a6e', fg: '#7dd3fc' },
  reddit: { bg: '#431407', fg: '#fdba74' },
  youtube: { bg: '#450a0a', fg: '#fca5a5' },
}
const ist = (ts: string) =>
  new Date(ts).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'short' }) + ' IST'
const minutesBetween = (a: string, b: string) => Math.round((new Date(b).getTime() - new Date(a).getTime()) / 60000)

export default function Lineage() {
  const { data } = useQuery({ queryKey: ['lineage'], queryFn: () => fetch('/api/lineage').then(r => r.json()) })
  const topics: any[] = data?.topics || []
  const images: any[] = data?.image_matches || []
  return (
    <div>
      <h1 style={{color:'white',fontSize:22,fontWeight:700,marginBottom:16}}>Narrative Lineage</h1>
      <p style={{color:'#9ca3af',fontSize:13,lineHeight:1.7,marginBottom:16}}>
        Earliest observed appearance of each narrative across platforms, from text-claim clustering, repost/forward chains and perceptual image hashing.
      </p>
      {topics.length === 0 && <div style={{color:'#4b5563',fontSize:13}}>No lineage yet - start the replay from the Command Center.</div>}
      {topics.map(t => (
        <div key={t.topic_id} style={{background:'#0d1326',border:`1px solid ${t.nature==='manufactured'?'#7f1d1d':'#1e2740'}`,borderRadius:12,padding:20,marginBottom:16}}>
          <div style={{display:'flex',justifyContent:'space-between',marginBottom:12}}>
            <span style={{color:'white',fontWeight:600}}>{t.label}</span>
            <span style={{fontSize:11,color:t.nature==='manufactured'?'#f87171':'#86efac'}}>
              {t.nature} - {((t.coordinated_share||0)*100).toFixed(0)}% coordinated - {t.n_posts} posts
            </span>
          </div>
          <div style={{fontFamily:'monospace',fontSize:12,color:'#9ca3af',lineHeight:2}}>
            {(t.platforms||[]).map((p: any, i: number) => {
              const s = PLATFORM_STYLE[p.platform] || { bg: '#1f2937', fg: '#e5e7eb' }
              return (
                <div key={p.platform} style={{display:'flex',alignItems:'center',gap:12,marginBottom:4}}>
                  <span style={{background:s.bg,color:s.fg,padding:'3px 10px',borderRadius:4,minWidth:80,textAlign:'center'}}>{p.platform.toUpperCase()}</span>
                  <span style={{color:'#6b7280'}}>
                    {i === 0 ? 'Earliest observed' : `+${minutesBetween(t.platforms[0].first_seen, p.first_seen)} min`} - {ist(p.first_seen)} - {p.n_posts} posts{p.has_media ? ' - with image' : ''}
                  </span>
                </div>
              )
            })}
          </div>
          {t.origin_candidate && (
            <div style={{marginTop:10,fontSize:12,color:'#9ca3af',borderLeft:'2px solid #374151',paddingLeft:12}}>
              "{t.origin_candidate.text}"
            </div>
          )}
          <p style={{color:'#4b5563',fontSize:11,marginTop:12,fontStyle:'italic'}}>{t.caveat}</p>
        </div>
      ))}
      {images.length > 0 && (
        <div style={{background:'#0d1326',border:'1px solid #1e2740',borderRadius:12,padding:20}}>
          <h3 style={{color:'white',fontWeight:600,marginBottom:10}}>Image variants (pHash)</h3>
          {images.map((m, i) => (
            <div key={i} style={{fontFamily:'monospace',fontSize:12,color:'#9ca3af',marginBottom:4}}>
              {m.media_id_a} ({m.platform_a}) {'->'} {m.media_id_b} ({m.platform_b}): Hamming {m.hamming} (threshold {m.threshold})
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
