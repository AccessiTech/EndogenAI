import { useEffect, useRef } from 'react'
import type { Message } from './types'
import { MessageItem } from './MessageItem'

interface MessageListProps {
  messages: Message[]
  isStreaming: boolean
}

/**
 * Scrollable conversation history.
 * WCAG:
 * - role="log" for a live region that records conversation history
 * - aria-live="polite" announces new messages without interruption
 * - aria-label provides a visible accessible name
 */
export function MessageList({ messages, isStreaming }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <ul
      role="log"
      aria-live="polite"
      aria-label="Conversation history"
      aria-busy={isStreaming}
      className="chat-messages"
    >
      {messages.length === 0 && (
        <li
          style={{
            color: 'var(--color-text-muted)',
            textAlign: 'center',
            padding: 'var(--space-8)',
          }}
          aria-label="No messages yet — start the conversation"
        >
          Start a conversation…
        </li>
      )}
      {messages.map((msg) => (
        <li key={msg.id}>
          <MessageItem message={msg} />
        </li>
      ))}
      <div ref={bottomRef} aria-hidden="true" />
    </ul>
  )
}
