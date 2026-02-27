/**
 * Integration tests for the MCP + A2A Adapter Bridge (MCPToA2ABridge).
 *
 * These tests verify the round-trip:
 *   A2A task send → MCP context publish → MCP handler → MCP reply → A2A task completion
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { v4 as uuidv4 } from 'uuid';
import { CapabilityRegistry, StateSynchronizer, ContextBroker } from '@accessitech/mcp';
import { TaskOrchestrator } from '@accessitech/a2a';
import { MCPToA2ABridge } from '../src/bridge.js';
import type { MCPContext } from '@accessitech/mcp';
import type { A2AMessage } from '@accessitech/a2a';

function makeMessage(overrides: Partial<A2AMessage> = {}): A2AMessage {
  return {
    id: uuidv4(),
    role: 'user',
    parts: [{ type: 'text', text: 'Hello from A2A' }],
    timestamp: new Date().toISOString(),
    ...overrides,
  };
}

const BRIDGE_SOURCE = { moduleId: 'mcp-a2a-bridge', layer: 'infrastructure' };
const REPLY_TARGET = 'bridge-reply-target';

describe('MCPToA2ABridge', () => {
  let registry: CapabilityRegistry;
  let sync: StateSynchronizer;
  let broker: ContextBroker;
  let orchestrator: TaskOrchestrator;
  let bridge: MCPToA2ABridge;

  beforeEach(() => {
    registry = new CapabilityRegistry();
    sync = new StateSynchronizer();
    broker = new ContextBroker(registry, sync);
    orchestrator = new TaskOrchestrator();
    bridge = new MCPToA2ABridge(broker, orchestrator, {
      source: BRIDGE_SOURCE,
      replyTargetModuleId: REPLY_TARGET,
    });
  });

  it('submits an A2A task and publishes an MCPContext', async () => {
    const published: MCPContext[] = [];
    broker.subscribeBroadcast(async (ctx) => {
      published.push(ctx);
    });

    const result = await bridge.sendAndRoute({ message: makeMessage() });

    expect(result.taskId).toBeDefined();
    expect(result.contextId).toBeDefined();
    expect(result.task.status.state).toBe('working');
    expect(published).toHaveLength(1);
    expect(published[0]?.taskId).toBe(result.taskId);
  });

  it('published MCPContext contains the A2A message in payload', async () => {
    const published: MCPContext[] = [];
    broker.subscribeBroadcast(async (ctx) => {
      published.push(ctx);
    });

    const msg = makeMessage();
    await bridge.sendAndRoute({ message: msg });

    const payload = published[0]?.payload as Record<string, unknown>;
    expect(payload?.['taskId']).toBeDefined();
    const embeddedMsg = payload?.['message'] as Record<string, unknown>;
    expect(embeddedMsg?.['id']).toBe(msg.id);
  });

  it('round-trip: MCP reply auto-completes the A2A task', async () => {
    const result = await bridge.sendAndRoute({ message: makeMessage() });
    const taskId = result.taskId;

    // Simulate a module replying via MCP, addressed to the reply target
    const reply: MCPContext = {
      id: uuidv4(),
      version: '0.1.0',
      timestamp: new Date().toISOString(),
      source: { moduleId: 'worker-module', layer: 'perception' },
      destination: { moduleId: REPLY_TARGET, layer: 'infrastructure' },
      contentType: 'application/json',
      payload: { answer: 42 },
      taskId,
      priority: 5,
    };
    await broker.publish(reply);

    const task = orchestrator.get(taskId)!;
    expect(task.status.state).toBe('completed');
    expect(task.artifacts).toHaveLength(1);
    expect(task.artifacts[0]?.name).toBe('mcp-reply');
    const data = (task.artifacts[0]?.parts[0] as { data: Record<string, unknown> }).data;
    expect(data['contextId']).toBe(reply.id);
    expect((data['payload'] as Record<string, unknown>)['answer']).toBe(42);
  });

  it('MCP reply without taskId does not affect any task', async () => {
    const result = await bridge.sendAndRoute({ message: makeMessage() });

    const replyNoTask: MCPContext = {
      id: uuidv4(),
      version: '0.1.0',
      timestamp: new Date().toISOString(),
      source: { moduleId: 'worker-module', layer: 'perception' },
      destination: { moduleId: REPLY_TARGET, layer: 'infrastructure' },
      contentType: 'application/json',
      payload: { data: 'no task' },
      // No taskId
      priority: 5,
    };
    await broker.publish(replyNoTask);

    // Task should remain working since reply had no taskId
    expect(orchestrator.get(result.taskId)?.status.state).toBe('working');
  });

  it('MCP reply to a completed task is ignored', async () => {
    const result = await bridge.sendAndRoute({ message: makeMessage() });
    const taskId = result.taskId;

    // First reply completes the task
    await broker.publish({
      id: uuidv4(),
      version: '0.1.0',
      timestamp: new Date().toISOString(),
      source: { moduleId: 'worker', layer: 'perception' },
      destination: { moduleId: REPLY_TARGET, layer: 'infrastructure' },
      contentType: 'application/json',
      payload: { first: true },
      taskId,
      priority: 5,
    });

    expect(orchestrator.get(taskId)?.status.state).toBe('completed');

    // Second reply should be a no-op (terminal state)
    await broker.publish({
      id: uuidv4(),
      version: '0.1.0',
      timestamp: new Date().toISOString(),
      source: { moduleId: 'worker', layer: 'perception' },
      destination: { moduleId: REPLY_TARGET, layer: 'infrastructure' },
      contentType: 'application/json',
      payload: { second: true },
      taskId,
      priority: 5,
    });

    // Still completed, artifacts unchanged
    expect(orchestrator.get(taskId)?.artifacts).toHaveLength(1);
  });

  it('propagates sessionId from A2A task to MCPContext', async () => {
    const published: MCPContext[] = [];
    broker.subscribeBroadcast(async (ctx) => published.push(ctx));

    await bridge.sendAndRoute({ message: makeMessage(), sessionId: 'test-session' });

    expect(published[0]?.sessionId).toBe('test-session');
  });
});
