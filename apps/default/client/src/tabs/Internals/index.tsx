import { useState, type KeyboardEvent } from 'react'
import type { SSEEvent } from '../../sse/useSSEStream'
import { AgentCardBrowserPanel } from './AgentCardBrowserPanel'
import { CollectionsViewer } from './CollectionsViewer'
import { SignalTraceFeed } from './SignalTraceFeed'
import { MemoryInspector } from './MemoryInspector'
import { ConfidencePanel } from './ConfidencePanel'

type InternalsPanelId = 'agents' | 'collections' | 'signal-trace' | 'memory' | 'confidence'

interface InternalsPanel {
  id: InternalsPanelId
  label: string
}

const PANELS: InternalsPanel[] = [
  { id: 'agents', label: 'Agent Cards' },
  { id: 'collections', label: 'Collections' },
  { id: 'signal-trace', label: 'Signal Trace' },
  { id: 'memory', label: 'Working Memory' },
  { id: 'confidence', label: 'Confidence' },
]

interface InternalsTabProps {
  accessToken: string | null
  sseEvents: SSEEvent[]
}

/**
 * Internals tab — Default Mode Network analogue.
 *
 * Secondary tablist provides access to five sub-panels:
 * - P0: Agent Cards, Collections
 * - P1: Signal Trace, Working Memory Inspector, Confidence Scores
 *
 * P1 panels render graceful placeholder per D5-B when data unavailable.
 */
export function InternalsTab({ accessToken, sseEvents }: InternalsTabProps) {
  // Default to Agent Cards panel (D5-D decision)
  const [activePanel, setActivePanel] = useState<InternalsPanelId>('agents')

  const handleKeyDown = (e: KeyboardEvent<HTMLElement>, index: number) => {
    let next = index
    if (e.key === 'ArrowRight') {
      e.preventDefault()
      next = (index + 1) % PANELS.length
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault()
      next = (index - 1 + PANELS.length) % PANELS.length
    } else {
      return
    }
    const nextPanel = PANELS[next]
    if (nextPanel) {
      setActivePanel(nextPanel.id)
      document.getElementById(`internals-tab-${nextPanel.id}`)?.focus()
    }
  }

  return (
    <section
      id="panel-internals"
      role="tabpanel"
      aria-labelledby="tab-internals"
      className="tab-panel internals-panel"
      data-active="true"
    >
      <div
        role="tablist"
        aria-label="Internals panels"
        className="internals-subnav"
      >
        {PANELS.map((panel, index) => (
          <button
            key={panel.id}
            id={`internals-tab-${panel.id}`}
            role="tab"
            aria-selected={activePanel === panel.id}
            aria-controls={`internals-panel-${panel.id}`}
            tabIndex={activePanel === panel.id ? 0 : -1}
            onClick={() => setActivePanel(panel.id)}
            onKeyDown={(e) => handleKeyDown(e, index)}
          >
            {panel.label}
          </button>
        ))}
      </div>

      <div className="internals-content">
        <div
          id="internals-panel-agents"
          role="tabpanel"
          aria-labelledby="internals-tab-agents"
          hidden={activePanel !== 'agents'}
        >
          {activePanel === 'agents' && (
            <AgentCardBrowserPanel accessToken={accessToken} />
          )}
        </div>

        <div
          id="internals-panel-collections"
          role="tabpanel"
          aria-labelledby="internals-tab-collections"
          hidden={activePanel !== 'collections'}
        >
          {activePanel === 'collections' && (
            <CollectionsViewer accessToken={accessToken} />
          )}
        </div>

        <div
          id="internals-panel-signal-trace"
          role="tabpanel"
          aria-labelledby="internals-tab-signal-trace"
          hidden={activePanel !== 'signal-trace'}
        >
          {activePanel === 'signal-trace' && (
            <SignalTraceFeed sseEvents={sseEvents} />
          )}
        </div>

        <div
          id="internals-panel-memory"
          role="tabpanel"
          aria-labelledby="internals-tab-memory"
          hidden={activePanel !== 'memory'}
        >
          {activePanel === 'memory' && (
            <MemoryInspector data={null} status="unavailable" />
          )}
        </div>

        <div
          id="internals-panel-confidence"
          role="tabpanel"
          aria-labelledby="internals-tab-confidence"
          hidden={activePanel !== 'confidence'}
        >
          {activePanel === 'confidence' && (
            <ConfidencePanel data={null} status="unavailable" />
          )}
        </div>
      </div>
    </section>
  )
}
