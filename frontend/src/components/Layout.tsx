import { ReactNode, useEffect } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  Activity, BookOpenCheck, Database, FileText, Fingerprint, GitBranch, Menu, Moon, Network as NetIcon,
  Radar, Search as SearchIcon, ShieldCheck, Sun, TrendingUp, Users, PlayCircle,
} from 'lucide-react'
import { useAppStore } from '../store/app'
import { useHealth } from '../hooks/useApi'
import { useLiveStatus } from '../hooks/useLive'
import { Seg } from './ui'

export const NAV: { group: string; items: { path: string; label: string; code: string; icon: ReactNode }[] }[] = [
  { group: 'Monitor', items: [
    { path: '/', label: 'Command Center', code: 'OVR', icon: <Radar size={16} /> },
    { path: '/timeline', label: 'Timeline & Emotions', code: 'B', icon: <Activity size={16} /> },
    { path: '/trends', label: 'Trends', code: 'D', icon: <TrendingUp size={16} /> },
  ] },
  { group: 'Investigate', items: [
    { path: '/coordination', label: 'Coordination', code: 'V2', icon: <Fingerprint size={16} /> },
    { path: '/network', label: 'Network', code: 'E', icon: <NetIcon size={16} /> },
    { path: '/lineage', label: 'Lineage', code: 'V3', icon: <GitBranch size={16} /> },
    { path: '/audience', label: 'Audience', code: 'C', icon: <Users size={16} /> },
    { path: '/search', label: 'Search', code: 'FTS', icon: <SearchIcon size={16} /> },
  ] },
  { group: 'Evidence', items: [
    { path: '/cases', label: 'Cases', code: 'CASE', icon: <FileText size={16} /> },
    { path: '/ledger', label: 'Ledger', code: 'LDG', icon: <ShieldCheck size={16} /> },
  ] },
  { group: 'System', items: [
    { path: '/sources', label: 'Sources', code: 'A', icon: <Database size={16} /> },
    { path: '/compliance', label: 'PS 26152 & Eval', code: 'PS', icon: <BookOpenCheck size={16} /> },
  ] },
]

function EngineStatus() {
  const { data: health, isError } = useHealth()
  const live = useLiveStatus()
  const analytics = live?.analytics
  const replay = live?.replay
  if (isError) return <span className="badge status-critical">Engine unreachable</span>
  if (!health) return <span className="badge">Connecting…</span>
  if (replay?.state === 'running') {
    return <span className="badge status-warning">Replay {Math.round((replay.ingested / Math.max(1, replay.total)) * 100)}%</span>
  }
  if (analytics?.state === 'running') return <span className="badge status-warning">Analytics: {analytics.stage ?? 'running'}</span>
  return (
    <span className="row">
      <span className="badge status-good" title={`${health.service} v${health.version}`}>Engine online</span>
      <span className="badge">{health.mode === 'live' ? 'LIVE' : 'REPLAY'}</span>
      {health.demo_readonly && <span className="badge" title="Public demo: ingestion and configuration are disabled">Read-only demo</span>}
    </span>
  )
}

export default function Layout({ children }: { children: ReactNode }) {
  const { organicOnly, setOrganicOnly, theme, setTheme, navOpen, setNavOpen, setTourActive } = useAppStore()
  const location = useLocation()
  useEffect(() => setNavOpen(false), [location.pathname, setNavOpen])

  return (
    <div className="shell">
      <div className="shell-banner sim-banner" role="note">
        SIMULATED SCENARIO — fictional places, accounts and events · PRAHARI · SIH 2026 · PS 26152 (NTRO) · Team MOGGERS, VIT Pune
      </div>
      <aside className={`sidebar ${navOpen ? 'open' : ''}`} aria-label="Primary navigation">
        <div className="brand">
          <div className="brand-name">PRAHARI</div>
          <div className="brand-sub">प्रहरी · narrative intelligence</div>
        </div>
        <nav className="nav">
          {NAV.map(g => (
            <div key={g.group}>
              <div className="nav-group">{g.group}</div>
              {g.items.map(n => (
                <NavLink key={n.path} to={n.path} end={n.path === '/'} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                  {n.icon}<span>{n.label}</span><span className="code">{n.code}</span>
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-foot stack" style={{ gap: 8 }}>
          <button className="btn btn-sm" onClick={() => setTourActive(true)}><PlayCircle size={14} />Guided investigation</button>
          <span className="muted" style={{ fontSize: 11 }}>Times shown in IST · data is synthetic</span>
        </div>
      </aside>
      <main className="main" id="main">
        <div className="topbar">
          <div className="topbar-inner">
            <button className="btn btn-ghost btn-sm mobile-only" aria-label="Open navigation" onClick={() => setNavOpen(!navOpen)}><Menu size={16} /></button>
            <Seg label="Analytics view" value={organicOnly ? 'organic' : 'raw'} onChange={v => setOrganicOnly(v === 'organic')} options={[
              { value: 'raw', label: 'Raw' },
              { value: 'organic', label: 'Organic only' },
            ]} />
            <span className="muted" style={{ fontSize: 12 }}>
              {organicOnly ? 'Coordinated accounts (score ≥ 0.7) removed from every view' : 'All accounts, including coordinated amplification'}
            </span>
            <span style={{ marginLeft: 'auto' }} />
            <EngineStatus />
            <button className="btn btn-ghost btn-sm" aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
              {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
            </button>
          </div>
        </div>
        <div className="page">{children}</div>
      </main>
    </div>
  )
}

