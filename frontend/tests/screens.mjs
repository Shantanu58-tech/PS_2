// Visual review helper: screenshot every route in dark and light themes.
//   node tests/screens.mjs http://127.0.0.1:8777 <outdir>
import { chromium } from 'playwright'
import fs from 'fs'

const base = process.argv[2] || 'http://127.0.0.1:8000'
const out = process.argv[3] || 'screens'
fs.mkdirSync(out, { recursive: true })
const routes = ['/', '/situation', '/platforms', '/platforms?p=telegram', '/timeline', '/trends', '/coordination', '/network', '/lineage', '/audience', '/cases', '/ledger', '/search?q=dam']
const browser = await chromium.launch()
for (const theme of ['dark', 'light']) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 })
  await ctx.addInitScript(t => {
    localStorage.setItem('deepastambha.theme', JSON.stringify(t))
    localStorage.setItem('deepastambha.briefingSeen', 'true')
  }, theme)
  const page = await ctx.newPage()
  const errors = []
  page.on('pageerror', e => errors.push(String(e)))
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()) })
  for (const r of routes) {
    await page.goto(base + r, { waitUntil: 'networkidle' })
    await page.waitForTimeout(r === '/network' ? 4000 : 1200)
    const name = `${theme}_${r === '/' ? 'landing' : r.slice(1).replace(/[?=]/g, '_')}.png`
    await page.screenshot({ path: `${out}/${name}`, fullPage: false })
  }
  if (theme === 'dark') { // also a mobile view and the briefing
    const m = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 })
    const mp = await m.newPage()
    await mp.goto(base + '/', { waitUntil: 'networkidle' })
    await mp.waitForTimeout(1200)
    await mp.screenshot({ path: `${out}/mobile_briefing.png` })
  }
  console.log(theme, errors.length ? `errors: ${errors.slice(0, 5).join(' | ')}` : 'no console errors')
  await ctx.close()
}
await browser.close()
