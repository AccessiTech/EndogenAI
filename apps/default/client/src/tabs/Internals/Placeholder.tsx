interface PlaceholderProps {
  message: string
  title?: string
}

/**
 * Placeholder panel for P1 panels that are not yet connected to live data.
 * Per D5-B decision: renders "not yet available" state gracefully.
 */
export function Placeholder({ message, title }: PlaceholderProps) {
  return (
    <div className="placeholder-panel" aria-label={title ?? 'Panel not yet available'}>
      <svg
        aria-hidden="true"
        width="48"
        height="48"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
      <p>{message}</p>
    </div>
  )
}
