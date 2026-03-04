import { useEffect, useState } from 'react'
import type { ResourceEntry } from '../../api/gateway'
import { gateway } from '../../api/gateway'
import { Placeholder } from './Placeholder'

interface CollectionsViewerProps {
  accessToken: string | null
}

/**
 * P0 panel — displays vector store collections from the resource registry.
 * Fetches GET /api/resources and groups entries by their `group` field.
 */
export function CollectionsViewer({ accessToken }: CollectionsViewerProps) {
  const [resources, setResources] = useState<ResourceEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await gateway.listResources(accessToken)
        if (!cancelled) setResources(data)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load resources')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void load()
    return () => { cancelled = true }
  }, [accessToken])

  if (loading) {
    return (
      <div role="status" aria-live="polite">
        <p className="placeholder-panel">Loading collections…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div role="alert" className="error-alert" aria-live="assertive">
        {error}
      </div>
    )
  }

  if (resources.length === 0) {
    return (
      <Placeholder
        message="No resource collections found. Register modules with vector store collections."
        title="No collections"
      />
    )
  }

  // Group by group field
  const grouped = resources.reduce<Record<string, ResourceEntry[]>>((acc, r) => {
    const group = r.group ?? 'ungrouped'
    if (!acc[group]) acc[group] = []
    acc[group].push(r)
    return acc
  }, {})

  return (
    <section aria-label="Resource collections">
      {Object.entries(grouped).map(([group, items]) => (
        <div key={group} style={{ marginBottom: 'var(--space-6)' }}>
          <h3
            style={{
              fontSize: 'var(--font-size-base)',
              fontWeight: 600,
              marginBottom: 'var(--space-3)',
              color: 'var(--color-text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            {group}
          </h3>
          <div className="collections-list">
            {items.map((r) => (
              <div key={r.uri} className="collection-item">
                <div className="collection-item-name">{r.uri}</div>
                {r.name && (
                  <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text)', marginTop: 'var(--space-1)' }}>
                    {r.name}
                  </div>
                )}
                {r.description && (
                  <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginTop: 'var(--space-1)' }}>
                    {r.description}
                  </div>
                )}
                <div className="collection-item-meta">
                  {r.backend && <span className="badge">{r.backend}</span>}
                  {r.mimeType && <span className="badge">{r.mimeType}</span>}
                  {r.recordCount !== undefined && (
                    <span className="badge">{r.recordCount.toLocaleString()} records</span>
                  )}
                  {r.accessControl && <span className="badge">{r.accessControl}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </section>
  )
}
