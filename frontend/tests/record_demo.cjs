// Records a captioned screen demo of DEEPASTAMBHA following the video script.
//   node tests/record_demo.cjs <baseUrl> <outDir>
// Output: <outDir>/raw/*.webm (convert with ffmpeg to mp4). Captions are drawn in-page.
const { chromium } = require('playwright')

const base = process.argv[2] || 'http://127.0.0.1:8000'
const out = process.argv[3] || 'demo_video'
const W = 1440, H = 900

const CAPTION_JS = () => {
  window.__cap = (text, sub) => {
    let el = document.getElementById('__cap')
    if (!el) {
      el = document.createElement('div'); el.id = '__cap'
      Object.assign(el.style, { position: 'fixed', left: '50%', bottom: '26px', transform: 'translateX(-50%)', zIndex: 99999,
        maxWidth: '980px', padding: '14px 22px', borderRadius: '10px', background: 'rgba(28,20,14,0.88)', color: '#fff',
        font: '600 19px/1.45 Inter, system-ui, sans-serif', textAlign: 'center', boxShadow: '0 10px 30px rgba(0,0,0,.35)',
        transition: 'opacity .25s', pointerEvents: 'none' })
      document.body.appendChild(el)
    }
    el.innerHTML = text + (sub ? `<div style="font-weight:500;font-size:14px;opacity:.8;margin-top:4px">${sub}</div>` : '')
    el.style.opacity = text ? '1' : '0'
  }
  window.__card = (html) => {
    let el = document.getElementById('__card')
    if (!html) { if (el) el.remove(); return }
    if (!el) {
      el = document.createElement('div'); el.id = '__card'
      Object.assign(el.style, { position: 'fixed', inset: '0', zIndex: 100000, display: 'grid', placeItems: 'center',
        background: 'linear-gradient(180deg,#3E342F,#1C140E)', color: '#F8F5F0', font: '500 18px Inter, system-ui, sans-serif', textAlign: 'center' })
      document.body.appendChild(el)
    }
    el.innerHTML = html
  }
}

const LOGO = () => document.querySelector('svg[aria-label$="logo"]')?.outerHTML || ''

