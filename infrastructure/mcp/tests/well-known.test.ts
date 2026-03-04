/**
 * Tests for /.well-known/oauth-protected-resource handler.
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { createServer } from 'node:http'
import type { Server } from 'node:http'
import { handleWellKnownRequest, buildProtectedResourceMetadata } from '../src/well-known.js'

// ── Unit tests (no HTTP) ────────────────────────────────────────────────────

describe('buildProtectedResourceMetadata', () => {
  it('uses default values when env vars are absent', () => {
    delete process.env.MCP_SERVER_URI
    delete process.env.AUTH_SERVER_URL

    const meta = buildProtectedResourceMetadata()
    expect(meta.resource).toBe('http://localhost:8000')
    expect(meta.authorization_servers).toEqual(['http://localhost:3001'])
    expect(meta.bearer_methods_supported).toContain('header')
    expect(meta.resource_documentation).toBeTruthy()
  })

  it('uses env var values when set', () => {
    process.env.MCP_SERVER_URI = 'https://mcp.example.com'
    process.env.AUTH_SERVER_URL = 'https://auth.example.com'

    const meta = buildProtectedResourceMetadata()
    expect(meta.resource).toBe('https://mcp.example.com')
    expect(meta.authorization_servers).toEqual(['https://auth.example.com'])

    delete process.env.MCP_SERVER_URI
    delete process.env.AUTH_SERVER_URL
  })
})

// ── Integration tests (real HTTP server) ────────────────────────────────────

let server: Server
let baseUrl: string

beforeAll(
  () =>
    new Promise<void>((resolve) => {
      server = createServer((req, res) => {
        if (!handleWellKnownRequest(req, res)) {
          res.writeHead(404)
          res.end('Not Found')
        }
      })
      server.listen(0, '127.0.0.1', () => {
        const addr = server.address()
        const port = typeof addr === 'object' && addr ? addr.port : 0
        baseUrl = `http://127.0.0.1:${port}`
        resolve()
      })
    }),
)

afterAll(
  () =>
    new Promise<void>((resolve) => {
      server.close(() => resolve())
    }),
)

describe('GET /.well-known/oauth-protected-resource', () => {
  it('returns 200 with application/json content-type', async () => {
    const res = await fetch(`${baseUrl}/.well-known/oauth-protected-resource`)
    expect(res.status).toBe(200)
    expect(res.headers.get('content-type')).toMatch(/application\/json/)
  })

  it('returns valid metadata document structure', async () => {
    const res = await fetch(`${baseUrl}/.well-known/oauth-protected-resource`)
    const body = await res.json() as {
      resource: string
      authorization_servers: string[]
      bearer_methods_supported: string[]
      resource_documentation: string
    }
    expect(body.resource).toBeTruthy()
    expect(Array.isArray(body.authorization_servers)).toBe(true)
    expect(body.authorization_servers.length).toBeGreaterThan(0)
    expect(body.bearer_methods_supported).toContain('header')
    expect(body.resource_documentation).toBeTruthy()
  })

  it('sets Cache-Control: no-store', async () => {
    const res = await fetch(`${baseUrl}/.well-known/oauth-protected-resource`)
    expect(res.headers.get('cache-control')).toBe('no-store')
  })
})

describe('Unknown routes', () => {
  it('returns 404 for unknown paths', async () => {
    const res = await fetch(`${baseUrl}/unknown`)
    expect(res.status).toBe(404)
  })
})
