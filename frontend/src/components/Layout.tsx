import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAppStore } from '../store/app'
import { useCollectors } from '../hooks/useApi'

const NAV = [
  { path: '/', label: 'Command Center', icon: '⚡' },
  { path: '/timeline', label: 'Timeline', icon: '📊' },
  { path: '/trends', label: 'Trends', icon: '📈' },
  { path: '/network', label: 'Network', icon: '🕸' },
  { path: '/audience', label: 'Audience', icon: '👥' },
  { path: '/lineage', label: 'Lineage', icon: '🔗' },
  { path: '/cases', label: 'Cases', icon: '📁' },
  { path: '/ledger', label: 'Ledger', icon: '🔒' },
  { path: '/search', label: 'Search', icon: '🔍' },
  { path: '/compliance', label: 'PS 26152 ✅', icon: '📋' },
]

export default function Layout({ children }: { children: ReactNode }) {
  const location = useLocation()
  const { organicOnly, setOrganicOnly } = useAppStore()
  const { data: collectors } = useCollectors()

  return (
    <div style={{display:'flex',flexDirection:'column',height:'100vh'}}>
      <div style={{background:'linear-gradient(90deg,#7c2d12,#991b1b)',color:'#fca5a5',padding:'6px 16px',fontSize:11,fontWeight:600,textAlign:'center',letterSpacing:'0.05em'}}>
        ⚠ SIMULATED SCENARIO — no real persons or events · PRAHARI v1.0 · SIH 2026 · PS 26152 (NTRO) · Team MOGGERS, VIT Pune
      </div>
      <div style={{display:'flex',flex:1,overflow:'hidden'}}>
        <aside style={{width:180,background:'#0d1326',borderRight:'1px solid #1e2740',display:'flex',flexDirection:'column',flexShrink:0}}>
          <div style={{padding:'16px',borderBottom:'1px solid #1e2740'}}>
            <div style={{fontSize:16,fontWeight:700,color:'white'}}>PRAHARI</div>
            <div style={{fontSize:10,color:'#6b7280',fontFamily:'monospace'}}>NARRATIVE INTEL</div>
          </div>
          <nav style={{flex:1,overflowY:'auto',padding:'8px 0'}}>
            {NAV.map(n => (
              <Link key={n.path} to={n.path} style={{
                display:'flex',alignItems:'center',gap:8,padding:'10px 16px',fontSize:12,textDecoration:'none',transition:'all 0.15s',
                background: location.pathname === n.path ? '#1e2740' : 'transparent',
                color: location.pathname === n.path ? 'white' : '#9ca3af',
              }}>
                <span>{n.icon}</span><span>{n.label}</span>
              </Link>
            ))}
          </nav>
          <div style={{padding:12,borderTop:'1px solid #1e2740'}}>
            <label style={{display:'flex',alignItems:'center',gap:6,cursor:'pointer'}}>
              <input type="checkbox" checked={organicOnly} onChange={e => setOrganicOnly(e.target.checked)} />
              <span style={{fontSize:11,color:'#9ca3af'}}>Organic only</span>
            </label>
            <div style={{marginTop:8,fontSize:10,color:'#4b5563'}}>
              {collectors?.collectors && Object.entries(collectors.collectors).map(([name, s]: any) => (
                <div key={name} style={{display:'flex',justifyContent:'space-between'}}>
                  <span>{name}</span>
                  <span style={{color:s.status==='ok'?'#22c55e':'#4b5563'}}>{s.status}</span>
                </div>
              ))}
            </div>
          </div>
        </aside>
        <main style={{flex:1,overflowY:'auto',padding:24}}>
          {children}
        </main>
      </div>
    </div>
  )
}
