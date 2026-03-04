import { Placeholder } from './Placeholder'
import type { SSEEvent } from '../../sse/useSSEStream'

interface SignalItem {
  id: string
  traceId?: string
  source?: string
  target?: string
  messageType?: string
  timestamp: string
}

interface SignalTraceFeedProps {
  sseEvents: SSEEvent[]
}

/**
 * P1 panel — live signal trace feed from brain://group-ii/working-memory/context/current.
 * Per D5-B: renders placeholder when subscription is not yet available.
 *
 * In Phase 8B this panel shows SSE events of type "resources/updated"
 * that carry signal trace data. If none are present, the placeholder displays.
 */
export function SignalTraceFeed({ sseEvents }: SignalTraceFeedProps) {
  const traceEvents = sseEvents.filter((e) => e.event === 'resources/updated')

  if (traceEvents.length === 0) {
    return (
      <Placeholder
        message="Signal trace subscription not yet available. Activate §8.5 subscribe support in infrastructure/mcp to enable this panel."
        title="Signal trace — not yet available"
      />
    )
  }

  const items: SignalItem[] = traceEvents.map((ev, i) => {
    let parsed: Partial<SignalItem> = {}
    try {
      parsed = JSON.parse(ev.data) as Partial<SignalItem>
    } catch {
      parsed = { id: ev.id ?? `event-${i}` }
    }
    return {
      id: ev.id ?? `event-${i}`,
      traceId: parsed.traceId,
      source: parsed.source,
      target: parsed.target,
      messageType: parsed.messageType,
      timestamp: parsed.timestamp ?? new Date().toISOString(),
    }
  })

  return (
    <section aria-label="Signal trace feed">
      <ul
        role="log"
        aria-live="polite"
        aria-label="Signal trace events"
        className="signal-trace-list"
      >
        {items.map((item) => (
          <li key={item.id} className="signal-trace-item">
            <span style={{ color: 'var(--color-text-muted)' }}>
              {new Date(item.timestamp).toLocaleTimeString()}
            </span>
            {item.source && (
              <span>
                {' '}
                <strong>{item.source}</strong> → <strong>{item.target ?? '?'}</strong>
              </span>
            )}
            {item.messageType && <span> [{item.messageType}]</span>}
            {item.traceId && (
              <span style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>
                {' '}
                trace:{item.traceId.slice(0, 8)}
              </span>
            )}
          </li>
        ))}
      </ul>
    </section>
  )
}
