/**
 * Typed gateway API client.
 * All requests route through the Vite proxy to http://localhost:3001 in dev,
 * or direct to VITE_GATEWAY_URL in production.
 */

const GATEWAY = import.meta.env['VITE_GATEWAY_URL'] ?? ''

export interface SendInputResponse {
  sessionId: string
  streamPath: string
}

export interface AgentEntry {
  name: string
  url: string
}

export interface AgentCard {
  name: string
  version: string
  description: string
  url: string
  capabilities: {
    mcp: boolean
    a2a: boolean
    sse?: boolean
  }
  neuroanatomicalAnalogue?: string
  tools?: Array<{ name: string; description?: string }>
}

export interface ResourceEntry {
  uri: string
  mimeType?: string
  name?: string
  description?: string
  group?: string
  backend?: string
  accessControl?: string
  recordCount?: number
  lastUpdated?: string
}

async function apiFetch<T>(
  path: string,
  token: string | null,
  options?: RequestInit,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string>),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${GATEWAY}${path}`, {
    ...options,
    headers,
    credentials: 'include',
  })

  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`)
  }

  const contentType = res.headers.get('content-type') ?? ''
  if (contentType.includes('application/json')) {
    return res.json() as Promise<T>
  }
  return res.text() as unknown as T
}

export const gateway = {
  health: (token: string | null) =>
    apiFetch<{ status: string }>('/api/health', token),

  sendInput: (token: string | null, content: string, sessionId?: string) =>
    apiFetch<SendInputResponse>('/api/input', token, {
      method: 'POST',
      body: JSON.stringify({ content, sessionId }),
    }),

  listAgents: (token: string | null) =>
    apiFetch<AgentEntry[]>('/api/agents', token),

  fetchAgentCard: async (token: string | null, agentUrl: string): Promise<AgentCard> => {
    const headers: Record<string, string> = {}
    if (token) headers['Authorization'] = `Bearer ${token}`
    const res = await fetch(`${agentUrl}/.well-known/agent-card.json`, {
      headers,
      credentials: 'include',
    })
    if (!res.ok) throw new Error(`Agent card fetch failed: ${res.status}`)
    return res.json() as Promise<AgentCard>
  },

  listResources: (token: string | null, group?: string) => {
    const params = group ? `?group=${encodeURIComponent(group)}` : ''
    return apiFetch<ResourceEntry[]>(`/api/resources${params}`, token)
  },
}
