import { Placeholder } from './Placeholder'

interface ConfidenceData {
  per_goal_class: Record<string, number>
}

interface ConfidencePanelProps {
  data: ConfidenceData | null
  status: 'available' | 'unavailable' | 'loading'
}

/**
 * P1 panel — metacognition confidence scores.
 * Per D5-B: renders placeholder when brain://group-iv/metacognition/confidence/current unavailable.
 *
 * WCAG:
 * - <table> with <th> headers (1.3.1)
 * - <meter> with aria-label on each row (accessible progress)
 */
export function ConfidencePanel({ data, status }: ConfidencePanelProps) {
  if (status === 'unavailable' || data === null) {
    return (
      <Placeholder
        message="Confidence scores not yet available. Activate §7.x metacognition in modules/group-iv-adaptive-systems."
        title="Confidence scores — not yet available"
      />
    )
  }

  if (status === 'loading') {
    return (
      <div role="status" aria-live="polite">
        <p className="placeholder-panel">Loading confidence scores…</p>
      </div>
    )
  }

  return (
    <section aria-label="Metacognition confidence scores">
      <table aria-label="Confidence scores by goal class">
        <thead>
          <tr>
            <th scope="col">Goal Class</th>
            <th scope="col">Confidence</th>
            <th scope="col">Score</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(data.per_goal_class).map(([cls, score]) => (
            <tr key={cls}>
              <td>{cls}</td>
              <td>
                <meter
                  min={0}
                  max={1}
                  value={score}
                  aria-label={`${cls} confidence: ${(score * 100).toFixed(0)}%`}
                />
              </td>
              <td>{(score * 100).toFixed(0)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
