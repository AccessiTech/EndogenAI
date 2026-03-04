import { defineConfig, devices } from '@playwright/experimental-ct-react'
import react from '@vitejs/plugin-react'

/**
 * Playwright Component Testing configuration for @endogenai/client.
 *
 * Runs component-level integration tests in a real Chromium browser.
 * Tests live in tests/playwright/ and use .ct.tsx extensions.
 *
 * Run: pnpm run test:playwright
 */
export default defineConfig({
  testDir: './tests/playwright',
  testMatch: '**/*.ct.tsx',
  snapshotDir: './tests/playwright/__snapshots__',
  timeout: 10_000,
  fullyParallel: true,
  forbidOnly: !!process.env['CI'],
  retries: process.env['CI'] ? 2 : 0,
  reporter: [['html', { open: 'never' }]],
  use: {
    ctPort: 3100,
    ctViteConfig: {
      plugins: [react()],
    },
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
