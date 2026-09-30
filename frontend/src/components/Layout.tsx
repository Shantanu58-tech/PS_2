import { Fragment, ReactNode, useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import {
  Activity, ArrowRight, ChevronRight, FileText, Fingerprint, GitBranch, Globe2, Info, Menu, Moon, Network as NetIcon,
  PlayCircle, Radar, Search as SearchIcon, ShieldCheck, Sun, TrendingUp, Users, Workflow,
} from 'lucide-react'
import { useAppStore } from '../store/app'
import { useHealth, useSituation, useCases } from '../hooks/useApi'
import { useLiveStatus } from '../hooks/useLive'
import { Seg } from './ui'
import { DeepastambhaMark } from './Brand'
import { NEXT, STAGES, stageOf } from '../lib/flow'

type Item = { path: string; label: string; icon: ReactNode; count?: (d: any) => { text: string; hot?: boolean } | null }

export const NAV: { group: string; items: Item[] }[] = [
  { group: '1 · Situation', items: [
    { path: '/situation', label: 'Situation Room', icon: <Radar size={18} />,
      count: s => s?.sitrep?.level === 'critical' ? { text: 'Critical', hot: true } : null },
  ] },
  { group: '2 · Detect', items: [
    { path: '/platforms', label: 'Platforms', icon: <Globe2 size={18} />, count: s => s ? { text: `${s.kpis.platforms}` } : null },
    { path: '/trends', label: 'Trends', icon: <TrendingUp size={18} />,
      count: s => s?.kpis.manufactured_trends ? { text: `${s.kpis.manufactured_trends} pushed`, hot: true } : null },
    { path: '/timeline', label: 'Emotions', icon: <Activity size={18} /> },
  ] },
  { group: '3 · Investigate', items: [
    { path: '/coordination', label: 'Coordination', icon: <Fingerprint size={18} />,
      count: s => s?.kpis.coordinated_accounts ? { text: `${s.kpis.coordinated_accounts} sync`, hot: true } : null },
    { path: '/network', label: 'Network', icon: <NetIcon size={18} /> },
    { path: '/lineage', label: 'Lineage', icon: <GitBranch size={18} /> },
    { path: '/audience', label: 'Audience', icon: <Users size={18} />, count: s => s ? { text: `${s.kpis.states_released} states` } : null },
  ] },
  { group: '4 · Evidence', items: [
    { path: '/cases', label: 'Cases', icon: <FileText size={18} /> },
    { path: '/ledger', label: 'Evidence ledger', icon: <ShieldCheck size={18} /> },
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
      <input value={q} onChange={e => setQ(e.target.value)} placeholder="Search posts, hashtags, accounts, claims…" aria-label="Search posts" />
    </form>
  )
}

function FlowBar() {
  const { pathname } = useLocation()
  const current = stageOf(pathname)
  const next = NEXT[pathname]
  return (
    <nav className="flowbar" aria-label="Operational flow">
      <div className="flowbar-inner">
        <span className="flow-label"><Workflow size={15} />Operational flow</span>
        {STAGES.map((s, i) => (
          <Fragment key={s.id}>
            {i > 0 && <ChevronRight size={15} className="flow-sep" aria-hidden="true" />}
            <Link to={s.pages[0]} className={`flow-step ${s.id === current.id ? 'active' : s.n < current.n ? 'done' : ''}`}
              aria-current={s.id === current.id ? 'step' : undefined}>
              <span className="n">{s.n}</span>{s.label}<span className="d hide-mobile">{s.desc}</span>
            </Link>
          </Fragment>
        ))}
        {next && <span className="flow-hint">Next: <Link to={next.to}>{next.label}</Link><ArrowRight size={13} /></span>}
      </div>
    </nav>
  )
}

export default function Layout({ children }: { children: ReactNode }) {
  const { organicOnly, setOrganicOnly, theme, setTheme, navOpen, setNavOpen, navCollapsed, setNavCollapsed, setTourActive, setShowBriefing } = useAppStore()
  const location = useLocation()
  const { data: sit } = useSituation()
  const { data: cases } = useCases()
  useEffect(() => setNavOpen(false), [location.pathname, setNavOpen])
  const toggleNav = () => (window.matchMedia('(max-width: 760px)').matches ? setNavOpen(!navOpen) : setNavCollapsed(!navCollapsed))
  const nCases = cases?.cases?.length ?? 0

  return (
    <div className={`shell ${navCollapsed ? 'collapsed' : ''}`}>
      <header className="masthead">
        <div className="masthead-inner">
          <button className="hamburger" aria-label="Toggle menu" aria-controls="primary-nav" aria-expanded={navCollapsed ? navOpen : !navCollapsed} onClick={toggleNav}><Menu size={21} /></button>
          <Link to="/" aria-label="DEEPASTAMBHA home" className="row" style={{ gap: 10 }}>
            <DeepastambhaMark size={34} />
            <span className="brand-word" style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.15 }}>
              <span style={{ fontWeight: 800, fontSize: 18, letterSpacing: '0.08em' }}>DEEPASTAMBHA</span>
              <span className="brand-sub">दीपस्तम्भ · National Narrative Situation Room</span>
            </span>
          </Link>
          <TopSearch />
          <Seg label="Which accounts to count" value={organicOnly ? 'organic' : 'raw'} onChange={v => setOrganicOnly(v === 'organic')} options={[
            { value: 'raw', label: <><span className="hide-mobile">All activity</span><span className="mobile-inline">All</span></> },
            { value: 'organic', label: <><span className="hide-mobile">Organic only</span><span className="mobile-inline">Organic</span></> },
          ]} />
          <span className="hide-mobile"><LiveDot /></span>
          <button className="icon-btn" aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
            {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
          </button>
        </div>
      </header>
      <FlowBar />
      <div className={`nav-backdrop ${navOpen ? 'open' : ''}`} onClick={() => setNavOpen(false)} aria-hidden="true" />
      <aside id="primary-nav" className={`sidebar ${navOpen ? 'open' : ''}`} aria-label="Primary navigation">
        <nav className="nav">
          {NAV.map(g => (
            <div key={g.group}>
              <div className="nav-group">{g.group}</div>
              {g.items.map(n => {
                const c = n.path === '/cases' ? (nCases ? { text: `${nCases}` } : null) : n.count?.(sit)
                return (
                  <NavLink key={n.path} to={n.path} end title={n.label} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                    {n.icon}<span>{n.label}</span>{c && <em className={`count ${c.hot ? 'warn' : ''}`} style={{ fontStyle: 'normal' }}>{c.text}</em>}
                  </NavLink>
                )
              })}
            </div>
          ))}
        </nav>
        <div className="sidebar-foot stack" style={{ gap: 1 }}>
          <button className="nav-link" style={{ border: 0, background: 'transparent', cursor: 'pointer', font: 'inherit', textAlign: 'left' }} title="Guided tour" onClick={() => setTourActive(true)}>
            <PlayCircle size={18} /><span>Guided tour</span>
          </button>
          <button className="nav-link" style={{ border: 0, background: 'transparent', cursor: 'pointer', font: 'inherit', textAlign: 'left' }} title="About DEEPASTAMBHA" onClick={() => setShowBriefing(true)}>
            <Info size={18} /><span>About DEEPASTAMBHA</span>
          </button>
        </div>
      </aside>
      <main className="main" id="main">
        <div className="page">{children}</div>
      </main>
    </div>
  )
}
