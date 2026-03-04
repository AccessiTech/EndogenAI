import { test, expect } from '@playwright/test'

/**
 * Phase 8B smoke test.
 *
 * Pre-requisites:
 * - Gateway running at http://localhost:3001 (pnpm dev in apps/default/server)
 * - Client built and preview running at http://localhost:5173 (pnpm preview)
 * - Phase 8A auth stub auto-approves PKCE flow
 */

test.describe('Phase 8B smoke test', () => {
  test.beforeEach(async ({ page }) => {
    // Intercept auth endpoints to simulate auto-approve flow
    await page.route('/auth/refresh', async (route) => {
      // First visit — no cookie — return 401 to trigger login page
      await route.fulfill({ status: 401 })
    })
  })

  test('renders login page when unauthenticated', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('main', { name: /sign in/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /log in/i })).toBeVisible()
  })

  test('two tabs visible after authenticated', async ({ page }) => {
    // Simulate authenticated state via refresh succeeding
    await page.route('/auth/refresh', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'test-token',
          expires_in: 900,
          token_type: 'Bearer',
        }),
      })
    })

    // Mock /api/stream to return empty stream
    await page.route('/api/stream', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache' },
        body: '',
      })
    })

    await page.goto('/')

    await expect(page.getByRole('tab', { name: /chat/i })).toBeVisible()
    await expect(page.getByRole('tab', { name: /internals/i })).toBeVisible()
  })

  test('chat tab has message input', async ({ page }) => {
    await page.route('/auth/refresh', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ access_token: 'test-token', expires_in: 900, token_type: 'Bearer' }),
      })
    })
    await page.route('/api/stream', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
        body: '',
      })
    })

    await page.goto('/')

    const chatTab = page.getByRole('tab', { name: /chat/i })
    await chatTab.click()

    await expect(page.getByRole('textbox', { name: /message input/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /send message/i })).toBeVisible()
  })

  test('switching to internals tab shows agent cards panel', async ({ page }) => {
    await page.route('/auth/refresh', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ access_token: 'test-token', expires_in: 900, token_type: 'Bearer' }),
      })
    })
    await page.route('/api/stream', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
        body: '',
      })
    })
    await page.route('/api/agents', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      })
    })

    await page.goto('/')

    const internalsTab = page.getByRole('tab', { name: /internals/i })
    await internalsTab.click()

    // Sub-panel nav should be visible
    await expect(page.getByRole('tablist', { name: /internals panels/i })).toBeVisible()
    await expect(page.getByRole('tab', { name: /agent cards/i })).toBeVisible()
  })

  test('no horizontal scroll at 320px viewport', async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 568 })
    await page.route('/auth/refresh', async (route) => {
      await route.fulfill({ status: 401 })
    })

    await page.goto('/')

    const scrollWidth = await page.evaluate(() => document.body.scrollWidth)
    const clientWidth = await page.evaluate(() => document.body.clientWidth)
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 2) // 2px tolerance
  })
})
