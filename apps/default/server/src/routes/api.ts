import { Hono } from 'hono'
import { authMiddleware } from '../auth/middleware.js'

const api = new Hono()

// Public health check — no auth required
api.get('/health', (c) => c.json({ status: 'ok', timestamp: new Date().toISOString() }))

// Protected routes — all /api/* except /health require a valid Bearer JWT
api.use('/input', authMiddleware)
api.post('/input', (c) => {
  // stub — full relay implemented in §8.1
  return c.json({ status: 'accepted' }, 202)
})

export default api
