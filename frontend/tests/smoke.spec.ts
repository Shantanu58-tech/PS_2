import { test, expect } from '@playwright/test'

// Clicks through every console route over the single-URL server (API + built UI)
// and fails on uncaught page errors or failed API calls.
const ROUTES: [string, RegExp][] = [
  ['/', /Every narrative watched/],
  ['/situation', /National Situation Room/],
  ['/timeline', /Emotions/],
  ['/platforms', /Platforms/],
  ['/trends', /Trends/],
  ['/coordination', /Coordinated groups/],
  ['/network', /Network/],
  ['/audience', /Audience/],
  ['/lineage', /Origin & spread/],
  ['/cases', /Cases/],
  ['/ledger', /Evidence ledger/],
  ['/search', /Search/],
]

for (const [path, heading] of ROUTES) {
  test(`route ${path} renders`, async ({ page }) => {
    const errors: string[] = []
    page.on('pageerror', e => errors.push(String(e)))
    page.on('response', r => { if (r.url().includes('/api/') && r.status() >= 500) errors.push(`${r.status()} ${r.url()}`) })
    await page.goto(path)
    const skip = page.getByText('Explore on my own')
    if (await skip.isVisible().catch(() => false)) await skip.click()
    await expect(page.locator('h1').first()).toHaveText(heading)
    await expect(page.getByRole('img', { name: 'DEEPASTAMBHA logo' }).first()).toBeVisible()
    expect(errors).toEqual([])
  })
}

test('ledger verify passes and tamper simulation is detected', async ({ page }) => {
  await page.goto('/ledger')
  const skip = page.getByText('Explore on my own')
  if (await skip.isVisible().catch(() => false)) await skip.click()
  await page.getByRole('button', { name: /Verify integrity/ }).click()
  await expect(page.getByText('VERIFICATION PASSED')).toBeVisible({ timeout: 90_000 })
  await page.getByRole('button', { name: /Run tamper simulation/ }).click()
  await expect(page.getByText(/Detected:/)).toBeVisible({ timeout: 90_000 })
})

test('situation room drills down in one click', async ({ page }) => {
  await page.goto('/situation')
  const skip = page.getByText('Explore on my own')
  if (await skip.isVisible().catch(() => false)) await skip.click()
  await expect(page.getByText('Situation report · India')).toBeVisible()
  await page.getByRole('button', { name: /Investigate the group/ }).click()
  await expect(page.locator('h1').first()).toHaveText(/Coordinated groups/)
  await page.goto('/situation')
  await page.locator('.sector').first().click()
  await expect(page.locator('h1').first()).toHaveText(/Trends/)
  await expect(page.getByText(/Sector:/)).toBeVisible()
})

// Phone width: every page must fit the screen (no sideways scrolling) and keep its heading.
test.describe('phone layout', () => {
  test.use({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true })
  for (const [path, heading] of ROUTES) {
    test(`route ${path} fits a phone`, async ({ page }) => {
      await page.goto(path)
      const skip = page.getByText('Explore on my own')
      if (await skip.isVisible().catch(() => false)) await skip.click()
      await expect(page.locator('h1').first()).toHaveText(heading)
      await page.waitForTimeout(800)
      // the console scrolls inside <main>, so also measure the shell's own blocks, not just the document
      const overflow = await page.evaluate(() => Math.max(document.documentElement.scrollWidth,
        ...[...document.querySelectorAll('.masthead, .flowbar, main, .landing')].map(e => e.getBoundingClientRect().right)) - window.innerWidth)
      expect(overflow).toBeLessThanOrEqual(1)
    })
  }
})
