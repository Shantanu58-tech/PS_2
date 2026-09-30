import { lazy, Suspense, useEffect } from 'react'
import { Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { ChevronLeft, ChevronRight, PlayCircle, X } from 'lucide-react'
import Layout from './components/Layout'
import { Loading } from './components/ui'
import SituationRoom from './pages/SituationRoom'

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
import { PrahariMark, TAGLINE } from './components/Brand'

function MissionBriefing() {
  const { setShowBriefing, setTourActive } = useAppStore()
  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-labelledby="briefing-title">
      <div className="card" style={{ maxWidth: 520, width: '100%', padding: 32, textAlign: 'center' }}>
        <div style={{ display: 'flex', justifyContent: 'center' }}><PrahariMark size={92} /></div>
        <h1 id="briefing-title" style={{ fontSize: 28, fontWeight: 800, margin: '14px 0 2px', letterSpacing: '0.06em' }}>
          <span style={{ fontFamily: '"Noto Sans Devanagari", var(--font)', letterSpacing: 0 }}>प्रहरी</span>
          <span style={{ color: 'var(--accent)', margin: '0 10px', fontWeight: 400 }}>|</span>PRAHARI
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
    { route: '/', organic: false, title: 'Step 1 · The national picture',
      body: 'The Situation Room answers three questions at a glance: what is being pushed (Dam Varunapur Evacuate, 93% coordinated), by whom (a group of 72 accounts in sync) and where it lands (by sector and by state). Every tile opens the detail.' },
    { route: '/platforms', organic: false, title: 'Step 2 · Detect across platforms',
      body: 'X and Telegram, Instagram and Facebook, Reddit and YouTube in one place, each with its own activity, mood, topics and most active accounts.' },
    { route: '/trends', organic: false, title: 'Manufactured vs organic',
      body: 'The rumour is marked Manufactured; the bigger cricket buzz stays Organic. Bands are bursts, the dashed line is the forecast, viral hashtags sit at the bottom.' },
    { route: '/timeline', organic: true, title: 'Organic only',
      body: 'The switch in the top bar is now on Organic only. Gray is all activity; colour is what real users feel once coordinated accounts are removed.' },
    { route: '/coordination', organic: false, title: 'Step 3 · Investigate who is behind it',
      body: 'This group posts copy-paste text within seconds of each other, on a clock-like rhythm. PRAHARI flags the pattern for review; it never calls anyone a bot.' },
    { route: '/network', organic: false, title: 'The network, across apps',
      body: 'Nodes are coloured by platform; press Play to watch the network form over time. Click any account for its followers, connections and activity on every platform.' },
    { route: '/lineage', organic: false, title: 'Where it started',
      body: 'First seen on Telegram, then X twelve minutes later, then YouTube, Facebook, Reddit and Instagram. Edited copies of the image are matched automatically.' },
    { route: '/cases', organic: false, title: 'Step 4 · Evidence',
      body: 'Approving a signal opens a case: a ready-to-share evidence pack with ledger references and a draft legal certificate.' },
    { route: '/ledger', organic: false, title: 'Tamper-proof',
      body: 'Verify integrity, then run the tamper test: one changed character in a copy is caught at that exact post.' },
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
          <Route path="/" element={<SituationRoom />} />
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
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
        </Suspense>
      </Layout>
    </>
  )
}
