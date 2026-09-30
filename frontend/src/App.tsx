import { lazy, Suspense, useEffect } from 'react'
import { Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { ChevronLeft, ChevronRight, PlayCircle, X } from 'lucide-react'
import Layout from './components/Layout'
import { Loading } from './components/ui'
import CommandCenter from './pages/CommandCenter'

// Route-level code splitting: only the landing page ships in the first bundle.
const TimelineEmotions = lazy(() => import('./pages/TimelineEmotions'))
const Trends = lazy(() => import('./pages/Trends'))
const Coordination = lazy(() => import('./pages/Coordination'))
const Network = lazy(() => import('./pages/Network'))
const Audience = lazy(() => import('./pages/Audience'))
const Lineage = lazy(() => import('./pages/Lineage'))
const CaseFile = lazy(() => import('./pages/CaseFile'))
const Ledger = lazy(() => import('./pages/Ledger'))
const Search = lazy(() => import('./pages/Search'))
import { useAppStore } from './store/app'
import { PrahariMark } from './components/Brand'

function MissionBriefing() {
  const { setShowBriefing, setTourActive } = useAppStore()
  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-labelledby="briefing-title">
      <div className="card" style={{ maxWidth: 520, width: '100%', padding: 32, textAlign: 'center' }}>
        <div style={{ display: 'flex', justifyContent: 'center' }}><PrahariMark size={64} /></div>
        <h1 id="briefing-title" style={{ fontSize: 30, fontWeight: 800, margin: '14px 0 2px', letterSpacing: '0.06em' }}>PRAHARI</h1>
        <div className="muted" style={{ marginBottom: 18 }}>प्रहरी · the sentinel for social media narratives</div>
        <p className="secondary" style={{ margin: '0 auto', fontSize: 15, maxWidth: 420 }}>
          See what is trending, tell genuine buzz from coordinated campaigns, trace where a story started, and keep every post as tamper-proof evidence.
        </p>
        <div className="row" style={{ marginTop: 26, flexWrap: 'wrap', justifyContent: 'center' }}>
          <button className="btn btn-primary" onClick={() => { setShowBriefing(false); setTourActive(true) }}>
            <PlayCircle size={16} />Take the guided tour
          </button>
          <button className="btn" onClick={() => setShowBriefing(false)}>Explore on my own</button>
        </div>
      </div>
    </div>
  )
}

function GuidedTour() {
  const { tourStep, setTourStep, setTourActive, setOrganicOnly } = useAppStore()
  const navigate = useNavigate()
  const STEPS = [
    { route: '/', organic: false, title: 'A signal fires',
      body: 'The top signal is a manufactured surge: a dam-crack rumour pushed by accounts acting in sync. Open "Why it fired" to see what drove its priority.' },
    { route: '/trends', organic: false, title: 'Manufactured vs organic',
      body: 'The rumour is marked Manufactured, while the bigger cricket buzz stays Organic. Shaded bands are bursts; the dashed line is the forecast.' },
    { route: '/coordination', organic: false, title: 'Accounts acting in sync',
      body: 'This group posts copy-paste text within seconds of each other, on a clock-like rhythm. PRAHARI flags the pattern for review; it never calls anyone a bot.' },
    { route: '/timeline', organic: true, title: 'Organic only',
      body: 'The switch in the top bar is now on Organic only. Gray is all activity; colour is what real users feel once coordinated accounts are removed.' },
    { route: '/lineage', organic: false, title: 'Where it started',
      body: 'The rumour first appeared on Telegram and jumped to X minutes later. Cropped and re-compressed copies of its image are matched automatically.' },
    { route: '/network', organic: false, title: 'Who spreads it',
      body: 'Accounts acting in sync carry a red ring. Flip to Organic only to see who genuinely drives the conversation.' },
    { route: '/ledger', organic: false, title: 'Tamper-proof evidence',
      body: 'Click Verify integrity, then run the Tamper test: changing a single character in a copy is caught at that exact post.' },
    { route: '/cases', organic: false, title: 'Build a case',
      body: 'Start a case from any signal to get a ready-to-share evidence pack, with a draft legal certificate.' },
  ]
  const step = STEPS[tourStep]
  useEffect(() => {
    if (!step) return
    navigate(step.route)
    setOrganicOnly(step.organic)
  }, [tourStep]) // eslint-disable-line react-hooks/exhaustive-deps
  if (!step) return null
  const last = tourStep === STEPS.length - 1
  return (
    <div className="tour card" role="dialog" aria-label="Guided investigation" style={{ padding: 18, borderColor: 'var(--accent)' }}>
      <div className="spread" style={{ marginBottom: 6 }}>
        <span className="mono muted" style={{ fontSize: 11 }}>STEP {tourStep + 1} / {STEPS.length}</span>
        <button className="btn btn-ghost btn-sm" aria-label="Close tour" onClick={() => setTourActive(false)}><X size={14} /></button>
      </div>
      <h2 style={{ fontSize: 15, margin: '0 0 6px' }}>{step.title}</h2>
      <p className="secondary" style={{ margin: 0, fontSize: 13 }}>{step.body}</p>
      <div className="row" style={{ marginTop: 14 }}>
        <button className="btn btn-sm" disabled={tourStep === 0} onClick={() => setTourStep(tourStep - 1)}><ChevronLeft size={14} />Back</button>
        <button className="btn btn-sm btn-primary" onClick={() => (last ? setTourActive(false) : setTourStep(tourStep + 1))}>
          {last ? 'Finish' : 'Next'}{!last && <ChevronRight size={14} />}
        </button>
        <div className="row" style={{ marginLeft: 'auto', gap: 3 }} aria-hidden="true">
          {STEPS.map((_, i) => <span key={i} style={{ width: 14, height: 3, borderRadius: 2, background: i <= tourStep ? 'var(--accent)' : 'var(--surface-3)' }} />)}
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const { showBriefing, tourActive } = useAppStore()
  return (
    <>
      {showBriefing && <MissionBriefing />}
      {tourActive && <GuidedTour />}
      <Layout>
        <Suspense fallback={<Loading label="Loading view" />}>
        <Routes>
          <Route path="/" element={<CommandCenter />} />
          <Route path="/timeline" element={<TimelineEmotions />} />
          <Route path="/trends" element={<Trends />} />
          <Route path="/coordination" element={<Coordination />} />
          <Route path="/network" element={<Network />} />
          <Route path="/audience" element={<Audience />} />
          <Route path="/lineage" element={<Lineage />} />
          <Route path="/cases" element={<CaseFile />} />
          <Route path="/ledger" element={<Ledger />} />
          <Route path="/search" element={<Search />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
        </Suspense>
      </Layout>
    </>
  )
}
