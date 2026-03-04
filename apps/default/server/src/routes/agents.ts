/**
 * agents.ts — GET /api/agents
 *
 * Fans out to each module's /.well-known/agent-card.json endpoint and returns
 * the collected cards as a unified list.  Uses Promise.allSettled so a single
 * unreachable module never fails the whole request.
 *
 * Configuration:
 *   MODULE_URLS — comma-separated base URLs, e.g.
 *                 http://localhost:8001,http://localhost:8002
 *                 Each URL is appended with /.well-known/agent-card.json.
 *
 * Response shape: { agents: AgentCard[], timestamp: ISO8601 }
 */
import { Hono } from 'hono'

export const agentsRouter = new Hono()

agentsRouter.get('/agents', async (c) => {
  // Read MODULE_URLS dynamically so runtime env changes are respected (and tests can stub it).
  const moduleUrls = (process.env.MODULE_URLS ?? '').split(',').filter(Boolean)

  const results = await Promise.allSettled(
    moduleUrls.map((url) =>
      fetch(`${url}/.well-known/agent-card.json`, {
        signal: AbortSignal.timeout(2000),
      }).then((r) => r.json()),
    ),
  )

  const agents = results
    .filter((r) => r.status === 'fulfilled')
    .map((r) => (r as PromiseFulfilledResult<unknown>).value)

  return c.json({ agents, timestamp: new Date().toISOString() })
})
