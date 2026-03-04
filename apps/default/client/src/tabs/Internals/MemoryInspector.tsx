import { Placeholder } from './Placeholder'

interface MemoryContext {
  content?: string
  tokenCount?: number
  tokenBudget?: number
  [key: string]: unknown
}

interface MemoryInspectorProps {
  data: MemoryContext | null
  status: 'available' | 'unavailable' | 'loading'
}

/**
 * P1 panel — working memory context inspector.
 * Per D5-B: renders placeholder when brain://group-ii/working-memory/context/current is unavailable.
 * WCAG: <section> with aria-label; <pre><code> for structured display.
 */
export function MemoryInspector({ data, status }: MemoryInspectorProps) {
  if (status === 'unavailable' || data === null) {
    return (
      <Placeholder
        message="Working memory inspector not yet available. Activate §5.2 working memory in modules/group-ii-cognitive-processing."
        title="Working memory — not yet available"
      />
    )
  }

  if (status === 'loading') {
    return (
      <div role="status" aria-live="polite">
        <p className="placeholder-panel">Loading memory context…</p>
      </div>
    )
  }

  const { tokenCount, tokenBudget, ...rest } = data

  return (
    <section aria-label="Working memory context">
      {tokenCount !== undefined && tokenBudget !== undefined && (
        <div style={{ marginBottom: 'var(--space-4)' }} aria-label="Token budget">
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-1)' }}>
            <span>Token usage</span>
            <span>
              {tokenCount.toLocaleString()} / {tokenBudget.toLocaleString()}
            </span>
          </div>
          <meter
            min={0}
            max={tokenBudget}
            value={tokenCount}
            style={{ width: '100%' }}
            aria-label={`Token usage: ${tokenCount} of ${tokenBudget}`}
          />
        </div>
      )}
      <pre
        style={{
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius)',
          padding: 'var(--space-3)',
          overflow: 'auto',
          fontSize: 'var(--font-size-sm)',
        }}
      >
        <code>{JSON.stringify(rest, null, 2)}</code>
      </pre>
    </section>
  )
}
