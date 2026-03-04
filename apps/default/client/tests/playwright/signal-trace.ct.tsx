import { test, expect } from '@playwright/experimental-ct-react'
import { SignalTraceFeed } from '../../src/tabs/Internals/SignalTraceFeed'
import type { SSEEvent } from '../../src/sse/useSSEStream'

// Inline fixtures to avoid ESM JSON import attribute requirements
const SSE_FIXTURES: SSEEvent[] = [
  {
    id: 'evt-001',
    event: 'resources/updated',
    data: JSON.stringify({
      id: 'evt-001',
      traceId: 'abc12345-0000-0000-0000-000000000001',
      source: 'working-memory',
      target: 'reasoning',
      messageType: 'context-push',
      timestamp: '2026-03-03T10:00:00.000Z',
    }),
  },
  {
    id: 'evt-002',
    event: 'resources/updated',
    data: JSON.stringify({
      id: 'evt-002',
      traceId: 'abc12345-0000-0000-0000-000000000002',
      source: 'attention-filtering',
      target: 'perception',
      messageType: 'signal-gate',
      timestamp: '2026-03-03T10:00:01.000Z',
    }),
  },
  { id: 'evt-003', event: 'mcp-push', data: JSON.stringify({ token: 'Hello', sessionId: 'session-001' }) },
  { id: 'evt-004', event: 'mcp-complete', data: JSON.stringify({ sessionId: 'session-001' }) },
]

/**
 * Component integration tests for SignalTraceFeed.
 *
 * Covers:
 * - Placeholder rendered when no events present
 * - Signal trace items rendered for resources/updated events
 * - Non-matching events (mcp-push) are ignored
 * - Source → target display in each list item
 */

test.describe('SignalTraceFeed', () => {
  test('renders placeholder when no events are provided', async ({ mount }) => {
    const component = await mount(<SignalTraceFeed sseEvents={[]} />)

    // component IS the placeholder div — assert it directly
    await expect(component).toBeVisible()
    await expect(component.getByText(/signal trace subscription not yet available/i)).toBeVisible()
  })

  test('renders trace items for resources/updated events', async ({ mount }) => {
    const traceEvents: SSEEvent[] = SSE_FIXTURES.filter(
      (e) => e.event === 'resources/updated',
    )

    const component = await mount(<SignalTraceFeed sseEvents={traceEvents} />)

    // Log role list should appear
    await expect(component.getByRole('log')).toBeVisible()

    // Both trace entries should be in the list
    const items = component.locator('.signal-trace-item')
    await expect(items).toHaveCount(2)

    // First item: working-memory → reasoning
    await expect(items.first()).toContainText('working-memory')
    await expect(items.first()).toContainText('reasoning')
    await expect(items.first()).toContainText('context-push')

    // Second item: attention-filtering → perception
    await expect(items.nth(1)).toContainText('attention-filtering')
    await expect(items.nth(1)).toContainText('perception')
    await expect(items.nth(1)).toContainText('signal-gate')
  })

  test('ignores non-resources/updated events', async ({ mount }) => {
    const mixedEvents: SSEEvent[] = SSE_FIXTURES

    const component = await mount(<SignalTraceFeed sseEvents={mixedEvents} />)

    // Only 2 of the 4 fixture events are resources/updated
    const items = component.locator('.signal-trace-item')
    await expect(items).toHaveCount(2)
  })

  test('shows traceId in truncated form on each item', async ({ mount }) => {
    const traceEvents: SSEEvent[] = SSE_FIXTURES.filter(
      (e) => e.event === 'resources/updated',
    )

    const component = await mount(<SignalTraceFeed sseEvents={traceEvents} />)

    // traceId is sliced to 8 chars in the component
    await expect(component.locator('.signal-trace-item').first()).toContainText('trace:abc12345')
  })

  test('renders gracefully when event data is not valid JSON', async ({ mount }) => {
    const badDataEvent: SSEEvent[] = [
      { id: 'bad-001', event: 'resources/updated', data: 'not-valid-json' },
    ]

    const component = await mount(<SignalTraceFeed sseEvents={badDataEvent} />)

    // Should still render 1 item (falls back to id-only)
    const items = component.locator('.signal-trace-item')
    await expect(items).toHaveCount(1)
  })
})
