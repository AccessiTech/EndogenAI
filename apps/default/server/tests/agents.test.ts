/**
 * agents.test.ts — unit tests for GET /api/agents
 *
 * Covers:
 *  - Happy path: all modules return valid agent cards
 *  - Partial failure: one module times out / rejects
 *  - All-timeout: every module is unreachable → empty array, 200
 *  - Timestamp format: response includes ISO 8601 timestamp
 */
import { describe, it, expect, beforeAll, afterEach, vi } from 'vitest'
import { createApp } from '../src/app.js'
import { signAccessToken } from '../src/auth/jwt.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

let validToken: string

beforeAll(async () => {
  process.env.JWT_SECRET = 'test-secret'
  process.env.ALLOWED_ORIGINS = 'http://localhost:5173'
})

afterEach(() => {
  vi.restoreAllMocks()
  delete process.env.MODULE_URLS
})

async function getToken() {
  if (!validToken) {
    validToken = await signAccessToken({
      sub: 'test-user',
      scope: 'openid profile',
      aud: 'http://localhost:8000',
    })
  }
  return validToken
}

function authedRequest(path: string) {
  return new Request(`http://localhost${path}`, {
    headers: {
      Authorization: `Bearer ${validToken}`,
      'Content-Type': 'application/json',
    },
  })
}

const CARD_A = { name: 'ModuleA', version: '1.0.0', description: 'Module A', capabilities: {} }
const CARD_B = { name: 'ModuleB', version: '1.0.0', description: 'Module B', capabilities: {} }
const CARD_C = { name: 'ModuleC', version: '1.0.0', description: 'Module C', capabilities: {} }

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('GET /api/agents — happy path', () => {
  it('returns 200 with 3 agent cards when all modules respond', async () => {
    await getToken()
    process.env.MODULE_URLS =
      'http://module-a.test,http://module-b.test,http://module-c.test'

    const cards = [CARD_A, CARD_B, CARD_C]
    let callIndex = 0
    vi.stubGlobal('fetch', vi.fn((_url: string) => {
      const card = cards[callIndex++]
      return Promise.resolve({ json: () => Promise.resolve(card) })
    }))

    const res = await createApp().fetch(authedRequest('/api/agents'))
    expect(res.status).toBe(200)
    const body = await res.json() as { agents: unknown[]; timestamp: string }
    expect(body.agents).toHaveLength(3)
  })
})

describe('GET /api/agents — partial failure', () => {
  it('returns 2 cards when 1 of 3 modules rejects', async () => {
    await getToken()
    process.env.MODULE_URLS =
      'http://module-a.test,http://module-bad.test,http://module-c.test'

    vi.stubGlobal('fetch', vi.fn((url: string) => {
      if ((url as string).includes('module-bad')) {
        return Promise.reject(new Error('Connection refused'))
      }
      const card = (url as string).includes('module-a') ? CARD_A : CARD_C
      return Promise.resolve({ json: () => Promise.resolve(card) })
    }))

    const res = await createApp().fetch(authedRequest('/api/agents'))
    expect(res.status).toBe(200)
    const body = await res.json() as { agents: unknown[] }
    expect(body.agents).toHaveLength(2)
  })
})

describe('GET /api/agents — all timeout', () => {
  it('returns empty agents array with 200 when all modules are unreachable', async () => {
    await getToken()
    process.env.MODULE_URLS =
      'http://module-a.test,http://module-b.test,http://module-c.test'

    vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new Error('Network error'))))

    const res = await createApp().fetch(authedRequest('/api/agents'))
    expect(res.status).toBe(200)
    const body = await res.json() as { agents: unknown[]; timestamp: string }
    expect(body.agents).toHaveLength(0)
    expect(typeof body.timestamp).toBe('string')
  })
})

describe('GET /api/agents — timestamp', () => {
  it('includes a valid ISO 8601 timestamp in the response', async () => {
    await getToken()
    process.env.MODULE_URLS = 'http://module-a.test'

    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve({ json: () => Promise.resolve(CARD_A) }),
    ))

    const res = await createApp().fetch(authedRequest('/api/agents'))
    expect(res.status).toBe(200)
    const body = await res.json() as { agents: unknown[]; timestamp: string }
    expect(typeof body.timestamp).toBe('string')
    // ISO 8601: parseable by Date and not NaN
    const parsed = new Date(body.timestamp).getTime()
    expect(Number.isNaN(parsed)).toBe(false)
  })
})
