export default function Lineage() {
  return (
    <div>
      <h1 style={{color:'white',fontSize:22,fontWeight:700,marginBottom:16}}>Narrative Lineage</h1>
      <div style={{background:'#0d1326',border:'1px solid #1e2740',borderRadius:12,padding:24,marginBottom:16}}>
        <p style={{color:'#9ca3af',fontSize:13,lineHeight:1.7,marginBottom:16}}>
          Cross-platform narrative lineage traces the earliest observed appearance of a claim across Telegram to X to Reddit/YouTube using text embeddings, perceptual image hashing (pHash Hamming distance), and Telegram forward headers.
        </p>
        <div style={{fontFamily:'monospace',fontSize:12,color:'#9ca3af',lineHeight:2}}>
          <div style={{display:'flex',alignItems:'center',gap:12,marginBottom:4}}>
            <span style={{background:'#1e3a8a',color:'#93c5fd',padding:'3px 10px',borderRadius:4}}>TELEGRAM</span>
            <span style={{color:'#6b7280'}}>T0 22:10 IST - Origin meme posted in channel cluster</span>
          </div>
          <div style={{marginLeft:20,borderLeft:'2px solid #374151',paddingLeft:12,marginBottom:4,color:'#4b5563',fontSize:11}}>
            Image variant JPEG q30 + crop 10% · Hamming distance 6 less than threshold 10 - MATCH
          </div>
          <div style={{display:'flex',alignItems:'center',gap:12,marginBottom:4}}>
            <span style={{background:'#0c4a6e',color:'#7dd3fc',padding:'3px 10px',borderRadius:4}}>X</span>
            <span style={{color:'#6b7280'}}>T0+12min - 60 coordinated accounts begin template posts</span>
          </div>
          <div style={{marginLeft:20,borderLeft:'2px solid #374151',paddingLeft:12,marginBottom:4,color:'#4b5563',fontSize:11}}>
            Text cosine similarity 0.94 to Telegram cluster · Detected as coordinated cluster
          </div>
          <div style={{display:'flex',alignItems:'center',gap:12}}>
            <span style={{background:'#431407',color:'#fdba74',padding:'3px 10px',borderRadius:4}}>REDDIT</span>
            <span style={{color:'#6b7280'}}>T0+2h - Organic anxious replies begin, decoy cricket still top trend</span>
          </div>
        </div>
        <p style={{color:'#4b5563',fontSize:11,marginTop:16,fontStyle:'italic'}}>
          Earliest observed in monitored sources. True origin may be outside coverage area.
        </p>
      </div>
    </div>
  )
}
