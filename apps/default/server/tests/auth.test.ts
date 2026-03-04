import { describe, it, expect, beforeAll, afterEach } from 'vitest'
import { SignJWT } from 'jose'
import { createApp } from '../src/app.js'
import { generateCodeVerifier, generateCodeChallenge } from '../src/auth/pkce.js'
import { clearAllCodes } from '../src/auth/sessions.js'

// Set env vars before any module-level JWT reads
beforeAll(() => {
  process.env.JWT_SECRET = 'test-secret-for-vitest-gate1'
  process.env.MCP_SERVER_URI = 'http://localhost:8000'
  process.env.MCP_SERVER_URL = 'http://localhost:8000'
  process.env.ISSUER_URL = 'http://localhost:3001'
})

afterEach(() => {
  clearAllCodes()
})

const CLIENT_ID = 'apps-default-browser'
const REDIRECT_URI = 'http://localhost:5173/callback'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeApp() {
  return createApp()
}

async function doAuthorize(
  app: ReturnType<typeof makeApp>,
  verifier: string,
  state = 'teststate',
): Promise<string> {
  const challenge = generateCodeChallenge(verifier)
  const url = new URL('http://localhost:3001/auth/authorize')
  url.searchParams.set('client_id', CLIENT_ID)
  url.searchParams.set('response_type', 'code')
  url.searchParams.set('redirect_uri', REDIRECT_URI)
  url.searchParams.set('code_challenge', challenge)
  url.searchParams.set('code_challenge_method', 'S256')
  url.searchParams.set('state', state)

  const res = await app.request(url.toString())
  expect(res.status).toBe(302)

  const location = res.headers.get('Location')!
  const redirected = new URL(location)
  const code = redirected.searchParams.get('code')!
  expect(code).toBeTruthy()
  return code
}

async function doTokenExchange(
  app: ReturnType<typeof makeApp>,
  code: string,
  verifier: string,
): Promise<{ status: number; body: Record<string, unknown>; setCookie: string | null }> {
  const res = await app.request('http://localhost:3001/auth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      grant_type: 'authorization_code',
      code,
      code_verifier: verifier,
      redirect_uri: REDIRECT_URI,
      client_id: CLIENT_ID,
    }),
  })
  const body = (await res.json()) as Record<string, unknown>
  const setCookie = res.headers.get('Set-Cookie')
  return { status: res.status, body, setCookie }
}

/** Sign a token whose exp is `secondsFromNow` seconds in the future (negative = past). */
async function signTokenWithCustomExp(sub: string, secondsFromNow: number): Promise<string> {
  const secret = new TextEncoder().encode(process.env.JWT_SECRET ?? 'test-secret-for-vitest-gate1')
  const now = Math.floor(Date.now() / 1000)
  return new SignJWT({ sub, scope: 'mcp', aud: process.env.MCP_SERVER_URI ?? 'http://localhost:8000' })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt(now - 60)
    .setExpirationTime(now + secondsFromNow)
    .sign(secret)
}

// ---------------------------------------------------------------------------
// 1. PKCE round-trip
// ---------------------------------------------------------------------------

describe('PKCE round-trip', () => {
  it('authorize → exchange → returns access token with correct aud', async () => {
    const app = makeApp()
    const verifier = generateCodeVerifier()
    const code = await doAuthorize(app, verifier)

    const { status, body } = await doTokenExchange(app, code, verifier)
    expect(status).toBe(200)
    expect(body.access_token).toBeTruthy()
    expect(body.token_type).toBe('Bearer')

    // Verify access token aud
    const { verifyAccessToken } = await import('../src/auth/jwt.js')
    const payload = await verifyAccessToken(body.access_token as string)
    expect(payload.aud).toBe('http://localhost:8000')
  })

  it('bad code_verifier returns 400', async () => {
    const app = makeApp()
    const verifier = generateCodeVerifier()
    const code = await doAuthorize(app, verifier)

    const { status } = await doTokenExchange(app, code, 'wrong-verifier')
    expect(status).toBe(400)
  })
})

