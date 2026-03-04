import { useEffect, useState } from 'react'
import type { AgentCard, AgentEntry } from '../../api/gateway'
import { gateway } from '../../api/gateway'
import { AgentCardDisplay } from './AgentCardBrowser'
import { Placeholder } from './Placeholder'

interface AgentCardBrowserPanelProps {
  accessToken: string | null
}

/**
 * P0 panel — fetches all agent cards from the gateway and displays them.
 * Data flow per D5-C: GET /api/agents → list of agent URLs → per-agent card fetch.
 */
export function AgentCardBrowserPanel({ accessToken }: AgentCardBrowserPanelProps) {
  const [cards, setCards] = useState<AgentCard[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadCards() {
      setLoading(true)
      setError(null)
      try {
        const agents = await gateway.listAgents(accessToken)
        const fetched: AgentCard[] = []
        for (const agent of agents as AgentEntry[]) {
          try {
            const card = await gateway.fetchAgentCard(accessToken, agent.url)
            fetched.push(card)
          } catch {
            // Skip individual failed cards gracefully
            fetched.push({
              name: agent.name,
              version: 'unknown',
              description: 'Agent card unavailable',
              url: agent.url,
              capabilities: { mcp: false, a2a: false },
            })
          }
        }
        if (!cancelled) setCards(fetched)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load agents')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void loadCards()
    return () => { cancelled = true }
  }, [accessToken])

  if (loading) {
    return (
      <div role="status" aria-live="polite" aria-label="Loading agent cards">
        <span className="sr-only">Loading agent cards…</span>
        <div className="placeholder-panel">
          <p>Loading agent cards…</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div role="alert" className="error-alert" aria-live="assertive">
        Failed to load agent cards: {error}
      </div>
    )
  }

  if (cards.length === 0) {
    return (
      <Placeholder
        message="No agents registered. Start the gateway and register modules."
        title="No agents available"
      />
    )
  }

  return (
    <section aria-label="Agent cards">
      <div className="internals-grid">
        {cards.map((card) => (
          <AgentCardDisplay key={card.name} card={card} />
        ))}
      </div>
    </section>
  )
}
