import { ReactNode, useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import {
  Activity, FileText, Fingerprint, GitBranch, Globe2, Info, LayoutDashboard, Menu, Moon, Network as NetIcon,
  PlayCircle, Search as SearchIcon, ShieldCheck, Sun, TrendingUp, Users,
} from 'lucide-react'
import { useAppStore } from '../store/app'
import { useHealth } from '../hooks/useApi'
import { useLiveStatus } from '../hooks/useLive'
import { Seg } from './ui'
import { PrahariLogo } from './Brand'

export const NAV: { group: string; items: { path: string; label: string; icon: ReactNode }[] }[] = [
  { group: 'Monitor', items: [
    { path: '/', label: 'Overview', icon: <LayoutDashboard size={19} /> },
    { path: '/platforms', label: 'Platforms', icon: <Globe2 size={19} /> },
    { path: '/trends', label: 'Trends', icon: <TrendingUp size={19} /> },
    { path: '/timeline', label: 'Emotions', icon: <Activity size={19} /> },
  ] },
  { group: 'Investigate', items: [
    { path: '/coordination', label: 'Coordination', icon: <Fingerprint size={19} /> },
    { path: '/network', label: 'Network', icon: <NetIcon size={19} /> },
    { path: '/lineage', label: 'Lineage', icon: <GitBranch size={19} /> },
    { path: '/audience', label: 'Audience', icon: <Users size={19} /> },
  ] },
  { group: 'Evidence', items: [
    { path: '/cases', label: 'Cases', icon: <FileText size={19} /> },
    { path: '/ledger', label: 'Evidence ledger', icon: <ShieldCheck size={19} /> },
  ] },
]

function LiveDot() {
  const { data: health, isError } = useHealth()
  const live = useLiveStatus()
  if (isError) return <span className="live-dot down">Offline</span>
  if (!health) return <span className="live-dot busy">Connecting</span>
  if (live?.replay?.state === 'running' || live?.analytics?.state === 'running') return <span className="live-dot busy">Updating</span>
  return <span className="live-dot">Live</span>
}

function TopSearch() {
  const navigate = useNavigate()
  const [q, setQ] = useState('')
  return (
    <form className="search-pill hide-mobile" role="search" onSubmit={e => { e.preventDefault(); if (q.trim()) navigate(`/search?q=${encodeURIComponent(q.trim())}`) }}>
      <SearchIcon size={16} />
      <input value={q} onChange={e => setQ(e.target.value)} placeholder="Search posts, hashtags, accounts…" aria-label="Search posts" />
    </form>
  )
}

export default function Layout({ children }: { children: ReactNode }) {
  const { organicOnly, setOrganicOnly, theme, setTheme, navOpen, setNavOpen, navCollapsed, setNavCollapsed, setTourActive, setShowBriefing } = useAppStore()
  const toggleNav = () => (window.matchMedia('(max-width: 760px)').matches ? setNavOpen(!navOpen) : setNavCollapsed(!navCollapsed))
  const location = useLocation()
  useEffect(() => setNavOpen(false), [location.pathname, setNavOpen])

  return (
    <div className={`shell ${navCollapsed ? 'collapsed' : ''}`}>
      <div className={`nav-backdrop ${navOpen ? 'open' : ''}`} onClick={() => setNavOpen(false)} aria-hidden="true" />
      <aside id="primary-nav" className={`sidebar ${navOpen ? 'open' : ''}`} aria-label="Primary navigation">
        <div className="brand"><Link to="/" aria-label="PRAHARI home"><PrahariLogo size={36} compact={navCollapsed && !navOpen} /></Link></div>
        <nav className="nav">
          {NAV.map(g => (
            <div key={g.group}>
              <div className="nav-group">{g.group}</div>
              {g.items.map(n => (
                <NavLink key={n.path} to={n.path} end={n.path === '/'} title={n.label} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                  {n.icon}<span>{n.label}</span>
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-foot stack" style={{ gap: 2 }}>
          <button className="nav-link" style={{ border: 0, background: 'transparent', cursor: 'pointer', font: 'inherit', textAlign: 'left' }} title="Guided tour" onClick={() => setTourActive(true)}>
            <PlayCircle size={19} /><span>Guided tour</span>
          </button>
          <button className="nav-link" style={{ border: 0, background: 'transparent', cursor: 'pointer', font: 'inherit', textAlign: 'left' }} title="About PRAHARI" onClick={() => setShowBriefing(true)}>
            <Info size={19} /><span>About PRAHARI</span>
          </button>
        </div>
      </aside>
      <main className="main" id="main">
        <header className="topbar">
          <div className="topbar-inner">
            <button className="hamburger" aria-label="Toggle menu" aria-controls="primary-nav" aria-expanded={navCollapsed ? navOpen : !navCollapsed} onClick={toggleNav}><Menu size={21} /></button>
            <TopSearch />
            <span style={{ marginLeft: 'auto' }} />
            <Seg label="Which accounts to count" value={organicOnly ? 'organic' : 'raw'} onChange={v => setOrganicOnly(v === 'organic')} options={[
              { value: 'raw', label: 'All activity' },
              { value: 'organic', label: 'Organic only' },
            ]} />
            <span className="hide-mobile"><LiveDot /></span>
            <button className="icon-btn" aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
              {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
            </button>
          </div>
        </header>
        <div className="page">{children}</div>
      </main>
    </div>
  )
}
