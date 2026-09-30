import { lazy, Suspense, useEffect } from 'react'
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { ChevronLeft, ChevronRight, PlayCircle, X } from 'lucide-react'
import Layout from './components/Layout'
import { Loading } from './components/ui'
import SituationRoom from './pages/SituationRoom'
import Landing from './pages/Landing'

// Route-level code splitting: only the landing page ships in the first bundle.
const TimelineEmotions = lazy(() => import('./pages/TimelineEmotions'))
const Trends = lazy(() => import('./pages/Trends'))
const Platforms = lazy(() => import('./pages/Platforms'))
const Coordination = lazy(() => import('./pages/Coordination'))
const Network = lazy(() => import('./pages/Network'))
const Audience = lazy(() => import('./pages/Audience'))
const Lineage = lazy(() => import('./pages/Lineage'))
const CaseFile = lazy(() => import('./pages/CaseFile'))
const Ledger = lazy(() => import('./pages/Ledger'))
const Search = lazy(() => import('./pages/Search'))
import { useAppStore } from './store/app'
import { DeepastambhaMark, TAGLINE } from './components/Brand'

function MissionBriefing() {
  const { setShowBriefing, setTourActive } = useAppStore()
  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-labelledby="briefing-title">
      <div className="card" style={{ maxWidth: 520, width: '100%', padding: 32, textAlign: 'center' }}>
        <div style={{ display: 'flex', justifyContent: 'center' }}><DeepastambhaMark size={92} /></div>
        <h1 id="briefing-title" style={{ fontSize: 24, fontWeight: 800, margin: '14px 0 2px', letterSpacing: '0.06em' }}>
          <span style={{ fontFamily: '"Noto Sans Devanagari", var(--font)', letterSpacing: 0 }}>दीपस्तम्भ</span>
          <span style={{ color: 'var(--accent)', margin: '0 10px', fontWeight: 400 }}>|</span>DEEPASTAMBHA
        </h1>
        <div className="muted" style={{ fontSize: 13 }}>National Narrative Situation Room</div>
        <div style={{ margin: '6px 0 18px', fontSize: 13.5, fontWeight: 600, color: 'var(--accent-ink)' }}>{TAGLINE}</div>
        <p className="secondary" style={{ margin: '0 auto', fontSize: 15, maxWidth: 420 }}>
          One national picture of what is happening on social media: which narratives are being pushed, by which coordinated groups, and where the impact lands. From that overview, investigate, then secure the evidence.
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
    { route: '/situation', organic: false, title: '1 · The national picture',
      body: 'This page shows the stories spreading right now, and which sectors and states they reach. The red card is the one story the system thinks needs attention first.' },
    { route: '/platforms', organic: false, title: '2 · Each app on its own',
      body: 'Pick any app to see its busiest topics, its most active accounts and how people there feel.' },
    { route: '/trends', organic: false, title: '3 · Real buzz or a push?',
      body: '“Likely coordinated” means many accounts posted the same thing at the same moment. Ordinary buzz, like cricket chatter, is marked Organic.' },
    { route: '/timeline', organic: true, title: '4 · How people feel',
      body: 'We switched on “Organic only”, which hides the coordinated accounts. The coloured lines now show how ordinary users really feel.' },
    { route: '/coordination', organic: false, title: '5 · Who is pushing it',
      body: 'These accounts posted near-identical text within seconds of each other, again and again. The page shows the evidence and leaves the judgement to an analyst.' },
    { route: '/network', organic: false, title: '6 · Who reaches whom',
      body: 'Each dot is an account and each line is a reply, repost or forward. Press Play to watch the story spread, or click a dot for details.' },
    { route: '/lineage', organic: false, title: '7 · Where it started',
      body: 'This traces the story back to the first post we saw and shows how it hopped between apps. Edited copies of the same image are matched too.' },
    { route: '/cases', organic: false, title: '8 · Build the case',
      body: 'Approving a signal opens a case: the posts, charts and ledger references packed into one shareable file.' },
    { route: '/ledger', organic: false, title: '9 · Prove nothing changed',
      body: 'Every post is sealed when it is collected. Press Verify to check that none was altered, or run the tamper test to see a change caught.' },
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
  const { pathname } = useLocation()
  if (pathname === '/') return <Landing />
  return (
    <>
      {showBriefing && <MissionBriefing />}
      {tourActive && <GuidedTour />}
      <Layout>
        <Suspense fallback={<Loading label="Loading view" />}>
        <Routes>
          <Route path="/situation" element={<SituationRoom />} />
          <Route path="/timeline" element={<TimelineEmotions />} />
          <Route path="/trends" element={<Trends />} />
          <Route path="/platforms" element={<Platforms />} />
          <Route path="/coordination" element={<Coordination />} />
          <Route path="/network" element={<Network />} />
          <Route path="/audience" element={<Audience />} />
          <Route path="/lineage" element={<Lineage />} />
          <Route path="/cases" element={<CaseFile />} />
          <Route path="/ledger" element={<Ledger />} />
          <Route path="/search" element={<Search />} />
          <Route path="*" element={<Navigate to="/situation" />} />
        </Routes>
        </Suspense>
      </Layout>
    </>
  )
}
