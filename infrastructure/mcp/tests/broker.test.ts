/**
 * Unit tests for ContextBroker
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { v4 as uuidv4 } from 'uuid';
import { ContextBroker } from '../src/broker.js';
import { CapabilityRegistry } from '../src/registry.js';
import { StateSynchronizer } from '../src/sync.js';
import type { MCPContext } from '../src/types.js';

function makeContext(overrides: Partial<MCPContext> = {}): MCPContext {
  return {
    id: uuidv4(),
    version: '0.1.0',
    timestamp: new Date().toISOString(),
    source: { moduleId: 'test-source', layer: 'signal-processing' },
    contentType: 'signal/text',
    payload: { text: 'hello' },
    priority: 5,
    ...overrides,
  };
}

describe('ContextBroker', () => {
  let broker: ContextBroker;
  let registry: CapabilityRegistry;
  let sync: StateSynchronizer;

  beforeEach(() => {
    registry = new CapabilityRegistry();
    sync = new StateSynchronizer();
    broker = new ContextBroker(registry, sync);
  });

  it('routes a directed message to the correct handler', async () => {
    const handler = vi.fn();
    broker.subscribe('target-module', handler);
    const ctx = makeContext({
      destination: { moduleId: 'target-module', layer: 'cognitive-processing' },
    });
    await broker.publish(ctx);
    expect(handler).toHaveBeenCalledOnce();
    expect(handler).toHaveBeenCalledWith(ctx);
  });

  it('does not route a directed message to wrong module', async () => {
    const handler = vi.fn();
    broker.subscribe('other-module', handler);
    await broker.publish(
      makeContext({ destination: { moduleId: 'target-module', layer: 'cognitive-processing' } }),
    );
    expect(handler).not.toHaveBeenCalled();
  });

  it('broadcasts to broadcast subscribers when no destination', async () => {
    const handler = vi.fn();
    broker.subscribeBroadcast(handler);
    await broker.publish(makeContext());
    expect(handler).toHaveBeenCalledOnce();
  });

  it('routes broadcast to capability-matched modules', async () => {
    registry.register({
      moduleId: 'perception',
      layer: 'signal-processing',
      accepts: ['signal/text'],
      emits: ['memory/item'],
      version: '0.1.0',
    });
    const handler = vi.fn();
    broker.subscribe('perception', handler);
    await broker.publish(makeContext());
    expect(handler).toHaveBeenCalledOnce();
  });

  it('records source heartbeat on publish', async () => {
    await broker.publish(makeContext());
    expect(sync.getState('test-source')?.state).toBe('idle');
  });

  it('rejects invalid context', async () => {
    await expect(broker.publish({ bad: 'data' })).rejects.toThrow('Invalid MCPContext');
  });

  it('builds a valid reply context', async () => {
    const original = makeContext({ sessionId: 'sess-1', taskId: 'task-1' });
    const reply = broker.buildReply(
      original,
      { moduleId: 'replier', layer: 'cognitive-processing' },
      'application/json',
      { result: 'ok' },
    );
    expect(reply.correlationId).toBe(original.id);
    expect(reply.destination).toEqual(original.source);
    expect(reply.sessionId).toBe('sess-1');
    expect(reply.taskId).toBe('task-1');
  });

  it('multiple handlers can subscribe to the same module', async () => {
    const h1 = vi.fn();
    const h2 = vi.fn();
    broker.subscribe('target', h1);
    broker.subscribe('target', h2);
    const ctx = makeContext({
      destination: { moduleId: 'target', layer: 'cognitive-processing' },
    });
    await broker.publish(ctx);
    expect(h1).toHaveBeenCalledOnce();
    expect(h2).toHaveBeenCalledOnce();
  });
});
