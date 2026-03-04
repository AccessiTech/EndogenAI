/**
 * logger.ts — Pino logger with OTel trace context injection.
 *
 * Every log record emits trace_id and span_id so that logs can be correlated
 * with distributed traces in Grafana / Loki.
 *
 * Biological analogue: cortical output reporting — every log carries the
 * trace vector that produced it.
 *
 * @see docs/research/phase-8c-detailed-workplan.md §5
 */
import pino from 'pino'
import { trace } from '@opentelemetry/api'

export const logger = pino({
  level: process.env.LOG_LEVEL ?? 'info',
  formatters: {
    log: (obj) => {
      const span = trace.getActiveSpan()
      if (span?.isRecording()) {
        const ctx = span.spanContext()
        return {
          ...obj,
          trace_id: ctx.traceId,
          span_id: ctx.spanId,
          trace_flags: ctx.traceFlags,
        }
      }
      return obj
    },
  },
})
