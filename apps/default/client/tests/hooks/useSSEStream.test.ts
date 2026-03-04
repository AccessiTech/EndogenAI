import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useSSEStream } from '../../src/sse/useSSEStream'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeSSEBody(lines: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder()
  return new ReadableStream({
    start(controller) {
      for (const line of lines) {
        controller.enqueue(encoder.encode(line))
      }
      controller.close()
    },
  })
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('useSSEStream', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.unstubAllGlobals()
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
    vi.useRealTimers()
  })

  it('sends Authorization: Bearer header in fetch call', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      body: makeSSEBody(['data: hello\n\n']),
    })
    vi.stubGlobal('fetch', fetchMock)

    const { result } = renderHook(() =>
      useSSEStream({ url: '/api/stream', token: 'test-token-123', enabled: true }),
    )

    await waitFor(() => expect(fetchMock).toHaveBeenCalled())

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect((options.headers as Record<string, string>)['Authorization']).toBe(
      'Bearer test-token-123',
    )
    expect(result.current).toBeDefined()
  })

  it('parses data: lines from SSE stream and updates events array', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      body: makeSSEBody([
        'event: mcp-push\ndata: {"token":"Hello"}\n\n',
        'event: mcp-push\ndata: {"token":" world"}\n\n',
      ]),
    })
    vi.stubGlobal('fetch', fetchMock)

    const { result } = renderHook(() =>
      useSSEStream({ url: '/api/stream', token: 'tok', enabled: true }),
    )

    await waitFor(() => result.current.events.length >= 2, { timeout: 3000 })

    expect(result.current.events[0]?.data).toBe('{"token":"Hello"}')
    expect(result.current.events[0]?.event).toBe('mcp-push')
    expect(result.current.events[1]?.data).toBe('{"token":" world"}')
  })

  it('sends Last-Event-ID header on reconnect after stream ends', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: false })
    const encoder = new TextEncoder()

    let callCount = 0
    const fetchMock = vi.fn().mockImplementation(() => {
      callCount++
      if (callCount === 1) {
        return Promise.resolve({
          ok: true,
          body: new ReadableStream({
            start(ctl) {
              ctl.enqueue(encoder.encode('id: evt-42\ndata: test\n\n'))
              ctl.close()
            },
          }),
        })
      }
      // Hang forever on second call so we can inspect headers
      return Promise.resolve({
        ok: true,
        body: new ReadableStream({ start() {} }),
      })
    })
    vi.stubGlobal('fetch', fetchMock)

    renderHook(() =>
      useSSEStream({ url: '/api/stream', token: 'tok', enabled: true }),
    )

    // Flush all pending microtasks so the first stream is fully read
    await act(async () => {
      await Promise.resolve()
      await Promise.resolve()
      await Promise.resolve()
    })

    // First fetch should have been called
    expect(callCount).toBe(1)

    // Advance fake time past the 1000ms reconnect delay
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1500)
    })

    // Second fetch should now have been called
    expect(callCount).toBe(2)

    const secondCall = fetchMock.mock.calls[1] as [string, RequestInit] | undefined
    expect(secondCall).toBeDefined()
    if (secondCall) {
      const [, secondOptions] = secondCall
      expect((secondOptions.headers as Record<string, string>)['Last-Event-ID']).toBe('evt-42')
    }
  })

  it('cleans up AbortController on unmount', async () => {
    const abortMock = vi.fn()
    const mockAbortController = { abort: abortMock, signal: { aborted: false } as AbortSignal }
    vi.stubGlobal('AbortController', vi.fn().mockReturnValue(mockAbortController))

    vi.stubGlobal('fetch', vi.fn().mockReturnValue(new Promise(() => {}))) // Never resolves

    const { unmount } = renderHook(() =>
      useSSEStream({ url: '/api/stream', token: 'tok', enabled: true }),
    )

    unmount()

    expect(abortMock).toHaveBeenCalled()
  })

  it('transitions to connecting status when enabled', async () => {
    // Hook immediately calls connect(), transitioning to 'connecting'
    vi.stubGlobal('fetch', vi.fn().mockReturnValue(new Promise(() => {}))) // Never resolves

    const { result } = renderHook(() =>
      useSSEStream({ url: '/api/stream', token: 'tok', enabled: true }),
    )

    // By the time the first render + effect runs, status should be 'connecting'
    await waitFor(() => result.current.status === 'connecting')
    expect(result.current.status).toBe('connecting')
  })

  it('does not connect when enabled=false', () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    renderHook(() =>
      useSSEStream({ url: '/api/stream', token: 'tok', enabled: false }),
    )

    expect(fetchMock).not.toHaveBeenCalled()
  })
})
