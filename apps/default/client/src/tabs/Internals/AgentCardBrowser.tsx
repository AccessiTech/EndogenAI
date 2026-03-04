import type { AgentCard } from '../../api/gateway'

interface AgentCardProps {
  card: AgentCard
}

/**
 * Displays a single agent card fetched from /.well-known/agent-card.json.
 * WCAG: <article> with aria-labelledby pointing to the module name.
 */
export function AgentCardDisplay({ card }: AgentCardProps) {
  const titleId = `agent-${card.name.replace(/\s+/g, '-').toLowerCase()}`

  return (
    <article className="agent-card" aria-labelledby={titleId}>
      <h3 id={titleId} className="agent-card-name">
        {card.name}
      </h3>
      {card.description && (
        <p className="agent-card-description">{card.description}</p>
      )}
      <div className="agent-card-meta">
        <span className="badge">v{card.version}</span>
        {card.capabilities.mcp && <span className="badge">MCP</span>}
        {card.capabilities.a2a && <span className="badge">A2A</span>}
        {card.capabilities.sse && <span className="badge">SSE</span>}
        {card.neuroanatomicalAnalogue && (
          <span className="badge" title="Neuroanatomical analogue">
            {card.neuroanatomicalAnalogue}
          </span>
        )}
      </div>
      {card.url && (
        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', margin: 0 }}>
          <span aria-label="Endpoint">Endpoint:</span>{' '}
          <code>{card.url}</code>
        </p>
      )}
      {card.tools && card.tools.length > 0 && (
        <details>
          <summary style={{ cursor: 'pointer', fontSize: 'var(--font-size-sm)' }}>
            Tools ({card.tools.length})
          </summary>
          <ul style={{ marginTop: 'var(--space-2)', paddingLeft: 'var(--space-4)' }}>
            {card.tools.map((tool) => (
              <li key={tool.name} style={{ fontSize: 'var(--font-size-sm)' }}>
                <strong>{tool.name}</strong>
                {tool.description && ` — ${tool.description}`}
              </li>
            ))}
          </ul>
        </details>
      )}
    </article>
  )
}
