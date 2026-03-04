/**
 * tracing.ts — Hono per-request tracing middleware.
 *
 * Extracts W3C TraceContext from incoming request headers, creates a SERVER
 * span, and ensures it is active for the full request lifecycle so that all
 * downstream OTel API calls and pino log records inherit the trace context.
 *
 * Note: Hono is not auto-instrumented by @opentelemetry/auto-instrumentations-node
 * (which covers Express, Fastify, etc.) — manual middleware is required.
 *
 * Biological analogue: thalamic relay — every incoming signal is catalogued
 * before being forwarded to the cortex.
 *
 * @see docs/research/phase-8c-detailed-workplan.md §4.2
 */
import { createMiddleware } from 'hono/factory'
import { trace, context, propagation, SpanStatusCode, SpanKind } from '@opentelemetry/api'

const tracer = trace.getTracer('hono-gateway', '0.1.0')

export const tracingMiddleware = createMiddleware(async (c, next) => {
  // Extract W3C TraceContext from incoming request headers (e.g. from browser)
  const carrier: Record<string, string> = {}
  c.req.raw.headers.forEach((val, key) => {
    carrier[key] = val
  })
  const parentCtx = propagation.extract(context.active(), carrier)

  // Create a SERVER span for this request
  const spanName = `${c.req.method} ${c.req.path}`
  const span = tracer.startSpan(spanName, { kind: SpanKind.SERVER }, parentCtx)
  const activeCtx = trace.setSpan(parentCtx, span)

  await context.with(activeCtx, async () => {
    try {
      await next()
      const status = c.res.status
      span.setStatus({ code: status < 400 ? SpanStatusCode.OK : SpanStatusCode.ERROR })
    } catch (err) {
      span.recordException(err as Error)
      span.setStatus({ code: SpanStatusCode.ERROR, message: (err as Error).message })
      throw err
    } finally {
      span.setAttribute('http.status_code', c.res.status)
      span.setAttribute('http.method', c.req.method)
      span.setAttribute('http.target', c.req.path)
      span.end()
    }
  })
})
