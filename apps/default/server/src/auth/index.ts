import { Hono } from 'hono'
import { getCookie, setCookie, deleteCookie } from 'hono/cookie'
import { randomBytes } from 'crypto'
import { signAccessToken, signRefreshToken, verifyRefreshToken } from './jwt.js'
import { verifyCodeChallenge } from './pkce.js'
import {
  storeAuthCode,
  consumeAuthCode,
  registerRefreshToken,
  rotateRefreshToken,
  revokeRefreshToken,
} from './sessions.js'

const ALLOWED_CLIENT_ID = 'apps-default-browser'
const AUTH_CODE_TTL_MS = 60_000 // 1 minute
const REFRESH_COOKIE = 'refresh_token'

// Allowlist of permitted redirect URIs. Set REDIRECT_URI_ALLOWLIST env var
// (comma-separated) to override. Defaults permit the local Vite dev server and
// its standard OAuth callback path.
const ALLOWED_REDIRECT_URIS = (
  process.env.REDIRECT_URI_ALLOWLIST ?? 'http://localhost:5173,http://localhost:5173/callback'
)
  .split(',')
  .map((u) => u.trim())

const auth = new Hono()

// GET /authorize — PKCE authorization endpoint
auth.get('/authorize', (c) => {
  const { client_id, redirect_uri, code_challenge, code_challenge_method, state, response_type } =
    c.req.query()

  if (client_id !== ALLOWED_CLIENT_ID) {
    return c.json({ error: 'unauthorized_client', error_description: 'Unknown client_id' }, 400)
  }
  if (response_type !== 'code') {
    return c.json({ error: 'unsupported_response_type' }, 400)
  }
  if (!redirect_uri) {
    return c.json({ error: 'invalid_request', error_description: 'redirect_uri is required' }, 400)
  }
  if (!ALLOWED_REDIRECT_URIS.includes(redirect_uri)) {
    return c.json({ error: 'invalid_redirect_uri', error_description: 'redirect_uri not in allowlist' }, 400)
  }
  if (!code_challenge) {
    return c.json({ error: 'invalid_request', error_description: 'code_challenge is required' }, 400)
  }
  if (code_challenge_method !== 'S256') {
    return c.json(
      { error: 'invalid_request', error_description: 'code_challenge_method must be S256' },
      400,
    )
  }

  const code = randomBytes(16).toString('hex')
  storeAuthCode(code, {
    clientId: client_id,
    redirectUri: redirect_uri,
    codeChallenge: code_challenge,
    codeChallengeMethod: 'S256',
    sub: 'anonymous', // stub subject — real OIDC would populate from session
    expiresAt: Date.now() + AUTH_CODE_TTL_MS,
  })

  const redirectUrl = new URL(redirect_uri)
  redirectUrl.searchParams.set('code', code)
  if (state) redirectUrl.searchParams.set('state', state)

  return c.redirect(redirectUrl.toString())
})

// POST /token — Authorization code exchange
auth.post('/token', async (c) => {
  let body: Record<string, string>
  try {
    const contentType = c.req.header('Content-Type') ?? ''
    if (contentType.includes('application/json')) {
      body = (await c.req.json()) as Record<string, string>
    } else {
      const formData = await c.req.parseBody()
      body = Object.fromEntries(
        Object.entries(formData).map(([k, v]) => [k, String(v)]),
      ) as Record<string, string>
    }
  } catch {
    return c.json({ error: 'invalid_request', error_description: 'Unable to parse request body' }, 400)
  }

  const { grant_type, code, code_verifier, redirect_uri, client_id } = body

  if (grant_type !== 'authorization_code') {
    return c.json({ error: 'unsupported_grant_type' }, 400)
  }
  if (client_id !== ALLOWED_CLIENT_ID) {
    return c.json({ error: 'unauthorized_client' }, 400)
  }
  if (!code || !code_verifier || !redirect_uri) {
    return c.json(
      { error: 'invalid_request', error_description: 'code, code_verifier, redirect_uri are required' },
      400,
    )
  }

  const entry = consumeAuthCode(code)
  if (!entry) {
    return c.json({ error: 'invalid_grant', error_description: 'Auth code invalid or expired' }, 400)
  }
  if (entry.redirectUri !== redirect_uri) {
    return c.json({ error: 'invalid_grant', error_description: 'redirect_uri mismatch' }, 400)
  }
  if (!verifyCodeChallenge(code_verifier, entry.codeChallenge)) {
    return c.json({ error: 'invalid_grant', error_description: 'code_verifier mismatch' }, 400)
  }

  const audUri = process.env.MCP_SERVER_URI ?? 'http://localhost:8000'
  const accessToken = await signAccessToken({ sub: entry.sub, scope: 'mcp', aud: audUri })
  const refreshToken = await signRefreshToken(entry.sub)

  registerRefreshToken(refreshToken)

  setCookie(c, REFRESH_COOKIE, refreshToken, {
    httpOnly: true,
    sameSite: 'Strict',
    path: '/auth',
    maxAge: Number(process.env.REFRESH_TOKEN_EXPIRY_SECONDS ?? 86400),
    secure: process.env.NODE_ENV === 'production',
  })

  return c.json({
    access_token: accessToken,
    token_type: 'Bearer',
    expires_in: Number(process.env.JWT_EXPIRY_SECONDS ?? 900),
  })
})

// POST /refresh — Refresh token rotation
auth.post('/refresh', async (c) => {
  const oldRefreshToken = getCookie(c, REFRESH_COOKIE)

  if (!oldRefreshToken) {
    return c.json({ error: 'invalid_request', error_description: 'No refresh token cookie' }, 401)
  }

  try {
    const payload = await verifyRefreshToken(oldRefreshToken)
    const sub = typeof payload.sub === 'string' ? payload.sub : 'anonymous'

    const newRefreshToken = await signRefreshToken(sub)
    const rotated = rotateRefreshToken(oldRefreshToken, newRefreshToken)

    if (!rotated) {
      // Token not in active set — replay attack or already rotated
      return c.json({ error: 'invalid_grant', error_description: 'Refresh token already used or revoked' }, 401)
    }

    const audUri = process.env.MCP_SERVER_URI ?? 'http://localhost:8000'
    const accessToken = await signAccessToken({ sub, scope: 'mcp', aud: audUri })

    setCookie(c, REFRESH_COOKIE, newRefreshToken, {
      httpOnly: true,
      sameSite: 'Strict',
      path: '/auth',
      maxAge: Number(process.env.REFRESH_TOKEN_EXPIRY_SECONDS ?? 86400),
      secure: process.env.NODE_ENV === 'production',
    })

    return c.json({
      access_token: accessToken,
      token_type: 'Bearer',
      expires_in: Number(process.env.JWT_EXPIRY_SECONDS ?? 900),
    })
  } catch {
    return c.json({ error: 'invalid_grant', error_description: 'Invalid refresh token' }, 401)
  }
})

// DELETE /session — Clear refresh cookie and revoke token
auth.delete('/session', (c) => {
  const refreshToken = getCookie(c, REFRESH_COOKIE)
  if (refreshToken) {
    revokeRefreshToken(refreshToken)
  }
  deleteCookie(c, REFRESH_COOKIE, { path: '/auth' })
  return new Response(null, { status: 204 })
})

export default auth
