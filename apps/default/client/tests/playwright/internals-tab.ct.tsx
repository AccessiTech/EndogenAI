import { test, expect } from '@playwright/experimental-ct-react'
import { InternalsTab } from '../../src/tabs/Internals'
import type { SSEEvent } from '../../src/sse/useSSEStream'

/**
 * Component integration tests for InternalsTab.
 *
 * Covers:
 * - Tab renders with Agent Cards panel active by default
 * - Sub-panel navigation: clicking each tab shows its panel
 * - Keyboard ArrowRight navigation cycles through panels
 * - Signal Trace panel shows placeholder when no SSE events
 * - Signal Trace panel renders items when resources/updated events are provided
 * - Memory and Confidence panels show placeholders
 */

const AGENT_CARD = {
  name: 'test-agent',
  version: '1.0.0',
  description: 'A test agent',
  url: 'http://localhost:9999',
  capabilities: { mcp: true, a2a: false, sse: false },
}

test.describe('InternalsTab', () => {
  test('renders the internals tablist with 5 panels', async ({ mount, page }) => {
    await page.route('/api/agents', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }),
    )

    const component = await mount(
      <InternalsTab accessToken="tok-123" sseEvents={[]} />,
    )

    const tablist = component.getByRole('tablist', { name: /internals panels/i })
    await expect(tablist).toBeVisible()

    // All 5 sub-tabs should be present
    await expect(tablist.getByRole('tab', { name: /agent cards/i })).toBeVisible()
    await expect(tablist.getByRole('tab', { name: /collections/i })).toBeVisible()
    await expect(tablist.getByRole('tab', { name: /signal trace/i })).toBeVisible()
    await expect(tablist.getByRole('tab', { name: /working memory/i })).toBeVisible()
    await expect(tablist.getByRole('tab', { name: /confidence/i })).toBeVisible()
  })

  test('Agent Cards is the active tab by default', async ({ mount, page }) => {
    await page.route('/api/agents', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }),
    )

    const component = await mount(
      <InternalsTab accessToken="tok-123" sseEvents={[]} />,
    )

    await expect(
      component.getByRole('tab', { name: /agent cards/i }),
    ).toHaveAttribute('aria-selected', 'true')
  })

  test('clicking Collections shows the collections panel', async ({ mount, page }) => {
    await page.route('/api/agents', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }),
    )
    await page.route('**/api/resources', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ resources: [], total: 0 }),
      }),
    )

    const component = await mount(
      <InternalsTab accessToken="tok-123" sseEvents={[]} />,
    )

    await component.getByRole('tab', { name: /collections/i }).click()

    await expect(
      component.getByRole('tab', { name: /collections/i }),
    ).toHaveAttribute('aria-selected', 'true')
    // Collections panel is now visible — shows placeholder for empty resources
    await expect(component.getByText(/no resource collections found/i)).toBeVisible({
      timeout: 5000,
    })
  })

  test('clicking Signal Trace shows placeholder when no SSE events', async ({ mount, page }) => {
    await page.route('/api/agents', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }),
    )

    const component = await mount(
      <InternalsTab accessToken="tok-123" sseEvents={[]} />,
    )

    await component.getByRole('tab', { name: /signal trace/i }).click()

    await expect(
      component.getByText(/signal trace subscription not yet available/i),
    ).toBeVisible()
  })

  test('Signal Trace panel renders trace items from SSE events', async ({ mount, page }) => {
    await page.route('/api/agents', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }),
    )

    const traceEvents: SSEEvent[] = [
      {
        id: 'e1',
        event: 'resources/updated',
        data: JSON.stringify({
          traceId: 'trace-001',
          source: 'attention-filter',
          target: 'perception',
          messageType: 'signal-gate',
          timestamp: new Date().toISOString(),
        }),
      },
    ]

    const component = await mount(
      <InternalsTab accessToken="tok-123" sseEvents={traceEvents} />,
    )

    await component.getByRole('tab', { name: /signal trace/i }).click()

    await expect(component.getByRole('log')).toBeVisible()
    await expect(component.locator('.signal-trace-item')).toHaveCount(1)
    await expect(component.locator('.signal-trace-item').first()).toContainText('attention-filter')
  })

  test('Working Memory tab shows placeholder in default state', async ({ mount, page }) => {
    await page.route('/api/agents', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }),
    )

    const component = await mount(
      <InternalsTab accessToken="tok-123" sseEvents={[]} />,
    )

    await component.getByRole('tab', { name: /working memory/i }).click()

    await expect(
      component.getByText(/working memory inspector not yet available/i),
    ).toBeVisible()
  })

  test('Confidence tab shows placeholder in default state', async ({ mount, page }) => {
    await page.route('/api/agents', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }),
    )

    const component = await mount(
      <InternalsTab accessToken="tok-123" sseEvents={[]} />,
    )

    await component.getByRole('tab', { name: /confidence/i }).click()

    await expect(
      component.getByText(/confidence scores not yet available/i),
    ).toBeVisible()
  })

  test('ArrowRight key navigates to the next sub-panel tab', async ({ mount, page }) => {
    await page.route('/api/agents', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }),
    )

    const component = await mount(
      <InternalsTab accessToken="tok-123" sseEvents={[]} />,
    )

    // Focus Agent Cards tab (first tab, already selected)
    const agentCardsTab = component.getByRole('tab', { name: /agent cards/i })
    await agentCardsTab.focus()
    await agentCardsTab.press('ArrowRight')

    // Should move to Collections
    await expect(
      component.getByRole('tab', { name: /collections/i }),
    ).toHaveAttribute('aria-selected', 'true')
  })
})
