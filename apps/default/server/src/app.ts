import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { logger } from 'hono/logger'
import authRouter from './auth/index.js'
import apiRouter from './routes/api.js'
import wellknownRouter from './routes/wellknown.js'

const allowedOrigins = (process.env.ALLOWED_ORIGINS ?? 'http://localhost:5173').split(',')

export function createApp(): Hono {
  const app = new Hono()

  app.use('*', logger())
  app.use(
    '*',
    cors({
      origin: (origin) => (allowedOrigins.includes(origin) ? origin : allowedOrigins[0]!),
      allowHeaders: ['Authorization', 'Content-Type', 'MCP-Protocol-Version'],
      allowMethods: ['GET', 'POST', 'DELETE', 'OPTIONS'],
      credentials: true,
    }),
  )

  app.route('/auth', authRouter)
  app.route('/.well-known', wellknownRouter)
  app.route('/api', apiRouter)

  return app
}
