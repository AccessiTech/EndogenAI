/**
 * telemetry.test.ts — Unit tests for OTel telemetry and metrics initialisation.
 *
 * @see docs/research/phase-8c-detailed-workplan.md §11 — Gate C1/C4 verification
 */
import { describe, it, expect, vi, afterEach } from 'vitest'

describe('initTelemetry', () => {
  afterEach(() => {
    // Reset env vars after each test
    delete process.env.OTEL_SDK_DISABLED
    delete process.env.OTEL_EXPORTER_OTLP_ENDPOINT
    delete process.env.OTEL_SERVICE_NAME
    vi.resetModules()
  })

  it('does not throw when OTEL_SDK_DISABLED=true', async () => {
    process.env.OTEL_SDK_DISABLED = 'true'
    const { initTelemetry } = await import('../src/telemetry.js')
    expect(() => initTelemetry()).not.toThrow()
  })

  it('does not throw without a running OTel collector (SDK is fault-tolerant)', async () => {
    // Point at a non-existent endpoint; SDK should start without throwing
    process.env.OTEL_EXPORTER_OTLP_ENDPOINT = 'http://localhost:19999'
    const { initTelemetry, shutdownTelemetry } = await import('../src/telemetry.js')
    expect(() => initTelemetry()).not.toThrow()
    // Shutdown should also be safe even when start used an unreachable endpoint
    // (uses a 3 s internal cap so this resolves promptly)
    await expect(shutdownTelemetry()).resolves.toBeUndefined()
  }, 10_000)

  it('does not throw with default config (no collector required to start)', async () => {
    const { initTelemetry, shutdownTelemetry } = await import('../src/telemetry.js')
    expect(() => initTelemetry()).not.toThrow()
    await expect(shutdownTelemetry()).resolves.toBeUndefined()
  }, 10_000)

  it('shutdownTelemetry resolves without crash when called twice', async () => {
    process.env.OTEL_SDK_DISABLED = 'true'
    const { initTelemetry, shutdownTelemetry } = await import('../src/telemetry.js')
    initTelemetry()
    await expect(shutdownTelemetry()).resolves.toBeUndefined()
    // Second shutdown should also be safe
    await expect(shutdownTelemetry()).resolves.toBeUndefined()
  })
})

describe('metricsMiddleware', () => {
  it('increments requestCounter on each request', async () => {
    const { requestCounter } = await import('../src/middleware/metrics.js')
    const addSpy = vi.spyOn(requestCounter, 'add')

    const { createApp } = await import('../src/app.js')
    const { McpClient } = await import('../src/mcp-client.js')

    class NoOpMcpClient extends McpClient {
      constructor() { super('http://localhost:9999') }
      override async initialize() { /* no-op */ }
      override async send() {
        return new Response(JSON.stringify({ jsonrpc: '2.0', result: {}, id: 1 }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }
    }

    const app = createApp(new NoOpMcpClient())
    await app.request('/api/health')

    expect(addSpy).toHaveBeenCalledWith(
      1,
      expect.objectContaining({ method: 'GET', route: '/api/health' })
    )

    addSpy.mockRestore()
  })
})
