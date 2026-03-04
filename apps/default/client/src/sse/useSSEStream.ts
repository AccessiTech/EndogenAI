import { useCallback, useEffect, useRef, useState } from 'react'

export type SSEStatus = 'idle' | 'connecting' | 'connected' | 'error' | 'closed'

export interface SSEEvent {
  id?: string
  event?: string
  data: string
}

export interface UseSSEStreamOptions {
  url: string
  token: string | null
  enabled: boolean
}

export interface UseSSEStreamResult {
  events: SSEEvent[]
  status: SSEStatus
  error: string | null
  reconnectCount: number
  clearEvents: () => void
}

const MAX_RETRIES = 5
const BASE_DELAY_MS = 1000
const MAX_DELAY_MS = 30_000

/**
 * fetch()-based SSE client — Option B decision (D8B-1).
 *
 * Uses fetch() so that Authorization: Bearer <token> can be sent with the
 * SSE connection request. EventSource cannot send arbitrary headers, making
 * it unsuitable for the MCP transport spec's auth requirements.
 *
 * Features:
 * - Exponential backoff reconnect (up to MAX_RETRIES)
 * - Last-Event-ID resumption on reconnect
 * - AbortController cleanup on unmount
 * - Parses SSE text/event-stream frames manually
 */
export function useSSEStream({ url, token, enabled }: UseSSEStreamOptions): UseSSEStreamResult {
  const [events, setEvents] = useState<SSEEvent[]>([])
  const [status, setStatus] = useState<SSEStatus>('idle')
  const [error, setError] = useState<string | null>(null)
  const [reconnectCount, setReconnectCount] = useState(0)

  const controllerRef = useRef<AbortController | null>(null)
  const lastEventIdRef = useRef<string | undefined>(undefined)
  const retryCountRef = useRef(0)
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const clearEvents = useCallback(() => setEvents([]), [])

  const connect = useCallback(async (signal: AbortSignal) => {
    setStatus('connecting')

    try {
      const headers: Record<string, string> = {
        Accept: 'text/event-stream',
        'Cache-Control': 'no-cache',
      }

      if (token) headers['Authorization'] = `Bearer ${token}`
      if (lastEventIdRef.current) headers['Last-Event-ID'] = lastEventIdRef.current

      const response = await fetch(url, { headers, signal, credentials: 'include' })

      if (!response.ok) {
        throw new Error(`SSE connection failed: ${response.status} ${response.statusText}`)
      }
      if (!response.body) {
        throw new Error('SSE response has no body')
      }

      setStatus('connected')
      setError(null)
      retryCountRef.current = 0

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const frames = buffer.split('\n\n')
        buffer = frames.pop() ?? ''

        for (const frame of frames) {
          if (!frame.trim()) continue
          const parsed = parseSSEFrame(frame)
          if (parsed) {
            if (parsed.id) lastEventIdRef.current = parsed.id
            setEvents((prev) => [...prev, parsed])
          }
        }
      }

      // Stream ended cleanly — attempt reconnect
      setStatus('closed')
      scheduleReconnect(signal)
    } catch (err) {
      if (signal.aborted) return // Normal cleanup

      const message = err instanceof Error ? err.message : 'SSE connection error'
      setError(message)
      setStatus('error')
      scheduleReconnect(signal)
    }
  }, [url, token]) // eslint-disable-line react-hooks/exhaustive-deps

  function scheduleReconnect(signal: AbortSignal) {
    if (signal.aborted) return
    if (retryCountRef.current >= MAX_RETRIES) {
      setError('Connection lost. Please reconnect manually.')
      setStatus('error')
      return
    }

    const delay = Math.min(BASE_DELAY_MS * 2 ** retryCountRef.current, MAX_DELAY_MS)
    retryCountRef.current += 1
    setReconnectCount((c) => c + 1)

    retryTimerRef.current = setTimeout(() => {
      if (!signal.aborted) void connect(signal)
    }, delay)
  }

  useEffect(() => {
    if (!enabled || !url) {
      setStatus('idle')
      return
    }

    const controller = new AbortController()
    controllerRef.current = controller
    retryCountRef.current = 0

    void connect(controller.signal)

    return () => {
      controller.abort()
      if (retryTimerRef.current) clearTimeout(retryTimerRef.current)
    }
  }, [url, token, enabled, connect])

  return { events, status, error, reconnectCount, clearEvents }
}

function parseSSEFrame(frame: string): SSEEvent | null {
  const lines = frame.split('\n')
  const event: Partial<SSEEvent> & { data: string } = { data: '' }
  const dataParts: string[] = []

  for (const line of lines) {
    if (line.startsWith('id:')) {
      event.id = line.slice(3).trim()
    } else if (line.startsWith('event:')) {
      event.event = line.slice(6).trim()
    } else if (line.startsWith('data:')) {
      dataParts.push(line.slice(5).trim())
    }
    // retry: lines are intentionally ignored — we use our own backoff
  }

  event.data = dataParts.join('\n')

  // Only return events with actual data (or an id/event for heartbeats)
  if (event.data || event.id || event.event) {
    return event as SSEEvent
  }
  return null
}
