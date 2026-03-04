import type { Message } from './types'

interface MessageItemProps {
  message: Message
}

/**
 * Individual message bubble.
 * WCAG: role="article", aria-label describing role + content summary.
 */
export function MessageItem({ message }: MessageItemProps) {
  const { role, content, streaming, error } = message
  const ariaLabel = role === 'user' ? 'Your message' : 'Assistant message'

  return (
    <article
      className="message-item"
      data-role={role}
      aria-label={ariaLabel}
    >
      <div className="message-bubble">
        {content}
        {streaming && (
          <span aria-hidden="true" className="cursor-blink">
            ▌
          </span>
        )}
      </div>
      {error && (
        <div role="alert" className="message-error" aria-live="assertive">
          {error}
        </div>
      )}
      <time
        className="message-meta"
        dateTime={message.timestamp.toISOString()}
        aria-label={`Sent at ${message.timestamp.toLocaleTimeString()}`}
      >
        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </time>
    </article>
  )
}