// ---------------------------------------------------------------------------
// 2. Auth code single-use
// ---------------------------------------------------------------------------

describe('Auth code single-use', () => {
  it('exchanging same code twice returns 400 on second attempt', async () => {
    const app = makeApp()
    const verifier = generateCodeVerifier()
    const code = await doAuthorize(app, verifier)

    const first = await doTokenExchange(app, code, verifier)
    expect(first.status).toBe(200)

    const second = await doTokenExchange(app, code, verifier)
    expect(second.status).toBe(400)
  })
})

// ---------------------------------------------------------------------------
// 3. Expired auth code
// ---------------------------------------------------------------------------

describe('Expired auth code', () => {
  it('expired code returns 400', async () => {
    const app = makeApp()
    const { storeAuthCode } = await import('../src/auth/sessions.js')

    storeAuthCode('expired-code', {
      clientId: CLIENT_ID,
      redirectUri: REDIRECT_URI,
      codeChallenge: generateCodeChallenge('someverifier'),
      codeChallengeMethod: 'S256',
      sub: 'user1',
      expiresAt: Date.now() - 1, // already expired
    })

    const res = await app.request('http://localhost:3001/auth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        grant_type: 'authorization_code',
        code: 'expired-code',
        code_verifier: 'someverifier',
        redirect_uri: REDIRECT_URI,
        client_id: CLIENT_ID,
      }),
    })
    expect(res.status).toBe(400)
  })
})

// ---------------------------------------------------------------------------
// 4. Refresh token rotation
// ---------------------------------------------------------------------------

describe('Refresh token rotation', () => {
  it('valid refresh cookie returns new access token and rotated cookie', async () => {
    const app = makeApp()
    const verifier = generateCodeVerifier()
    const code = await doAuthorize(app, verifier)
    const { status, setCookie } = await doTokenExchange(app, code, verifier)
    expect(status).toBe(200)
    expect(setCookie).toBeTruthy()

    // Extract the refresh_token cookie value
    const cookieValue = setCookie!.split(';')[0] // "refresh_token=<value>"

    const refreshRes = await app.request('http://localhost:3001/auth/refresh', {
      method: 'POST',
      headers: { Cookie: cookieValue },
    })
    expect(refreshRes.status).toBe(200)
    const refreshBody = (await refreshRes.json()) as Record<string, unknown>
    expect(refreshBody.access_token).toBeTruthy()

    const newCookie = refreshRes.headers.get('Set-Cookie')
    expect(newCookie).toBeTruthy()
    // New cookie value should differ from old one (rotation)
    expect(newCookie).not.toBe(setCookie)
  })

  it('second refresh with same (rotated-away) cookie returns 401', async () => {
    const app = makeApp()
    const verifier = generateCodeVerifier()
    const code = await doAuthorize(app, verifier)
    const { status, setCookie } = await doTokenExchange(app, code, verifier)
    expect(status).toBe(200)

    const cookieValue = setCookie!.split(';')[0]

    // First refresh — succeeds and rotates token
    const first = await app.request('http://localhost:3001/auth/refresh', {
      method: 'POST',
      headers: { Cookie: cookieValue },
    })
    expect(first.status).toBe(200)

    // Second refresh with SAME old cookie — must fail (replay protection)
    const second = await app.request('http://localhost:3001/auth/refresh', {
      method: 'POST',
      headers: { Cookie: cookieValue },
    })
    expect(second.status).toBe(401)
  })
})

// ---------------------------------------------------------------------------
// 5. Clock skew tolerance
// ---------------------------------------------------------------------------

describe('Clock skew tolerance', () => {
  it('token expired 20s ago is accepted (within 30s tolerance)', async () => {
    const app = makeApp()
    const token = await signTokenWithCustomExp('user1', -20)

    const res = await app.request('http://localhost:3001/api/input', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: 'test' }),
    })
    // Should be accepted (202 stub response)
    expect(res.status).toBe(202)
  })

  it('token expired 60s ago is rejected (outside 30s tolerance)', async () => {
    const app = makeApp()
    const token = await signTokenWithCustomExp('user1', -60)

    const res = await app.request('http://localhost:3001/api/input', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: 'test' }),
    })
    expect(res.status).toBe(401)
  })
})

