import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { logger } from 'hono/logger'
import { secureHeaders } from 'hono/secure-headers'
import { authMiddleware } from './auth/middleware.js'
import { createApiRouter } from './routes/api.js'
import wellknownRouter from './routes/wellknown.js'
import authRouter from './auth/index.js'
import { McpClient } from './mcp-client.js'
import { tracingMiddleware } from './middleware/tracing.js'
import { metricsMiddleware } from './middleware/metrics.js'

const allowedOrigins = () =>
  (process.env.ALLOWED_ORIGINS ?? 'http://localhost:5173').split(',').map((s) => s.trim())

export function createApp(mcpClient?: McpClient): Hono {
  const client = mcpClient ?? new McpClient(process.env.MCP_SERVER_URL ?? 'http://localhost:8080')
  const app = new Hono()

  app.use('*', tracingMiddleware)
  app.use('*', metricsMiddleware)
  app.use('*', logger())
  app.use('*', secureHeaders())

  app.use('/api/*', cors({
    origin: (origin) => {
      const allowed = allowedOrigins()
      return allowed.includes(origin) ? origin : null
    },
    credentials: true,
    allowHeaders: ['Content-Type', 'Authorization', 'Mcp-Session-Id'],
    allowMethods: ['GET', 'POST', 'DELETE', 'OPTIONS'],
  }))

  // Public routes (no auth)
  app.route('/.well-known', wellknownRouter)
  app.route('/auth', authRouter)

  // Protected API routes
  app.use('/api/input', authMiddleware)
  app.use('/api/stream', authMiddleware)
  app.use('/api/resources', authMiddleware)
  app.use('/api/agents', authMiddleware)

  app.route('/api', createApiRouter(client))

  return app
}
