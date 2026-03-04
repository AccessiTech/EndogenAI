import { describe, it, expect, vi, beforeEach } from 'vitest'
import { McpClient } from '../src/mcp-client.js'

describe('McpClient', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('initialize stores Mcp-Session-Id from response header', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ 'Mcp-Session-Id': 'test-session-abc' }),
    })
    vi.stubGlobal('fetch', mockFetch)

    const client = new McpClient('http://localhost:8000')
    await client.initialize()
    expect(client.getSessionId()).toBe('test-session-abc')
  })

  it('send includes Mcp-Session-Id header after initialize', async () => {
    const mockFetch = vi.fn()
      .mockResolvedValueOnce({ ok: true, headers: new Headers({ 'Mcp-Session-Id': 'sess-xyz' }) })
      .mockResolvedValueOnce({ ok: true, headers: new Headers() })
    vi.stubGlobal('fetch', mockFetch)

    const client = new McpClient('http://localhost:8000')
    await client.initialize()
    await client.send({ jsonrpc: '2.0', method: 'ping', id: 1 })

    const calls = mockFetch.mock.calls as [unknown, { headers: Record<string, string> }][]
    const secondCall = calls[1]!
    expect(secondCall[1].headers['Mcp-Session-Id']).toBe('sess-xyz')
  })

  it('terminate sends DELETE with session header', async () => {
    const mockFetch = vi.fn()
      .mockResolvedValueOnce({ ok: true, headers: new Headers({ 'Mcp-Session-Id': 'sess-del' }) })
      .mockResolvedValueOnce({ ok: true, headers: new Headers() })
    vi.stubGlobal('fetch', mockFetch)

    const client = new McpClient('http://localhost:8000')
    await client.initialize()
    await client.terminate()

    const calls = mockFetch.mock.calls as [string, { method: string; headers: Record<string, string> }][]
    const deleteCall = calls[1]!
    expect(deleteCall[1].method).toBe('DELETE')
    expect(deleteCall[1].headers['Mcp-Session-Id']).toBe('sess-del')
  })

  it('subscribe sends Last-Event-ID if provided', async () => {
    const sseBody = 'data: hello\n\n'
    const encoder = new TextEncoder()
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(sseBody))
        controller.close()
      },
    })
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      body: stream,
      headers: new Headers(),
    })
    vi.stubGlobal('fetch', mockFetch)

    const client = new McpClient('http://localhost:8000')
    const events: unknown[] = []
    for await (const event of client.subscribe('last-id-123')) {
      events.push(event)
    }

    const calls = mockFetch.mock.calls as [string, { headers: Record<string, string> }][]
    const fetchOptions = calls[1]![1]
    expect(fetchOptions.headers['Last-Event-ID']).toBe('last-id-123')
    expect(events).toHaveLength(1)
    expect((events[0] as { data: string }).data).toBe('hello')
  })
})
