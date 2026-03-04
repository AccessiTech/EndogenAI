import { createMiddleware } from 'hono/factory'
import { verifyAccessToken } from './jwt.js'
import type { JWTPayload } from 'jose'

// Extend Hono context variables type
declare module 'hono' {
  interface ContextVariableMap {
    jwtPayload: JWTPayload
  }
}

export const authMiddleware = createMiddleware(async (c, next) => {
  const authHeader = c.req.header('Authorization')
  const token = authHeader?.startsWith('Bearer ') ? authHeader.slice(7) : undefined

  if (!token) {
    const mcpServerUri = process.env.MCP_SERVER_URI ?? 'http://localhost:8000'
    const mcpServerUrl = process.env.MCP_SERVER_URL ?? 'http://localhost:8000'
    return c.json({ error: 'unauthorized' }, 401, {
      'WWW-Authenticate':
        `Bearer realm="${mcpServerUri}", ` +
        `resource_metadata="${new URL('/.well-known/oauth-protected-resource', mcpServerUrl).href}"`,
    })
  }

  try {
    const payload = await verifyAccessToken(token)
    c.set('jwtPayload', payload)
    await next()
  } catch {
    return c.json({ error: 'invalid_token' }, 401, {
      'WWW-Authenticate': `Bearer error="invalid_token"`,
    })
  }
})