// ---------------------------------------------------------------------------
// 6. Audience mismatch
// ---------------------------------------------------------------------------

describe('Audience mismatch', () => {
  it('token with wrong aud returns 401', async () => {
    const app = makeApp()
    const secret = new TextEncoder().encode(process.env.JWT_SECRET ?? 'test-secret-for-vitest-gate1')
    const now = Math.floor(Date.now() / 1000)
    const badAudToken = await new SignJWT({ sub: 'user1', scope: 'mcp', aud: 'http://wrong-audience.example.com' })
      .setProtectedHeader({ alg: 'HS256' })
      .setIssuedAt(now)
      .setExpirationTime(now + 900)
      .sign(secret)

    const res = await app.request('http://localhost:3001/api/input', {
      method: 'POST',
      headers: { Authorization: `Bearer ${badAudToken}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: 'test' }),
    })
    expect(res.status).toBe(401)
  })
})

// ---------------------------------------------------------------------------
// 7. Missing token on protected route
// ---------------------------------------------------------------------------

describe('Missing token', () => {
  it('POST /api/input without token returns 401 with WWW-Authenticate header', async () => {
    const app = makeApp()
    const res = await app.request('http://localhost:3001/api/input', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: 'test' }),
    })
    expect(res.status).toBe(401)
    const wwwAuth = res.headers.get('WWW-Authenticate')
    expect(wwwAuth).toBeTruthy()
    expect(wwwAuth).toContain('Bearer realm=')
    expect(wwwAuth).toContain('resource_metadata=')
  })

  it('GET /api/health returns 200 without auth (public endpoint)', async () => {
    const app = makeApp()
    const res = await app.request('http://localhost:3001/api/health')
    expect(res.status).toBe(200)
  })
})

// ---------------------------------------------------------------------------
// 8. DELETE /auth/session
// ---------------------------------------------------------------------------

describe('Session deletion', () => {
  it('DELETE /auth/session returns 204 and clears cookie', async () => {
    const app = makeApp()
    const verifier = generateCodeVerifier()
    const code = await doAuthorize(app, verifier)
    const { status, setCookie } = await doTokenExchange(app, code, verifier)
    expect(status).toBe(200)

    const cookieValue = setCookie!.split(';')[0]

    const deleteRes = await app.request('http://localhost:3001/auth/session', {
      method: 'DELETE',
      headers: { Cookie: cookieValue },
    })
    expect(deleteRes.status).toBe(204)
  })

  it('after session deletion, refresh with old cookie returns 401', async () => {
    const app = makeApp()
    const verifier = generateCodeVerifier()
    const code = await doAuthorize(app, verifier)
    const { status, setCookie } = await doTokenExchange(app, code, verifier)
    expect(status).toBe(200)

    const cookieValue = setCookie!.split(';')[0]

    // Delete session (server revokes token)
    await app.request('http://localhost:3001/auth/session', {
      method: 'DELETE',
      headers: { Cookie: cookieValue },
    })

    // Try to refresh with the old cookie — should fail
    const refreshRes = await app.request('http://localhost:3001/auth/refresh', {
      method: 'POST',
      headers: { Cookie: cookieValue },
    })
    expect(refreshRes.status).toBe(401)
  })
})

// ---------------------------------------------------------------------------
// 9. /.well-known/oauth-authorization-server
// ---------------------------------------------------------------------------

describe('OAuth Authorization Server Metadata', () => {
  it('returns issuer and required RFC 8414 fields', async () => {
    const app = makeApp()
    const res = await app.request('http://localhost:3001/.well-known/oauth-authorization-server')
    expect(res.status).toBe(200)
    const body = (await res.json()) as Record<string, unknown>
    expect(body.issuer).toBeTruthy()
    expect(body.authorization_endpoint).toBeTruthy()
    expect(body.token_endpoint).toBeTruthy()
    expect(body.code_challenge_methods_supported).toContain('S256')
  })
})
