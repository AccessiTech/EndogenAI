/**
 * telemetry.ts — OTel NodeSDK setup for Hono gateway.
 *
 * Must be called at startup in index.ts before any other application code.
 * This ensures auto-instrumentations are registered before modules load.
 *
 * Biological analogue: insular cortex setup — all afferent signals route to
 * the interoceptive integration centre before reaching the executive surface.
 *
 * @see docs/research/phase-8c-detailed-workplan.md §4.1
 */
import { NodeSDK } from '@opentelemetry/sdk-node'
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http'
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-http'
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node'
import { W3CTraceContextPropagator } from '@opentelemetry/core'
import { resourceFromAttributes } from '@opentelemetry/resources'
import { PeriodicExportingMetricReader } from '@opentelemetry/sdk-metrics'

let sdk: NodeSDK | undefined

export function initTelemetry(): void {
  if (process.env.OTEL_SDK_DISABLED === 'true') return

  const endpoint = process.env.OTEL_EXPORTER_OTLP_ENDPOINT ?? 'http://localhost:4318'

  try {
    sdk = new NodeSDK({
      resource: resourceFromAttributes({
        'service.name': process.env.OTEL_SERVICE_NAME ?? 'hono-gateway',
        'service.version': '0.1.0',
        'service.namespace': 'brain',
      }),
      traceExporter: new OTLPTraceExporter({
        url: `${endpoint}/v1/traces`,
      }),
      metricReader: new PeriodicExportingMetricReader({
        exporter: new OTLPMetricExporter({
          url: `${endpoint}/v1/metrics`,
        }),
        exportIntervalMillis: 15_000,
      }),
      instrumentations: [
        getNodeAutoInstrumentations({
          // Disable noisy fs instrumentation to reduce span volume
          '@opentelemetry/instrumentation-fs': { enabled: false },
        }),
      ],
      textMapPropagator: new W3CTraceContextPropagator(),
    })

    sdk.start()
  } catch (err) {
    // OTel initialisation must never crash the gateway
    console.warn('[telemetry] OTel SDK start failed (non-fatal):', (err as Error).message)
    sdk = undefined
  }
}

export async function shutdownTelemetry(): Promise<void> {
  try {
    // Cap shutdown at 3 s to avoid hanging when the OTel collector is unreachable
    await Promise.race([
      sdk?.shutdown() ?? Promise.resolve(),
      new Promise<void>((resolve) => setTimeout(resolve, 3_000)),
    ])
  } catch {
    // Swallow shutdown errors — process is exiting
  }
}
