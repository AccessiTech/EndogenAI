import { Hono } from 'hono'
import { streamSSE } from 'hono/streaming'
import { readFileSync } from 'fs'
import { join } from 'path'
import { fileURLToPath } from 'url'
import { randomUUID } from 'crypto'
import { propagation, context } from '@opentelemetry/api'
import type { McpClient } from '../mcp-client.js'
import { sseConnectionsGauge } from '../middleware/metrics.js'

// Resolve registry path relative to this source file so it works regardless of cwd.
// src/routes/api.ts → ../../../../../resources/uri-registry.json = workspace root
const __dirname = fileURLToPath(new URL('.', import.meta.url))
const REGISTRY_PATH = join(__dirname, '..', '..', '..', '..', '..', 'resources', 'uri-registry.json')

// Load registry at startup (cached)
function loadRegistry() {
  // Try import.meta.url-relative path first, fall back to cwd-relative
  const candidates = [
    REGISTRY_PATH,
    join(process.cwd(), 'resources', 'uri-registry.json'),
    join(process.cwd(), '..', '..', '..', 'resources', 'uri-registry.json'),
  ]
  for (const p of candidates) {
    try {
      return JSON.parse(readFileSync(p, 'utf8'))
    } catch {
      // try next
    }
  }
  return { version: '0.0.0', generated: new Date().toISOString(), resources: [] }
}

const registry = loadRegistry()

export function createApiRouter(mcpClient: McpClient): Hono {
  const api = new Hono()

  // GET /api/health — public
  api.get('/health', (c) =>
    c.json({ status: 'ok', version: '0.1.0', timestamp: new Date().toISOString() })
  )

  // POST /api/input — protected (authMiddleware mounted in app.ts)
  api.post('/input', async (c) => {
    const body = await c.req.json<{ message?: string }>()
    const message = body?.message ?? ''
    if (!message.trim()) {
      return c.json({ error: 'message is required' }, 400)
    }
    const sessionId = randomUUID()
    // Inject W3C TraceContext into MCP message (§6.3 traceparent propagation)
    const carrier: Record<string, string> = {}
    propagation.inject(context.active(), carrier)
    const traceparent = carrier['traceparent']
    try {
      await mcpClient.send({
        jsonrpc: '2.0',
        id: sessionId,
        method: 'tools/call',
        params: {
          name: 'chat',
          arguments: {
            message,
            ...(traceparent ? { traceparent } : {}),
          },
        },
      })
    } catch {
      // MCP may not be running in dev/test — return session ID regardless
    }
    return c.json({ sessionId, streamPath: '/api/stream' }, 202)
  })

  // GET /api/stream — protected, SSE relay
  api.get('/stream', (c) => {
    sseConnectionsGauge.add(1)
    return streamSSE(c, async (stream) => {
      try {
        // Send initial heartbeat
        await stream.writeSSE({ event: 'heartbeat', data: JSON.stringify({ ts: Date.now() }) })

        // Relay from MCP (best-effort — if MCP is unavailable, keep stream open with heartbeats)
        try {
          for await (const event of mcpClient.subscribe()) {
            await stream.writeSSE({
              data: event.data,
              event: event.type ?? 'mcp-push',
              id: event.id,
            })
          }
        } catch {
          await stream.writeSSE({ event: 'error', data: JSON.stringify({ message: 'mcp-unavailable' }) })
        }
      } finally {
        sseConnectionsGauge.add(-1)
      }
    })
  })

  // GET /api/resources — protected
  api.get('/resources', (c) => {
    const group = c.req.query('group')
    const module = c.req.query('module')
    const resources = (registry.resources ?? []).filter(
      (r: { group?: string; module?: string }) =>
        (!group || r.group === group) && (!module || r.module === module)
    )
    return c.json({ resources, total: resources.length })
  })

  return api
}
