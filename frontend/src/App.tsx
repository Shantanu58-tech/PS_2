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
const Sources = lazy(() => import('./pages/Sources'))
const Compliance = lazy(() => import('./pages/Compliance'))
import { useAppStore } from './store/app'
import { useEvalSummary } from './hooks/useApi'

function MissionBriefing() {
  const { setShowBriefing, setTourActive } = useAppStore()
  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-labelledby="briefing-title">
      <div className="card" style={{ maxWidth: 600, width: '100%', padding: 28 }}>
        <div className="muted mono" style={{ fontSize: 11, letterSpacing: '0.14em' }}>SIH 2026 · PS 26152 · NTRO</div>
        <h1 id="briefing-title" style={{ fontSize: 30, margin: '6px 0 2px', letterSpacing: '0.04em' }}>PRAHARI</h1>
        <div className="secondary" style={{ marginBottom: 16 }}>प्रहरी · coordination-adjusted social media intelligence</div>
        <div className="notice crit" style={{ marginBottom: 16 }}>SIMULATED SCENARIO: fictional places, accounts and events.</div>
        <div className="stack secondary" style={{ gap: 10, fontSize: 14 }}>
          <p style={{ margin: 0 }}><b style={{ color: 'var(--ink-1)' }}>Problem.</b> Narratives, real and manufactured, spread across Telegram, X, Reddit and YouTube in English and Hinglish. Analysts cannot tell organic virality from coordinated amplification.</p>
          <p style={{ margin: 0 }}><b style={{ color: 'var(--ink-1)' }}>PRAHARI</b> detects coordinated clusters, shows every metric raw or organic-only, traces where a narrative was first seen, and keeps every record in a tamper-evident, Bitcoin-anchored ledger.</p>
          <p style={{ margin: 0 }}><b style={{ color: 'var(--ink-1)' }}>Scenario.</b> Seven days of synthetic posts: a dam-crack rumour seeded on Telegram and amplified on X by coordinated accounts, anxious organic reactions, and a bigger but genuine cricket surge as a decoy.</p>
        </div>
        <div className="row" style={{ marginTop: 22 }}>
          <button className="btn btn-primary" style={{ flex: 1, justifyContent: 'center' }} onClick={() => { setShowBriefing(false); setTourActive(true) }}>
            <PlayCircle size={16} />Start the 3-minute guided investigation
          </button>
          <button className="btn" style={{ flex: 1, justifyContent: 'center' }} onClick={() => setShowBriefing(false)}>Explore freely</button>
        </div>
      </div>
    </div>
  )
}

function GuidedTour() {
  const { tourStep, setTourStep, setTourActive, setOrganicOnly } = useAppStore()
  const navigate = useNavigate()
  const { data: ev } = useEvalSummary()
  const lead = ev?.burst?.lead_time_minutes
  const mig = ev?.lineage?.telegram_to_x_minutes
  const tamper = ev?.ledger?.tamper_detection_rate
  const STEPS = [
    { route: '/', organic: false, title: 'A Signal Card fires',
      body: `The top card is a manufactured surge: a dam-crack rumour amplified by coordinated accounts. Open "Why it fired" to see the priority formula.${lead != null ? ` In evaluation it was flagged ${lead} minutes before a keyword-volume alarm.` : ''}` },
    { route: '/trends', organic: false, title: 'Manufactured vs organic trends',
      body: 'Trends marks the rumour as a Manufactured trend, while the bigger cricket surge stays Organic. Shaded bands are Kleinberg burst windows; the purple band is the forecast.' },
    { route: '/coordination', organic: false, title: 'Why accounts are flagged',
      body: 'The cluster was flagged for synchrony, low timing entropy and near-duplicate text, and each account is scored on its own cadence. This is a statistical signal, not an accusation.' },
    { route: '/timeline', organic: true, title: 'Raw vs organic',
      body: 'The global switch is now on Organic only. Every panel compares all accounts (gray) with coordinated accounts removed (colour).' },
    { route: '/lineage', organic: false, title: 'Where it started',
      body: `The rumour was first observed on Telegram, then moved to X${mig != null ? ` about ${Math.round(mig)} minutes later` : ''}. Re-encoded and cropped copies of the meme are matched by perceptual hash.` },
    { route: '/network', organic: false, title: 'Who spreads it',
      body: 'Coordinated accounts carry a red ring. Switch to Organic only in the top bar to see how the influencer ranking changes when amplification is removed.' },
    { route: '/ledger', organic: false, title: 'Tamper-evident evidence',
      body: `Click Verify to re-check every hash, Merkle root and signature, then run the Tamper simulation: one changed character in a copy fails at that exact record.${tamper != null ? ` Evaluation: ${Math.round(tamper * 100)}% of ${ev?.ledger?.tamper_trials} tampers detected.` : ''}` },
    { route: '/cases', organic: false, title: 'Case & §63 draft',
      body: 'Open a case from a signal: the brief assembles lineage, coordination and an evidence index with ledger sequence numbers, plus a draft BSA §63 certificate for counsel review.' },
    { route: '/compliance', organic: false, title: 'PS 26152 coverage',
      body: 'Requirements A–E and the theme, each with the page that implements it and a measured number from the evaluation harness, including the limitations.' },
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
          <Route path="/sources" element={<Sources />} />
          <Route path="/compliance" element={<Compliance />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
        </Suspense>
      </Layout>
    </>
  )
}
