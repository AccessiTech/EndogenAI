/**
 * Integration tests for the A2A HTTP server (createA2AServer).
 * Starts the server on a random port and verifies HTTP endpoints.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { v4 as uuidv4 } from 'uuid';
import { createA2AServer } from '../src/server.js';
import type { A2AServerInstance } from '../src/server.js';
import type { A2AMessage } from '../src/types.js';

const TEST_AGENT_CARD = {
  id: 'test-a2a-server',
  name: 'Test A2A Server',
  version: '0.0.1',
  description: 'Test agent for integration tests',
  url: 'http://localhost',
  skills: [],
};

function makeMessage(): A2AMessage {
  return {
    id: uuidv4(),
    role: 'user',
    parts: [{ type: 'text', text: 'test' }],
    timestamp: new Date().toISOString(),
  };
}

async function rpc(
  port: number,
  method: string,
  params: Record<string, unknown> = {},
): Promise<unknown> {
  const resp = await fetch(`http://localhost:${port}/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ jsonrpc: '2.0', id: 1, method, params }),
  });
  return resp.json();
}

describe('A2A HTTP Server', () => {
  let instance: A2AServerInstance;
  let port: number;

  beforeEach(async () => {
    instance = createA2AServer({ agentCard: TEST_AGENT_CARD });
    port = await instance.listen();
  });

  afterEach(async () => {
    await instance.close();
  });

  it('serves agent-card.json at /.well-known/agent-card.json', async () => {
    const resp = await fetch(`http://localhost:${port}/.well-known/agent-card.json`);
    expect(resp.status).toBe(200);
    const card = await resp.json();
    expect((card as { id: string }).id).toBe('test-a2a-server');
  });

  it('returns 404 for unknown routes', async () => {
    const resp = await fetch(`http://localhost:${port}/unknown`);
    expect(resp.status).toBe(404);
  });

  it('handles tasks/send via POST /', async () => {
    const resp = await rpc(port, 'tasks/send', { message: makeMessage() }) as {
      result: { id: string; status: { state: string } };
    };
    expect(resp.result.status.state).toBe('submitted');
    expect(resp.result.id).toBeDefined();
  });

  it('handles tasks/get via POST /', async () => {
    const send = await rpc(port, 'tasks/send', {}) as { result: { id: string } };
    const taskId = send.result.id;
    const get = await rpc(port, 'tasks/get', { taskId }) as {
      result: { id: string };
    };
    expect(get.result.id).toBe(taskId);
  });

  it('handles tasks/cancel via POST /', async () => {
    const send = await rpc(port, 'tasks/send', {}) as { result: { id: string } };
    const taskId = send.result.id;
    const cancel = await rpc(port, 'tasks/cancel', { taskId }) as {
      result: { status: { state: string } };
    };
    expect(cancel.result.status.state).toBe('canceled');
  });

  it('returns parse error for invalid JSON body', async () => {
    const resp = await fetch(`http://localhost:${port}/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: 'not json',
    });
    const body = await resp.json() as { error: { code: number } };
    expect(body.error.code).toBe(-32700);
  });
});
