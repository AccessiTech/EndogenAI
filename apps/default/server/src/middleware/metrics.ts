/**
 * metrics.ts — OTel-based Prometheus metrics for the Hono gateway.
 *
 * Flow: gateway → OTLP HTTP → OTel Collector → Prometheus scrape
 *
 * The OTel Collector applies `namespace: brain` when exporting to its
 * Prometheus endpoint (:8889), so effective Prometheus metric names are:
 *   brain_hono_gateway_requests_total
 *   brain_hono_gateway_auth_failures_total
 *   brain_hono_gateway_sse_active_connections
 *   brain_hono_gateway_input_latency_ms_{bucket,count,sum}
 *
 * Biological analogue: insular posterior cortex — raw visceral metrics
 * accumulated before anterior integration produces actionable readouts.
 *
 * @see docs/research/phase-8c-detailed-workplan.md §4.3
 */
import { createMiddleware } from 'hono/factory'
import { metrics } from '@opentelemetry/api'

const meter = metrics.getMeter('hono-gateway', '0.1.0')

export const requestCounter = meter.createCounter('hono_gateway_requests_total', {
  description: 'Total HTTP requests handled by Hono gateway',
})

export const authFailureCounter = meter.createCounter('hono_gateway_auth_failures_total', {
  description: 'Total auth failures (401 responses)',
})

export const sseConnectionsGauge = meter.createUpDownCounter(
  'hono_gateway_sse_active_connections',
  {
    description: 'Currently active SSE connections',
  }
)

export const inputLatencyHistogram = meter.createHistogram('hono_gateway_input_latency_ms', {
  description: 'Latency histogram for POST /api/input → 202 response (ms)',
  unit: 'ms',
})

/**
 * Hono middleware that records per-request metrics.
 * Mount globally in app.ts: app.use('*', metricsMiddleware)
 */
export const metricsMiddleware = createMiddleware(async (c, next) => {
  const start = Date.now()
  await next()
  const durationMs = Date.now() - start
  const route = c.req.path
  const method = c.req.method
  const statusCode = String(c.res.status)

  requestCounter.add(1, { method, route, status_code: statusCode })

  if (route === '/api/input' && method === 'POST') {
    inputLatencyHistogram.record(durationMs, { route, method })
  }

  if (c.res.status === 401) {
    authFailureCounter.add(1, { reason: 'unauthorized' })
  }
})
