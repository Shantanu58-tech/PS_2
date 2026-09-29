import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  timeout: 180_000,
  retries: process.env.CI ? 1 : 0,
  use: { baseURL: process.env.BASE_URL || 'http://localhost:8000', trace: 'retain-on-failure' },
  projects: [{ name: 'chromium', use: { browserName: 'chromium' } }],
})
