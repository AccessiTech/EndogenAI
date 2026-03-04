import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChatTab } from '../../src/tabs/Chat'
import type { SSEEvent } from '../../src/sse/useSSEStream'

// Mock gateway module
vi.mock('../../src/api/gateway', () => ({
  gateway: {
    sendInput: vi.fn().mockResolvedValue({ sessionId: 'sess-1', streamPath: '/api/stream' }),
  },
}))

function renderChat(sseEvents: SSEEvent[] = [], sseStatus = 'connected') {
  return render(
    <ChatTab
      accessToken="test-token"
      sseEvents={sseEvents}
      sseStatus={sseStatus}
    />,
  )
}

describe('ChatTab', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorage.clear()
  })

  it('renders message input with correct aria-label', () => {
    renderChat()
    const textarea = screen.getByRole('textbox', { name: /message input/i })
    expect(textarea).toBeInTheDocument()
  })

  it('renders send button with accessible name', () => {
    renderChat()
    const btn = screen.getByRole('button', { name: /send message/i })
    expect(btn).toBeInTheDocument()
  })

  it('submitting a message calls gateway.sendInput', async () => {
    const user = userEvent.setup()
    renderChat()

    const textarea = screen.getByRole('textbox', { name: /message input/i })
    await user.type(textarea, 'Hello world')
    await user.keyboard('{Enter}')

    const { gateway } = await import('../../src/api/gateway')
    await waitFor(() => expect(gateway.sendInput).toHaveBeenCalledWith(
      'test-token',
      'Hello world',
      undefined,
    ))
  })

  it('renders messages in a log list', async () => {
    const user = userEvent.setup()
    renderChat()

    const textarea = screen.getByRole('textbox', { name: /message input/i })
    await user.type(textarea, 'Test message')
    await user.keyboard('{Enter}')

    const log = screen.getByRole('log', { name: /conversation history/i })
    expect(log).toBeInTheDocument()
  })

  it('shows loading state (aria-live status) after sending a message', async () => {
    const user = userEvent.setup()
    renderChat()

    const textarea = screen.getByRole('textbox', { name: /message input/i })
    await user.type(textarea, 'Hello')
    await user.keyboard('{Enter}')

    // The conversation log should be aria-busy during streaming
    const log = screen.getByRole('log', { name: /conversation history/i })
    await waitFor(() => expect(log).toHaveAttribute('aria-busy'))
  })

  it('disables textarea and button while loading', async () => {
    const user = userEvent.setup()
    renderChat()

    const textarea = screen.getByRole('textbox', { name: /message input/i })
    const btn = screen.getByRole('button', { name: /send message/i })

    await user.type(textarea, 'Hello')
    await user.keyboard('{Enter}')

    // After submit, both should be disabled while awaiting response
    await waitFor(() => {
      expect(textarea).toBeDisabled()
      expect(btn).toBeDisabled()
    })
  })

  it('shows connection error alert when sseStatus is error', () => {
    renderChat([], 'error')
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('shift+enter does NOT submit form', async () => {
    const user = userEvent.setup()
    renderChat()

    const textarea = screen.getByRole('textbox', { name: /message input/i })
    await user.type(textarea, 'Line one')
    await user.keyboard('{Shift>}{Enter}{/Shift}')

    const { gateway } = await import('../../src/api/gateway')
    expect(gateway.sendInput).not.toHaveBeenCalled()
  })
})
