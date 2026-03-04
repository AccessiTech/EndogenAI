import { useEffect, useState } from 'react'
import type { SSEStatus } from '../sse/useSSEStream'

interface StatusBarProps {
  sseStatus: SSEStatus
  reconnectCount: number
}

/**
 * Connection status bar showing live SSE state and gateway health.
 * Distinguishes "stream error" (SSE dropped) from "gateway unreachable"
 * (health poll failed).
 */
export function StatusBar({ sseStatus, reconnectCount }: StatusBarProps) {
  const [gatewayReachable, setGatewayReachable] = useState<boolean | null>(null)

  useEffect(() => {
    let cancelled = false

    async function checkHealth() {
      try {
        const res = await fetch('/api/health', { credentials: 'include' })
        if (!cancelled) setGatewayReachable(res.ok)
      } catch {
        if (!cancelled) setGatewayReachable(false)
      }
    }

    void checkHealth()
    const interval = setInterval(() => void checkHealth(), 30_000)

    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [])

  const dotStatus = sseStatus === 'connected'
    ? 'connected'
    : sseStatus === 'connecting'
    ? 'connecting'
    : 'error'

  const label = sseStatus === 'connected'
    ? 'Stream connected'
    : sseStatus === 'connecting'
    ? 'Connecting…'
    : sseStatus === 'error' && gatewayReachable === false
    ? 'Gateway unreachable'
    : sseStatus === 'error'
    ? `Stream error${reconnectCount > 0 ? ` (retry ${reconnectCount})` : ''}`
    : 'Idle'

  return (
    <div className="status-bar" aria-label="Connection status">
      <span
        className="status-dot"
        data-status={dotStatus}
        aria-hidden="true"
      />
      <span aria-live="polite" aria-atomic="true" style={{ fontSize: 'var(--font-size-sm)' }}>
        {label}
      </span>
    </div>
  )
}
