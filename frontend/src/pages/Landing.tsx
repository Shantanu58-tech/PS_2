import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  ArrowRight, Fingerprint, Globe2, Lock, PlayCircle, Radar, ShieldCheck, TrendingUp, Users, Workflow,
} from 'lucide-react'
import { useSituation } from '../hooks/useApi'
import { useLive } from '../components/LiveFeed'
import { PLATFORM_LABEL } from '../lib/viz'
import { DeepastambhaMark, TAGLINE, TAGLINE_HI } from '../components/Brand'
import { useAppStore } from '../store/app'
import { STAGES } from '../lib/flow'

const Hero3D = lazy(() => import('../components/Hero3D'))

/** Counts up to `value` once it is known (skipped for reduced motion). */
function CountUp({ value }: { value?: number }) {
  const [shown, setShown] = useState(0)
  const done = useRef(false)
  useEffect(() => {
    if (value == null || done.current) return
    done.current = true
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) { setShown(value); return }
    const t0 = performance.now(), dur = 1400
    let raf = 0
    const tick = (now: number) => {
      const k = Math.min(1, (now - t0) / dur)
      setShown(Math.round(value * (1 - Math.pow(1 - k, 3))))
      if (k < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [value])
  return <>{value == null ? '—' : shown.toLocaleString('en-IN')}</>
}

function A11yBar() {
  const [scale, setScale] = useState(100)
  useEffect(() => { document.documentElement.style.fontSize = `${scale}%` }, [scale])
  return (
    <div className="gov-a11y">
      <a href="#landing-main">Skip to main content</a>
      <span className="sep" />
      <span className="row" style={{ gap: 4 }} aria-label="Text size">
        <button onClick={() => setScale(s => Math.max(90, s - 10))} aria-label="Smaller text">A−</button>
        <button onClick={() => setScale(100)} aria-label="Default text size">A</button>
        <button onClick={() => setScale(s => Math.min(125, s + 10))} aria-label="Larger text">A+</button>
      </span>
      <span className="sep" />
      <span lang="hi">{TAGLINE_HI}</span>
    </div>
  )
}

const STEP_ICON = [<Radar key="1" size={22} />, <TrendingUp key="2" size={22} />, <Fingerprint key="3" size={22} />, <ShieldCheck key="4" size={22} />]
const STEP_TEXT = [
  'One national picture: which stories are spreading, who is pushing them, and which states and sectors feel it.',
  'Every platform side by side, with trends, bursts, forecasts and the mood of real users.',
  'Find the group behind a campaign, see the network it reaches, and trace where the story started.',
  'Approve a signal and a case opens: an evidence pack whose every record can be verified.',
]

export default function Landing() {
  const navigate = useNavigate()
  const { data: sit } = useSituation()
  const { data: live } = useLive('all')
  const setTourActive = useAppStore(s => s.setTourActive)
  const k = sit?.kpis
  // newest first, but take turns between platforms so one busy app does not fill the ticker
  const headlines: any[] = (() => {
    const by = new Map<string, any[]>()
    for (const p of (live?.posts ?? []).filter((p: any) => p.kind !== 'comment')) by.set(p.platform, [...(by.get(p.platform) ?? []), p])
    const out: any[] = []
    for (let i = 0; out.length < 16 && [...by.values()].some(v => v.length > i); i++) for (const v of by.values()) if (v[i]) out.push(v[i])
    return out.slice(0, 16)
  })()

  return (
    <div className="landing">
      <A11yBar />
      <header className="gov-head">
        <Link to="/" className="row" style={{ gap: 12 }} aria-label="DEEPASTAMBHA home">
          <DeepastambhaMark size={46} />
          <span className="gov-title">
            <span><span lang="hi" className="hi">दीपस्तम्भ</span><span className="bar">|</span>DEEPASTAMBHA</span>
            <small>National Narrative Situation Room</small>
          </span>
        </Link>
        <nav className="gov-nav" aria-label="Sections">
          {STAGES.map(s => <Link key={s.id} to={s.pages[0]}>{s.label}</Link>)}
          <Link to="/situation" className="btn btn-primary btn-sm">Enter the console<ArrowRight size={14} /></Link>
        </nav>
      </header>

      <main id="landing-main">
        <section className="hero">
          <div className="hero-copy">
            <div className="hero-kicker"><span className="live-dot" style={{ border: 0, padding: 0 }}>Live</span> watching {k?.platforms ?? 6} platforms across India</div>
            <h1>Every narrative watched.<br /><span>Every record kept.</span></h1>
            <p>
              Deepastambha, the lamp tower that burns through the night, is a situation room for social media.
              It shows which stories are being pushed and by whom, where they land, and keeps every post as
              tamper-proof evidence.
            </p>
            <div className="row-wrap" style={{ gap: 12, marginTop: 26 }}>
              <button className="btn btn-primary hero-cta" onClick={() => navigate('/situation')}>Enter the Situation Room<ArrowRight size={16} /></button>
              <button className="btn hero-ghost" onClick={() => { navigate('/situation'); setTourActive(true) }}><PlayCircle size={16} />Take the guided tour</button>
            </div>
          </div>
          <div className="hero-visual">
            <Suspense fallback={<div className="hero3d" />}><Hero3D /></Suspense>
          </div>
        </section>

        <section className="stat-band" aria-label="At a glance">
          <div><b><CountUp value={k?.posts_secured} /></b><span>posts secured in the evidence chain</span></div>
          <div><b><CountUp value={k?.platforms} /></b><span>platforms watched together</span></div>
          <div><b><CountUp value={k?.states_released} /></b><span>states with reportable impact</span></div>
          <div><b><CountUp value={k?.coordinated_accounts} /></b><span>accounts found acting in sync</span></div>
        </section>

        {headlines.length > 0 && (
          <section className="ticker" aria-label="Live from social media">
            <span className="ticker-label"><span className="live-pill">LIVE</span> Social media</span>
            <div className="ticker-track">
              <div className="ticker-run">
                {[...headlines, ...headlines].map((p, i) => (
                  <a key={p.platform + p.id + i} href={p.link} target="_blank" rel="noreferrer">
                    <b>{PLATFORM_LABEL[p.platform]} · {p.source_title.replace(/\s*[-–|].*$/, '').trim()}</b> {p.text.slice(0, 110)}{p.text.length > 110 ? '…' : ''}
                  </a>
                ))}
              </div>
            </div>
          </section>
        )}

        <section className="land-section">
          <h2 className="section-title">How it works</h2>
          <p className="land-lead">One connected flow, from a national glance to evidence that holds up.</p>
          <div className="flow-cards">
            {STAGES.map((s, i) => (
              <Link key={s.id} to={s.pages[0]} className="flow-card">
                <span className="flow-card-n">{s.n}</span>
                <span className="flow-card-ic">{STEP_ICON[i]}</span>
                <b>{s.label}</b>
                <span>{STEP_TEXT[i]}</span>
                <span className="flow-card-go">Open<ArrowRight size={13} /></span>
              </Link>
            ))}
          </div>
        </section>

        <section className="land-section">
          <h2 className="section-title">Built for trust</h2>
          <div className="cap-grid">
            <div><Globe2 size={20} /><b>Six platforms</b><span>X, Telegram, Instagram, Facebook, Reddit and YouTube, in English, Hindi and Hinglish.</span></div>
            <div><Fingerprint size={20} /><b>Coordination, not guesswork</b><span>Finds accounts posting the same thing in lock-step, and shows every reason. Never labels anyone a bot.</span></div>
            <div><Workflow size={20} /><b>Organic view</b><span>One switch removes coordinated accounts, so you see what real people actually think.</span></div>
            <div><ShieldCheck size={20} /><b>Tamper-evident evidence</b><span>Every post is sealed in a hash chain with signed checkpoints anchored to Bitcoin.</span></div>
            <div><Users size={20} /><b>Private by design</b><span>Only group counts; small groups are hidden. No individual is ever profiled.</span></div>
            <div><Lock size={20} /><b>Analyst in control</b><span>Signals are reviewed by a person; every decision is recorded in the same chain.</span></div>
          </div>
        </section>
      </main>

      <footer className="gov-foot">
        <div className="gov-foot-in">
          <div className="row" style={{ gap: 10 }}><DeepastambhaMark size={34} /><span><b>DEEPASTAMBHA</b><br /><small>{TAGLINE}</small></span></div>
          <nav className="row-wrap" style={{ gap: 18 }}>
            <Link to="/situation">Situation Room</Link><Link to="/platforms">Platforms</Link>
            <Link to="/coordination">Coordinated groups</Link><Link to="/ledger">Evidence ledger</Link>
          </nav>
        </div>
      </footer>
    </div>
  )
}