;(async () => {
  const browser = await chromium.launch()
  const ctx = await browser.newContext({ viewport: { width: W, height: H }, recordVideo: { dir: `${out}/raw`, size: { width: W, height: H } } })
  await ctx.addInitScript(() => {
    localStorage.setItem('prahari.theme', JSON.stringify('light'))
    localStorage.setItem('prahari.briefingSeen', 'true')
    localStorage.setItem('prahari.navCollapsed', 'false')
  })
  await ctx.addInitScript(CAPTION_JS)
  const page = await ctx.newPage()
  const wait = ms => page.waitForTimeout(ms)
  const cap = (t, s) => page.evaluate(([a, b]) => window.__cap(a, b), [t, s || ''])
  const card = html => page.evaluate(h => window.__card(h), html)
  const scrollTo = async (y, steps = 12) => {
    const from = await page.evaluate(() => document.querySelector('.main').scrollTop)
    for (let i = 1; i <= steps; i++) {
      await page.evaluate(v => document.querySelector('.main').scrollTo(0, v), from + ((y - from) * i) / steps)
      await wait(45)
    }
  }
  const scrollToEl = async sel => {
    const y = await page.evaluate(s => { const e = document.querySelector(s); const m = document.querySelector('.main')
      return e ? e.getBoundingClientRect().top + m.scrollTop - 150 : 0 }, sel)
    await scrollTo(y)
  }

  // 0 · title card
  await page.goto(base + '/', { waitUntil: 'networkidle' })
  const logo = await page.evaluate(LOGO)
  await card(`<div><div style="transform:scale(3.2);margin-bottom:70px">${logo}</div>
    <div style="font:800 48px Inter,system-ui;letter-spacing:.08em">DEEPASTAMBHA</div>
    <div style="font-size:24px;margin-top:6px">दीपस्तम्भ · National Narrative Situation Room</div>
    <div style="font-size:18px;margin-top:22px;color:#E4A265">Every narrative watched. Every record kept.</div>
    <div style="font-size:14px;margin-top:40px;opacity:.7">SIH 2026 · PS 26152 · Team MOGGERS</div></div>`)
  await wait(6000)
  await card('')

  // 1 · situation report
  await cap('A rumour says a dam has cracked. Within an hour it is everywhere.', 'Is the panic real, or is someone pushing it?')
  await wait(5000)
  await cap('The Situation Room answers it in one glance: what is pushed, by whom, and how it travelled.', 'Telegram first, X 12 minutes later, then four more platforms')
  await wait(7000)
  await scrollToEl('.kpi-card')
  await cap('Every number is live and clickable: posts secured, priority alerts, accounts in sync, manufactured trends.')
  await wait(5500)

  // 2 · map and narratives
  await scrollToEl('.tilemap')
  await page.selectOption('select[aria-label="Map metric"]', 'anxiety')
  await cap('Impact by state, from public profile locations only, never an individual profile.')
  await wait(3500)
  const mh = page.locator('button.tile[aria-label^="maharashtra"]')
  if (await mh.count()) { await mh.click(); await cap('Maharashtra: what people talk about, how anxious they are, where the pushed narrative landed.'); await wait(5500)
    await page.locator('.drawer button[aria-label="Close"]').click() }
  await cap('The narrative, the coordinated group behind it, and its most active amplifiers.')
  await wait(5000)

  // 3 · sectors -> trends
  await scrollToEl('.sector-grid')
  await cap('Impact by sector: Critical Infrastructure is critical; the bigger cricket buzz is organic.')
  await wait(5000)
  await page.locator('.sector.critical').first().click()
  await wait(1500)
  await cap('One click opens the detail: the rumour is marked Manufactured, with its burst and forecast.')
  await wait(5500)
  await page.evaluate(() => document.querySelector('.main').scrollTo(0, 99999)); await wait(800)
  await cap('Viral hashtags: #VarunapurDam spiked to 95× its usual rate.')
  await wait(5000)

  // 4 · live telegram
  await page.goto(base + '/platforms?p=telegram', { waitUntil: 'networkidle' })
  await wait(1200)
  await cap('Six platforms, one view. And Telegram is connected live:', 'real posts from Indian news channels, fetched just now')
  await wait(8000)

  // 5 · coordination
  await page.goto(base + '/', { waitUntil: 'networkidle' }); await wait(800)
  await page.getByRole('button', { name: /Investigate the group/ }).click(); await wait(1500)
  await cap('Who is behind it? Accounts posting copy-paste text within seconds, on a clock-like rhythm.', 'A signal for review, never a "bot" label')
  await wait(5500)
  await scrollToEl('.recharts-wrapper'); await wait(4000)

  // 6 · network
  await page.goto(base + '/network', { waitUntil: 'networkidle' }); await wait(3500)
  await cap('The network across apps, coloured by platform. Watch it form over the week.')
  await page.getByRole('button', { name: /Play the week/ }).click()
  await wait(15500)
  await page.goto(base + '/network?account=acc_tgchannel_1', { waitUntil: 'networkidle' }); await wait(2500)
  await cap('Click any account: this Telegram channel has 12,000 followers and was forwarded by 66 accounts on X.')
  await wait(6500)

  // 7 · lineage
  await page.goto(base + '/', { waitUntil: 'networkidle' }); await wait(800)
  await page.getByRole('button', { name: /Trace the origin/ }).click(); await wait(1800)
  await cap('The origin: Telegram at 10:10 pm, then X, YouTube, Facebook, Reddit and Instagram.', 'Edited copies of the image are matched automatically')
  await wait(7000)

  // 8 · review -> case
  await page.goto(base + '/', { waitUntil: 'networkidle' }); await wait(800)
  await scrollToEl('#signals')
  await cap('The analyst approves the signal. The decision is sealed in the evidence chain.')
  await wait(3500)
  await page.getByRole('button', { name: /Approve → case/ }).first().click()
  await wait(3500)
  await cap('A case opens with a ready-to-share evidence pack and a draft legal certificate.')
  await wait(6000)

  // 9 · ledger
  await page.goto(base + '/ledger', { waitUntil: 'networkidle' }); await wait(1000)
  await cap('Every post and every decision is tamper-evident.')
  await page.getByRole('button', { name: /Verify integrity/ }).click()
  await page.getByText('VERIFICATION PASSED').waitFor({ timeout: 90000 }); await wait(2500)
  await cap('Now change one character in a copy of the evidence…')
  await page.getByRole('button', { name: /Run tamper simulation/ }).click()
  await page.getByText(/Detected:/).waitFor({ timeout: 90000 }); await wait(1000)
  await cap('…and it is caught at that exact record.')
  await wait(5000)

  // 10 · end card
  await page.goto(base + '/', { waitUntil: 'networkidle' }); await wait(1500)
  await cap('From a national glance, to the people behind it, to evidence that holds up, in one flow.')
  await wait(5000)
  await cap('')
  await card(`<div><div style="transform:scale(2.6);margin-bottom:56px">${logo}</div>
    <div style="font:800 42px Inter,system-ui;letter-spacing:.08em">DEEPASTAMBHA</div>
    <div style="font-size:18px;margin-top:14px;color:#E4A265">See what is trending · know what is real · prove it</div>
    <div style="font-size:15px;margin-top:30px;opacity:.75">prahari-h849.onrender.com · github.com/Shantanu58-tech/PS_2</div></div>`)
  await wait(5000)
  await ctx.close()
  await browser.close()
  console.log('recorded to', `${out}/raw`)
})()
