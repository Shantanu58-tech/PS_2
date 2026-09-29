import { test, expect } from '@playwright/test'

// Clicks through every console route over the single-URL server (API + built UI)
// and fails on uncaught page errors or failed API calls.
const ROUTES: [string, RegExp][] = [
  ['/', /Command Center/],
  ['/timeline', /Timeline & Emotions/],
  ['/trends', /Trends & topic detection/],
  ['/coordination', /Coordination detector/],
  ['/network', /Network & influence/],
  ['/audience', /Audience/],
  ['/lineage', /Narrative lineage/],
  ['/cases', /Case files/],
  ['/ledger', /Evidence ledger/],
  ['/search', /Search/],
  ['/sources', /Sources & collectors/],
  ['/compliance', /Problem statement coverage/],
]

for (const [path, heading] of ROUTES) {
  test(`route ${path} renders`, async ({ page }) => {
    const errors: string[] = []
    page.on('pageerror', e => errors.push(String(e)))
    page.on('response', r => { if (r.url().includes('/api/') && r.status() >= 500) errors.push(`${r.status()} ${r.url()}`) })
    await page.goto(path)
    const skip = page.getByText('Explore freely')
    if (await skip.isVisible().catch(() => false)) await skip.click()
    await expect(page.locator('h1').first()).toHaveText(heading)
    await expect(page.getByText('SIMULATED SCENARIO').first()).toBeVisible()
    expect(errors).toEqual([])
  })
}

test('ledger verify passes and tamper simulation is detected', async ({ page }) => {
  await page.goto('/ledger')
  const skip = page.getByText('Explore freely')
  if (await skip.isVisible().catch(() => false)) await skip.click()
  await page.getByRole('button', { name: /Verify integrity/ }).click()
  await expect(page.getByText('VERIFICATION PASSED')).toBeVisible({ timeout: 90_000 })
  await page.getByRole('button', { name: /Run tamper simulation/ }).click()
  await expect(page.getByText(/Detected:/)).toBeVisible({ timeout: 90_000 })
})
