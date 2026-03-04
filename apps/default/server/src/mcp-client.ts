/**
 * MCP Streamable HTTP client for the Hono gateway.
 * Implements MCP 2025-06-18 Streamable HTTP transport.
 */
import { propagation, context } from '@opentelemetry/api'

export interface McpMessage {
  jsonrpc: '2.0'
  id?: string | number
  method: string
  params?: unknown
}

export interface McpEvent {
  data: string
  type?: string
  id?: string
}

export class McpClient {
  private sessionId: string | undefined
  private readonly serverUrl: string

  constructor(serverUrl: string) {
    this.serverUrl = serverUrl
  }

  async initialize(): Promise<void> {
    const res = await this.post({
      jsonrpc: '2.0',
      id: 1,
      method: 'initialize',
      params: { protocolVersion: '2025-06-18', capabilities: {} },
    })
    if (!res.ok) {
      throw new Error(`MCP initialize failed: ${res.status}`)
    }
    this.sessionId = res.headers.get('Mcp-Session-Id') ?? undefined
  }

  async send(message: McpMessage): Promise<Response> {
    return this.post(message)
  }

  async *subscribe(lastEventId?: string): AsyncGenerator<McpEvent> {
    const headers: Record<string, string> = {
      ...this.buildHeaders(),
      Accept: 'text/event-stream',
    }
    if (lastEventId) headers['Last-Event-ID'] = lastEventId

    let res: Response
    try {
      res = await fetch(this.serverUrl, { method: 'GET', headers })
    } catch (err) {
      throw new Error(`MCP SSE connect failed: ${String(err)}`)
    }

    if (!res.ok || !res.body) {
      throw new Error(`MCP SSE error: ${res.status}`)
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let currentEvent: Partial<McpEvent> = {}

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (line === '') {
            // Dispatch event
            if (currentEvent.data !== undefined) {
              yield currentEvent as McpEvent
            }
            currentEvent = {}
          } else if (line.startsWith('data: ')) {
            currentEvent.data = line.slice(6)
          } else if (line.startsWith('event: ')) {
            currentEvent.type = line.slice(7)
          } else if (line.startsWith('id: ')) {
            currentEvent.id = line.slice(4)
          }
        }
      }
    } finally {
      reader.cancel()
    }
  }

  async terminate(): Promise<void> {
    if (!this.sessionId) return
    await fetch(this.serverUrl, {
      method: 'DELETE',
      headers: this.buildHeaders(),
    }).catch(() => undefined) // best-effort
  }

  getSessionId(): string | undefined {
    return this.sessionId
  }

  private async post(body: McpMessage | object): Promise<Response> {
    // Inject W3C TraceContext into outbound MCP HTTP headers (§6.2)
    const traceCarrier: Record<string, string> = {}
    propagation.inject(context.active(), traceCarrier)

    return fetch(this.serverUrl, {
      method: 'POST',
      headers: {
        ...this.buildHeaders(),
        'Content-Type': 'application/json',
        Accept: 'application/json, text/event-stream',
        ...traceCarrier,
      },
      body: JSON.stringify(body),
    })
  }

  private buildHeaders(): Record<string, string> {
    const h: Record<string, string> = { 'MCP-Protocol-Version': '2025-06-18' }
    if (this.sessionId) h['Mcp-Session-Id'] = this.sessionId
    return h
  }
}
