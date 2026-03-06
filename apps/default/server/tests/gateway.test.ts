import { describe, it, expect, beforeAll } from 'vitest'
import { createApp } from '../src/app.js'
import { McpClient, type McpEvent } from '../src/mcp-client.js'
import { signAccessToken } from '../src/auth/jwt.js'

// ── Mock McpClient ───────────────────────────────────────────────────────────

class MockMcpClient extends McpClient {
  constructor() {
    super('http://localhost:9999')
  }

  override async initialize(): Promise<void> {
    // no-op
  }

  override async send(): Promise<Response> {
    return new Response(JSON.stringify({ jsonrpc: '2.0', result: {}, id: 1 }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    })
  }

  override async *subscribe(): AsyncGenerator<McpEvent> {
    yield { data: JSON.stringify({ type: 'heartbeat' }), type: 'heartbeat', id: '1' }
  }

  override getSessionId(): string {
    return 'mock-session-42'
  }
}

// ── Test setup ───────────────────────────────────────────────────────────────

let mockClient: MockMcpClient
let validToken: string

beforeAll(async () => {
  process.env.JWT_SECRET = 'test-secret'
  process.env.MCP_SERVER_URI = 'http://localhost:8000'
  process.env.ALLOWED_ORIGINS = 'http://localhost:5173,http://localhost:3000'

  mockClient = new MockMcpClient()

  validToken = await signAccessToken({
    sub: 'test-user',
    scope: 'openid profile',
    aud: 'http://localhost:8000',
  })
})

// ── Helpers ──────────────────────────────────────────────────────────────────

function app() {
  return createApp(mockClient)
}

function authedRequest(path: string, init?: RequestInit) {
  return new Request(`http://localhost${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${validToken}`,
      'Content-Type': 'application/json',
      ...(init?.headers as Record<string, string> | undefined ?? {}),
    },
  })
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe('GET /api/health', () => {
  it('returns 200 { status: ok }', async () => {
    const res = await app().fetch(new Request('http://localhost/api/health'))
    expect(res.status).toBe(200)
    const body = await res.json() as { status: string }
    expect(body.status).toBe('ok')
  })

  it('includes ACAO header for allowed origin', async () => {
    const res = await app().fetch(
      new Request('http://localhost/api/health', {
        headers: { Origin: 'http://localhost:5173' },
      })
    )
    expect(res.status).toBe(200)
    expect(res.headers.get('Access-Control-Allow-Origin')).toBe('http://localhost:5173')
  })

  it('does NOT include ACAO header for disallowed origin', async () => {
    const res = await app().fetch(
      new Request('http://localhost/api/health', {
        headers: { Origin: 'http://evil.example.com' },
      })
    )
    expect(res.headers.get('Access-Control-Allow-Origin')).toBeNull()
  })
})

describe('POST /api/input', () => {
  it('returns 401 without Authorization header', async () => {
    const res = await app().fetch(
      new Request('http://localhost/api/input', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: 'hello' }),
      })
    )
    expect(res.status).toBe(401)
    expect(res.headers.get('WWW-Authenticate')).toBeTruthy()
  })

  it('returns 202 with sessionId and streamPath for valid request', async () => {
    const res = await app().fetch(
      authedRequest('/api/input', {
        method: 'POST',
        body: JSON.stringify({ message: 'hello' }),
      })
    )
    expect(res.status).toBe(202)
    const body = await res.json() as { sessionId: string; streamPath: string }
    expect(body.sessionId).toBeTruthy()
    expect(body.streamPath).toBe('/api/stream')
  })

  it('returns 400 for empty message', async () => {
    const res = await app().fetch(
      authedRequest('/api/input', {
        method: 'POST',
        body: JSON.stringify({ message: '' }),
      })
    )
    expect(res.status).toBe(400)
    const body = await res.json() as { error: string }
    expect(body.error).toBe('message is required')
  })
})

describe('GET /api/stream', () => {
  it('returns 401 without Authorization header', async () => {
    const res = await app().fetch(new Request('http://localhost/api/stream'))
    expect(res.status).toBe(401)
  })

  it('returns text/event-stream content-type with valid auth', async () => {
    const res = await app().fetch(authedRequest('/api/stream'))
    expect(res.headers.get('Content-Type')).toMatch(/text\/event-stream/)
    await res.body?.cancel()
  })
})

describe('GET /api/resources', () => {
  it('returns 401 without Authorization header', async () => {
    const res = await app().fetch(new Request('http://localhost/api/resources'))
    expect(res.status).toBe(401)
  })

  it('returns 200 with resources array', async () => {
    const res = await app().fetch(authedRequest('/api/resources'))
    expect(res.status).toBe(200)
    const body = await res.json() as { resources: unknown[]; total: number }
    expect(Array.isArray(body.resources)).toBe(true)
    expect(typeof body.total).toBe('number')
  })

  it('filters by group query param', async () => {
    const res = await app().fetch(
      authedRequest('/api/resources?group=group-ii-cognitive-processing')
    )
    expect(res.status).toBe(200)
    const body = await res.json() as { resources: Array<{ group: string }> }
    expect(body.resources.every((r) => r.group === 'group-ii-cognitive-processing')).toBe(true)
    expect(body.resources.length).toBeGreaterThan(0)
  })
})

describe('GET /api/agents', () => {
  it('returns 401 without Authorization header', async () => {
    const res = await app().fetch(new Request('http://localhost/api/agents'))
    expect(res.status).toBe(401)
    expect(res.headers.get('WWW-Authenticate')).toBeTruthy()
  })

  it('returns 200 with { agents, timestamp } when authed and MODULE_URLS is empty', async () => {
    delete process.env.MODULE_URLS
    const res = await app().fetch(authedRequest('/api/agents'))
    expect(res.status).toBe(200)
    const body = await res.json() as { agents: unknown[]; timestamp: string }
    expect(Array.isArray(body.agents)).toBe(true)
    expect(typeof body.timestamp).toBe('string')
    expect(body.agents).toHaveLength(0)
  })

  it('gracefully omits unreachable MODULE_URLS entries', async () => {
    process.env.MODULE_URLS = 'http://127.0.0.1:19999'
    const res = await app().fetch(authedRequest('/api/agents'))
    expect(res.status).toBe(200)
    const body = await res.json() as { agents: unknown[]; timestamp: string }
    expect(Array.isArray(body.agents)).toBe(true)
    delete process.env.MODULE_URLS
  })
})

describe('GET /.well-known/oauth-authorization-server', () => {
  it('returns 200 with issuer field', async () => {
    const res = await app().fetch(
      new Request('http://localhost/.well-known/oauth-authorization-server')
    )
    expect(res.status).toBe(200)
    const body = await res.json() as { issuer: string }
    expect(body.issuer).toBeTruthy()
  })
})
