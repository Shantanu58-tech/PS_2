import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import CommandCenter from './pages/CommandCenter'
import TimelineEmotions from './pages/TimelineEmotions'
import Trends from './pages/Trends'
import Network from './pages/Network'
import Audience from './pages/Audience'
import Lineage from './pages/Lineage'
import CaseFile from './pages/CaseFile'
import Ledger from './pages/Ledger'
import Search from './pages/Search'
import Compliance from './pages/Compliance'
import { useAppStore } from './store/app'

function MissionBriefing() {
  const { setShowBriefing, setTourActive } = useAppStore()
  return (
    <div style={{position:'fixed',inset:0,zIndex:50,display:'flex',alignItems:'center',justifyContent:'center',background:'rgba(0,0,0,0.92)'}}>
      <div style={{maxWidth:560,width:'100%',margin:'0 16px',background:'#0d1326',border:'1px solid #1e2740',borderRadius:16,padding:32}}>
        <div style={{textAlign:'center',marginBottom:24}}>
          <div style={{fontSize:32,fontWeight:700,color:'white'}}>PRAHARI</div>
          <div style={{fontSize:12,color:'#3b82f6',fontFamily:'monospace'}}>NARRATIVE INTELLIGENCE PLATFORM · SIH 2026 · PS 26152</div>
        </div>
        <div style={{background:'rgba(161,51,0,0.2)',border:'1px solid #7c2d12',borderRadius:8,padding:12,marginBottom:20,textAlign:'center'}}>
          <span style={{color:'#fca5a5',fontSize:13,fontWeight:600}}>⚠ SIMULATED SCENARIO — no real persons or events</span>
        </div>
        <div style={{color:'#9ca3af',fontSize:14,lineHeight:1.7,marginBottom:24}}>
          <p><strong style={{color:'white'}}>Problem:</strong> Social media narratives — real and manufactured — spread across Telegram, X, Reddit, and YouTube in Hinglish and English. Analysts cannot distinguish organic virality from coordinated amplification.</p>
          <p style={{marginTop:8}}><strong style={{color:'white'}}>PRAHARI:</strong> Detects coordinated clusters, separates organic from manufactured sentiment, traces narrative lineage cross-platform, and assembles tamper-proof evidence cases.</p>
          <p style={{marginTop:8}}><strong style={{color:'white'}}>Demo:</strong> 7-day seeded scenario: cricket surge (organic), dam-scare rumour (60 coordinated accounts), anxious organic reactions.</p>
        </div>
        <div style={{display:'flex',gap:12}}>
          <button onClick={() => { setShowBriefing(false); setTourActive(true) }}
            style={{flex:1,background:'#3b82f6',color:'white',border:'none',borderRadius:8,padding:'12px 16px',fontSize:14,fontWeight:600,cursor:'pointer'}}>
            ▶ Start 3-min Guided Tour
          </button>
          <button onClick={() => setShowBriefing(false)}
            style={{flex:1,background:'#1e2740',color:'#e2e8f0',border:'none',borderRadius:8,padding:'12px 16px',fontSize:14,fontWeight:600,cursor:'pointer'}}>
            Explore Freely
          </button>
        </div>
      </div>
    </div>
  )
}

function GuidedTour() {
  const { tourStep, setTourStep, setTourActive } = useAppStore()
  const STEPS = [
    { title: 'Signal Card Fired', desc: 'A manufactured surge is detected: coordinated accounts amplifying a false dam-scare that moved from Telegram to X. The card shows its priority score and why it fired.' },
    { title: 'Raw vs Organic Toggle', desc: 'Enable "Organic only" in the sidebar to exclude coordinated accounts and see how much they distorted the emotion timeline (measured in the eval report).' },
    { title: 'Narrative Lineage', desc: 'The dam-scare meme is traced to its earliest observed post and platform, with the migration time to X and image variants matched by perceptual hash.' },
    { title: 'Network & KOLs', desc: 'A bridge account connects two communities. Coordinated accounts are marked. The organic-only recompute shows who really influences versus who is being amplified.' },
    { title: 'Tamper-Proof Ledger', desc: 'Click Verify to re-check every hash and signature. Tamper Simulation mutates one record in a scratch copy and verification fails at that exact sequence number.' },
    { title: 'Case & §63 Draft', desc: 'Create a case from any alert. Auto-assembles brief with Merkle root. §63 draft certificate generated (DRAFT label, needs counsel review).' },
    { title: 'PS 26152 Compliance', desc: 'Every requirement A–E plus the Blockchain theme, with metrics read from eval/reports/summary.json (or "not yet measured"). Limitations stated openly.' },
  ]
  const step = STEPS[tourStep]
  if (!step) return null
  return (
    <div style={{position:'fixed',bottom:24,right:24,zIndex:40,maxWidth:340,width:'100%',background:'#111827',border:'1px solid #3b82f6',borderRadius:12,padding:20,boxShadow:'0 20px 60px rgba(0,0,0,0.5)'}}>
      <div style={{display:'flex',justifyContent:'space-between',marginBottom:8}}>
        <span style={{fontSize:11,color:'#3b82f6',fontFamily:'monospace'}}>STEP {tourStep+1}/{STEPS.length}</span>
        <button onClick={() => setTourActive(false)} style={{background:'none',border:'none',color:'#6b7280',cursor:'pointer',fontSize:18}}>×</button>
      </div>
      <div style={{color:'white',fontWeight:600,marginBottom:8}}>{step.title}</div>
      <p style={{color:'#9ca3af',fontSize:13,lineHeight:1.6,marginBottom:16}}>{step.desc}</p>
      <div style={{display:'flex',gap:8}}>
        <button onClick={() => { if (tourStep < STEPS.length-1) setTourStep(tourStep+1); else setTourActive(false) }}
          style={{flex:1,background:'#3b82f6',color:'white',border:'none',borderRadius:8,padding:'8px 12px',fontSize:13,fontWeight:600,cursor:'pointer'}}>
          {tourStep < STEPS.length-1 ? 'Next →' : 'Finish'}
        </button>
        <button onClick={() => setTourActive(false)}
          style={{background:'#1e2740',color:'#9ca3af',border:'none',borderRadius:8,padding:'8px 12px',fontSize:13,cursor:'pointer'}}>Skip</button>
      </div>
      <div style={{display:'flex',gap:3,marginTop:12}}>
        {STEPS.map((_,i) => <div key={i} style={{height:3,flex:1,borderRadius:2,background:i<=tourStep?'#3b82f6':'#253454'}} />)}
      </div>
    </div>
  )
}

export default function App() {
  const { showBriefing, tourActive } = useAppStore()
  return (
    <div style={{minHeight:'100vh',background:'#0a0e1a'}}>
      {showBriefing && <MissionBriefing />}
      {tourActive && <GuidedTour />}
      <Layout>
        <Routes>
          <Route path="/" element={<CommandCenter />} />
          <Route path="/timeline" element={<TimelineEmotions />} />
          <Route path="/trends" element={<Trends />} />
          <Route path="/network" element={<Network />} />
          <Route path="/audience" element={<Audience />} />
          <Route path="/lineage" element={<Lineage />} />
          <Route path="/cases" element={<CaseFile />} />
          <Route path="/ledger" element={<Ledger />} />
          <Route path="/search" element={<Search />} />
          <Route path="/compliance" element={<Compliance />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Layout>
    </div>
  )
}
