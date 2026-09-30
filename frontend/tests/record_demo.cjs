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
    localStorage.setItem('deepastambha.theme', JSON.stringify('light'))
    localStorage.setItem('deepastambha.briefingSeen', 'true')
    localStorage.setItem('deepastambha.navCollapsed', 'false')
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

  // every number in a caption comes from the API of the server being recorded
  const api = async p => (await page.request.get(base + p)).json()
  const fmtTime = iso => new Date(iso).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', hour: 'numeric', minute: '2-digit', hour12: true, day: 'numeric', month: 'short', year: 'numeric' })
  const sit = await api('/api/situation')
  const flaggedId = sit.kpis.top_alert?.topic_id
  const lin = (await api('/api/lineage')).topics.find(t => t.topic_id === flaggedId) ?? (await api('/api/lineage')).topics[0]
  const plats = lin.platforms, P = { x: 'X', telegram: 'Telegram', instagram: 'Instagram', facebook: 'Facebook', reddit: 'Reddit', youtube: 'YouTube' }
  const hopMin = plats.length > 1 ? Math.round((new Date(plats[1].first_seen) - new Date(plats[0].first_seen)) / 60000) : 0
  const viral = (await api('/api/keywords/trending')).viral ?? []
  const vtag = viral.find(v => /dam|varunapur|evacuat|emergency/i.test(v.keyword)) ?? viral[0]
  const top = (await api('/api/influencers?limit=1')).influencers[0]
  const node = await api('/api/graph/node/' + encodeURIComponent(top.account_id))
  const sc = lin.stance_counts ?? {}

  // 0 · landing page, then title card
  await page.goto(base + '/', { waitUntil: 'networkidle' })
  await wait(1500)
  await cap('DEEPASTAMBHA: a situation room for social media.', 'The landing page, with live headlines from Telegram')
  await wait(6500)
  await cap('')
  await page.goto(base + '/situation', { waitUntil: 'networkidle' })
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
  await cap('The Situation Room answers it in one glance: what is pushed, by whom, and how it travelled.',
    plats.length > 1 ? `${P[plats[0].platform]} first, ${P[plats[1].platform]} ${hopMin} minutes later${plats.length > 2 ? `, then ${plats.length - 2} more platform${plats.length > 3 ? 's' : ''}` : ''}` : '')
  await wait(7000)
  await scrollToEl('.kpi-card')
  await cap('Every number is clickable: posts secured, priority alerts, accounts in sync, likely coordinated trends.')
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
  await cap('One click opens the detail: the rumour is marked Likely coordinated, with its burst and forecast.')
  await wait(5500)
  await page.evaluate(() => document.querySelector('.main').scrollTo(0, 99999)); await wait(800)
  await cap(vtag ? `Viral hashtags: ${vtag.keyword} spiked to ${Math.round(vtag.spike)}× its usual rate.` : 'Viral hashtags, with how far each spiked above its usual rate.')
  await wait(5000)

  // 4 · live telegram
  await page.goto(base + '/platforms?p=telegram', { waitUntil: 'networkidle' })
  await wait(1200)
  await cap('Six platforms, one view. And Telegram is connected live:', 'real posts from Indian news channels, fetched just now')
  await wait(8000)

  // 5 · coordination
  await page.goto(base + '/situation', { waitUntil: 'networkidle' }); await wait(800)
  await page.getByRole('button', { name: /Investigate the group/ }).click(); await wait(1500)
  await cap('Who is behind it? Accounts posting copy-paste text within seconds, on a clock-like rhythm.', 'A signal for review, never a "bot" label')
  await wait(5500)
  await scrollToEl('.fp-row'); await cap('Each row is an account, each tick a post. The group fires together; ordinary users do not.'); await wait(6000)

  // 5b · emotions and audience
  await page.goto(base + '/timeline', { waitUntil: 'networkidle' }); await wait(2000)
  await cap('How it makes people feel, compared with the everyday level.', 'Switch to Organic only to see ordinary users without the campaign')
  await wait(6500)
  await page.goto(base + '/audience', { waitUntil: 'networkidle' }); await wait(1500)
  await cap('Who is talking: states, languages, age groups and interests.', 'Group counts only. Small groups are hidden, and no individual is profiled')
  await wait(6500)

  // 6 · network
  await page.goto(base + '/network', { waitUntil: 'networkidle' }); await wait(3500)
  await cap('The network across apps, coloured by platform. Watch it form over the week.')
  await page.getByRole('button', { name: /Play the week/ }).click()
  await wait(15500)
  await page.goto(base + '/network?account=' + encodeURIComponent(top.account_id), { waitUntil: 'networkidle' }); await wait(2500)
  await cap(`Click any account: @${node.profile?.handle ?? top.account_id} on ${P[node.profile?.platform] ?? 'its platform'} has ${(node.profile?.followers ?? 0).toLocaleString('en-IN')} followers and was picked up by ${node.engaged_by} accounts.`)
  await wait(6500)

  // 7 · lineage
  await page.goto(base + '/situation', { waitUntil: 'networkidle' }); await wait(800)
  await page.getByRole('button', { name: /Trace the origin/ }).click(); await wait(1800)
  await cap(`The origin: ${P[plats[0].platform]} at ${fmtTime(plats[0].first_seen)}, then ${plats.slice(1).map(p => P[p.platform]).join(', ')}.`,
    `${sc.spreading ?? 0} posts spread it, ${sc.debunking ?? 0} debunk it, ${sc.questioning ?? 0} question it`)
  await wait(6000)
  await scrollToEl('.img-family')
  await cap('Edited copies of the same image are grouped automatically: cropped, re-compressed, watermarked.')
  await wait(7000)

  // 8 · review -> case
  await page.goto(base + '/situation', { waitUntil: 'networkidle' }); await wait(800)
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
  await page.goto(base + '/situation', { waitUntil: 'networkidle' }); await wait(1500)
  await cap('From a national glance, to the people behind it, to evidence that holds up, in one flow.')
  await wait(5000)
  await cap('')
  await card(`<div><div style="transform:scale(2.6);margin-bottom:56px">${logo}</div>
    <div style="font:800 42px Inter,system-ui;letter-spacing:.08em">DEEPASTAMBHA</div>
    <div style="font-size:18px;margin-top:14px;color:#E4A265">See what is trending · know what is real · prove it</div>
    <div style="font-size:15px;margin-top:30px;opacity:.75">deepastambha.onrender.com · github.com/Shantanu58-tech/PS_2</div></div>`)
  await wait(5000)
  await ctx.close()
  await browser.close()
  console.log('recorded to', `${out}/raw`)
})()
