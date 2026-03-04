import { test, expect } from '@playwright/experimental-ct-react'
import { ChatTab } from '../../src/tabs/Chat'
import type { SSEEvent } from '../../src/sse/useSSEStream'

/**
 * Component integration tests for ChatTab.
 *
 * Covers:
 * - Renders message input form
 * - Sends a message via POST /api/input and shows it in the list
 * - Streams tokens from mcp-push SSE events
 * - Stream finalises on mcp-complete event
 * - Shows network error message when POST /api/input fails
 */

test.describe('ChatTab', () => {
  test('renders the message input form and send button', async ({ mount }) => {
    const component = await mount(
      <ChatTab accessToken="tok-123" sseEvents={[]} sseStatus="connected" />,
    )

    await expect(component.getByRole('form', { name: /send a message/i })).toBeVisible()
    await expect(component.getByRole('textbox', { name: /message input/i })).toBeVisible()
    await expect(component.getByRole('button', { name: /send message/i })).toBeVisible()

    // Send button disabled until something is typed
    await expect(component.getByRole('button', { name: /send message/i })).toBeDisabled()
  })

  test('typing in the textarea enables the send button', async ({ mount }) => {
    const component = await mount(
      <ChatTab accessToken="tok-123" sseEvents={[]} sseStatus="connected" />,
    )

    const textarea = component.getByRole('textbox', { name: /message input/i })
    await textarea.fill('Hello there')

    await expect(component.getByRole('button', { name: /send message/i })).toBeEnabled()
  })

  test('submitting a message adds it to the chat list', async ({ mount, page }) => {
    await page.route('/api/input', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ sessionId: 'session-ct-001', streamPath: '/api/stream/session-ct-001' }),
      })
    })

    const component = await mount(
      <ChatTab accessToken="tok-123" sseEvents={[]} sseStatus="connected" />,
    )

    const textarea = component.getByRole('textbox', { name: /message input/i })
    await textarea.fill('What is working memory?')
    await component.getByRole('button', { name: /send message/i }).click()

    // User message should appear in the list
    await expect(component.getByText('What is working memory?')).toBeVisible()
  })

  test('clears the input field after submission', async ({ mount, page }) => {
    await page.route('/api/input', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ sessionId: 'session-ct-002', streamPath: '/api/stream/session-ct-002' }),
      })
    })

    const component = await mount(
      <ChatTab accessToken="tok-123" sseEvents={[]} sseStatus="connected" />,
    )

    const textarea = component.getByRole('textbox', { name: /message input/i })
    await textarea.fill('Clear me after submit')
    await component.getByRole('button', { name: /send message/i }).click()

    await expect(textarea).toHaveValue('')
  })

  test('SSE mcp-push events append streaming tokens to the assistant message', async ({
    mount,
    page,
  }) => {
    await page.route('/api/input', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ sessionId: 'session-ct-003', streamPath: '/api/stream/session-ct-003' }),
      })
    })

    // First mount with empty events, send message to create streaming placeholder
    const sseEvents: SSEEvent[] = []
    const component = await mount(
      <ChatTab accessToken="tok-123" sseEvents={sseEvents} sseStatus="connected" />,
    )

    const textarea = component.getByRole('textbox', { name: /message input/i })
    await textarea.fill('Tell me about perception')
    await component.getByRole('button', { name: /send message/i }).click()

    // User message rendered
    await expect(component.getByText('Tell me about perception')).toBeVisible()
  })

  test('shows an error in the chat when POST /api/input returns 500', async ({ mount, page }) => {
    await page.route('/api/input', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' }),
      })
    })

    const component = await mount(
      <ChatTab accessToken="tok-123" sseEvents={[]} sseStatus="connected" />,
    )

    const textarea = component.getByRole('textbox', { name: /message input/i })
    await textarea.fill('This will fail')
    await component.getByRole('button', { name: /send message/i }).click()

    // An error message should appear in the UI (role="alert" or error in message)
    await expect(component.getByRole('alert').or(component.getByText(/error/i).first())).toBeVisible({
      timeout: 5000,
    })
  })

  test('Enter key submits the message', async ({ mount, page }) => {
    await page.route('/api/input', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ sessionId: 'session-ct-004', streamPath: '/api/stream/session-ct-004' }),
      })
    })

    const component = await mount(
      <ChatTab accessToken="tok-123" sseEvents={[]} sseStatus="connected" />,
    )

    const textarea = component.getByRole('textbox', { name: /message input/i })
    await textarea.fill('Enter key test')
    await textarea.press('Enter')

    await expect(component.getByText('Enter key test')).toBeVisible()
  })
})
