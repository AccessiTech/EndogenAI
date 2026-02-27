/**
 * Integration tests for createMCPServer.
 * Validates that registry, broker, and sync are wired correctly and
 * provides an end-to-end context propagation smoke test.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { v4 as uuidv4 } from 'uuid';
import { createMCPServer } from '../src/server.js';
import type { MCPContext } from '../src/types.js';

function makeContext(overrides: Partial<MCPContext> = {}): MCPContext {
  return {
    id: uuidv4(),
    version: '0.1.0',
    timestamp: new Date().toISOString(),
    source: { moduleId: 'integration-source', layer: 'signal-processing' },
    contentType: 'signal/text',
    payload: { text: 'integration test' },
    priority: 5,
    ...overrides,
  };
}

describe('createMCPServer integration', () => {
  let mcp: ReturnType<typeof createMCPServer>;

  beforeEach(() => {
    mcp = createMCPServer({ name: 'test-mcp', version: '0.0.1' });
  });

  it('creates server with an empty registry', () => {
    expect(mcp.registry.size()).toBe(0);
  });

  it('register + deregister round-trip', () => {
    mcp.registry.register({
      moduleId: 'test-module',
      layer: 'signal-processing',
      accepts: ['signal/text'],
      emits: ['memory/item'],
      version: '0.1.0',
    });
    expect(mcp.registry.size()).toBe(1);
    mcp.registry.deregister('test-module');
    expect(mcp.registry.size()).toBe(0);
  });

  it('publishes a context and routes to subscriber', async () => {
    const handler = vi.fn();
    mcp.broker.subscribe('target', handler);
    await mcp.broker.publish(
      makeContext({ destination: { moduleId: 'target', layer: 'cognitive-processing' } }),
    );
    expect(handler).toHaveBeenCalledOnce();
  });

  it('sync tracks module state after publish', async () => {
    await mcp.broker.publish(makeContext());
    const state = mcp.sync.getState('integration-source');
    expect(state?.state).toBe('idle');
    expect(state?.moduleId).toBe('integration-source');
  });

  it('capability registry + broker routing end-to-end', async () => {
    mcp.registry.register({
      moduleId: 'consumer',
      layer: 'cognitive-processing',
      accepts: ['signal/text'],
      emits: [],
      version: '0.1.0',
    });

    const received: MCPContext[] = [];
    mcp.broker.subscribe('consumer', async (ctx) => {
      received.push(ctx);
    });

    const ctx = makeContext(); // broadcast — routed by content-type match
    await mcp.broker.publish(ctx);

    expect(received).toHaveLength(1);
    expect(received[0]?.id).toBe(ctx.id);
  });

  it('stale detection on StateSynchronizer', async () => {
    mcp.sync.setState('old-module', 'signal-processing', 'idle');
    // Manually backdate lastSeen
    const state = mcp.sync.getState('old-module')!;
    (state as { lastSeen: string }).lastSeen = new Date(
      Date.now() - 60_000,
    ).toISOString();
    const stale = mcp.sync.stale(30_000);
    expect(stale).toHaveLength(1);
    expect(stale[0]?.moduleId).toBe('old-module');
  });
});
