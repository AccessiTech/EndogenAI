import { useCallback, useEffect, useRef, useState } from 'react'
import type { Message } from './types'
import { MessageList } from './MessageList'
import { InputForm } from './InputForm'
import { gateway } from '../../api/gateway'
import type { SSEEvent } from '../../sse/useSSEStream'

const SESSION_STORAGE_KEY = 'brain_chat_messages'

interface ChatTabProps {
  accessToken: string | null
  sseEvents: SSEEvent[]
  sseStatus: string
}

/**
 * Chat tab — Global Workspace Theatre analogue.
 *
 * Manages:
 * 1. Message history (persisted to sessionStorage across page refreshes)
 * 2. POST /api/input on user submit
 * 3. Streaming token accumulation from SSE events
 * 4. Loading, error, and reconnection states
 */
export function ChatTab({ accessToken, sseEvents, sseStatus }: ChatTabProps) {
  const [messages, setMessages] = useState<Message[]>(() => {
    try {
      const stored = sessionStorage.getItem(SESSION_STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored) as Array<Omit<Message, 'timestamp'> & { timestamp: string }>
        return parsed.map((m) => ({ ...m, timestamp: new Date(m.timestamp) }))
      }
    } catch {
      // Ignore parse errors
    }
    return []
  })

  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | undefined>()
  const streamingIdRef = useRef<string | null>(null)
  const processedEventCount = useRef(0)

  // Persist messages to sessionStorage
  useEffect(() => {
    try {
      sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(messages))
    } catch {
      // Ignore storage errors
    }
  }, [messages])

  const appendToken = useCallback((token: string) => {
    if (!streamingIdRef.current) return
    const id = streamingIdRef.current
    setMessages((prev) =>
      prev.map((m) =>
        m.id === id ? { ...m, content: m.content + token } : m,
      ),
    )
  }, [])

  const finaliseStreaming = useCallback(() => {
    if (!streamingIdRef.current) return
    const id = streamingIdRef.current
    setMessages((prev) =>
      prev.map((m) => (m.id === id ? { ...m, streaming: false } : m)),
    )
    streamingIdRef.current = null
  }, [])

  const finaliseStreamingWithError = useCallback((error: string) => {
    if (!streamingIdRef.current) return
    const id = streamingIdRef.current
    setMessages((prev) =>
      prev.map((m) =>
        m.id === id ? { ...m, streaming: false, error } : m,
      ),
    )
    streamingIdRef.current = null
  }, [])

  // Process incoming SSE events
  useEffect(() => {
    const newEvents = sseEvents.slice(processedEventCount.current)
    if (newEvents.length === 0) return
    processedEventCount.current = sseEvents.length

    for (const ev of newEvents) {
      if (ev.event === 'mcp-push') {
        let tokenData: { token?: string; sessionId?: string }
        try {
          tokenData = JSON.parse(ev.data) as { token?: string; sessionId?: string }
        } catch {
          tokenData = { token: ev.data }
        }
        if (tokenData.token) {
          appendToken(tokenData.token)
        }
        setIsLoading(false)
      } else if (ev.event === 'mcp-complete') {
        finaliseStreaming()
      } else if (ev.event === 'error') {
        setIsLoading(false)
        finaliseStreamingWithError('Stream error received.')
      }
    }
  }, [sseEvents, appendToken, finaliseStreaming, finaliseStreamingWithError])

  const handleSend = useCallback(
    async (content: string) => {
      const userMsg: Message = {
        id: `user-${Date.now()}`,
        role: 'user',
        content,
        timestamp: new Date(),
      }
      const assistantId = `assistant-${Date.now()}`
      const assistantMsg: Message = {
        id: assistantId,
        role: 'assistant',
        content: '',
        streaming: true,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, userMsg, assistantMsg])
      streamingIdRef.current = assistantId
      setIsLoading(true)

      try {
        const res = await gateway.sendInput(accessToken, content, sessionId)
        setSessionId(res.sessionId)
      } catch (err) {
        setIsLoading(false)
        const message = err instanceof Error ? err.message : 'Failed to send message'
        finaliseStreamingWithError(message)
      }
    },
    [accessToken, sessionId, finaliseStreamingWithError],
  )

  const isStreaming = messages.some((m) => m.streaming)
  const inputDisabled = isLoading || isStreaming

  return (
    <section
      id="panel-chat"
      role="tabpanel"
      aria-labelledby="tab-chat"
      className="tab-panel chat-panel"
      data-active="true"
    >
      <MessageList messages={messages} isStreaming={isStreaming} />

      {isLoading && !isStreaming && (
        <div
          className="loading-indicator"
          role="status"
          aria-live="polite"
          aria-label="Waiting for response"
        >
          <span aria-hidden="true">●●●</span>
          <span>Thinking…</span>
        </div>
      )}

      {sseStatus === 'error' && (
        <div
          role="alert"
          aria-live="assertive"
          className="error-alert"
          style={{ margin: '0 var(--space-4) var(--space-2)' }}
        >
          Connection issue — responses may be delayed.
        </div>
      )}

      <InputForm onSubmit={(msg) => void handleSend(msg)} disabled={inputDisabled} />
    </section>
  )
}
