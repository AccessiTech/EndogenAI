/**
 * A2A Protocol Conformance Tests
 *
 * # spec-version: v0.3.0
 * # spec-commit: 2d3dc909972d9680b974e0fc9a1354c1ba8f519d
 * # spec-url: https://github.com/a2aproject/A2A/releases/tag/v0.3.0
 *
 * Verifies that TaskOrchestrator and A2ARequestHandler conform to the
 * A2A specification task lifecycle and JSON-RPC transport requirements.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { v4 as uuidv4 } from 'uuid';
import { TaskOrchestrator } from '../src/orchestrator.js';
import { A2ARequestHandler, A2A_ERROR_CODES } from '../src/handler.js';
import type { A2AMessage } from '../src/types.js';

function makeMessage(overrides: Partial<A2AMessage> = {}): A2AMessage {
  return {
    id: uuidv4(),
    role: 'user',
    parts: [{ type: 'text', text: 'Hello' }],
    timestamp: new Date().toISOString(),
    ...overrides,
  };
}

describe('A2A Conformance: Task Lifecycle', () => {
  let orchestrator: TaskOrchestrator;

  beforeEach(() => {
    orchestrator = new TaskOrchestrator();
  });

  it('[spec] task is created in submitted state', () => {
    const task = orchestrator.submit({});
    expect(task.status.state).toBe('submitted');
    expect(task.id).toBeDefined();
    expect(task.createdAt).toBeDefined();
    expect(task.updatedAt).toBeDefined();
  });

  it('[spec] submitted → working transition', () => {
    const task = orchestrator.submit({});
    const working = orchestrator.startWork(task.id);
    expect(working.status.state).toBe('working');
  });

  it('[spec] working → completed with artifacts', () => {
    const task = orchestrator.submit({});
    orchestrator.startWork(task.id);
    const artifact = { id: uuidv4(), name: 'result', parts: [{ type: 'text' as const, text: 'done' }] };
    const completed = orchestrator.complete(task.id, [artifact]);
    expect(completed.status.state).toBe('completed');
    expect(completed.artifacts).toHaveLength(1);
    expect(completed.artifacts[0]?.name).toBe('result');
  });

  it('[spec] working → failed with error', () => {
    const task = orchestrator.submit({});
    orchestrator.startWork(task.id);
    const failed = orchestrator.fail(task.id, {
      code: 'PROCESSING_ERROR',
      message: 'Something went wrong',
      retryable: true,
    });
    expect(failed.status.state).toBe('failed');
    expect(failed.error?.retryable).toBe(true);
  });

  it('[spec] working → input-required → working', () => {
    const task = orchestrator.submit({});
    orchestrator.startWork(task.id);
    orchestrator.requestInput(task.id, { message: 'What is your name?' });
    expect(orchestrator.get(task.id)?.status.state).toBe('input-required');
    orchestrator.startWork(task.id);
    expect(orchestrator.get(task.id)?.status.state).toBe('working');
  });

  it('[spec] submitted → canceled', () => {
    const task = orchestrator.submit({});
    const canceled = orchestrator.cancel(task.id);
    expect(canceled.status.state).toBe('canceled');
  });

  it('[spec] terminal state prevents further transitions', () => {
    const task = orchestrator.submit({});
    orchestrator.cancel(task.id);
    expect(() => orchestrator.startWork(task.id)).toThrow('terminal');
    expect(() => orchestrator.cancel(task.id)).toThrow('terminal');
  });

  it('[spec] messages are appended to history with taskId', () => {
    const task = orchestrator.submit({});
    orchestrator.startWork(task.id);
    orchestrator.addMessage(task.id, makeMessage());
    orchestrator.addMessage(task.id, makeMessage({ role: 'agent' }));
    const updated = orchestrator.get(task.id)!;
    expect(updated.history).toHaveLength(2);
    expect(updated.history[0]?.taskId).toBe(task.id);
  });

  it('[spec] initial message is stored in history', () => {
    const msg = makeMessage();
    const task = orchestrator.submit({ initialMessage: msg });
    expect(task.history).toHaveLength(1);
    expect(task.history[0]?.id).toBe(msg.id);
    expect(task.history[0]?.taskId).toBe(task.id);
  });
});

describe('A2A Conformance: JSON-RPC Transport', () => {
  let orchestrator: TaskOrchestrator;
  let handler: A2ARequestHandler;

  beforeEach(() => {
    orchestrator = new TaskOrchestrator();
    handler = new A2ARequestHandler(orchestrator);
  });

  it('[spec] tasks/send returns a task in submitted state', async () => {
    const resp = await handler.handle({
      jsonrpc: '2.0',
      id: 1,
      method: 'tasks/send',
      params: { message: makeMessage() },
    });
    expect(resp.error).toBeUndefined();
    expect((resp.result as { status?: { state: string } })?.status?.state).toBe('submitted');
  });

  it('[spec] tasks/get retrieves the task', async () => {
    const submit = await handler.handle({
      jsonrpc: '2.0',
      id: 1,
      method: 'tasks/send',
      params: {},
    });
    const taskId = (submit.result as { id: string })?.id;
    const get = await handler.handle({
      jsonrpc: '2.0',
      id: 2,
      method: 'tasks/get',
      params: { taskId },
    });
    expect(get.error).toBeUndefined();
    expect((get.result as { id: string })?.id).toBe(taskId);
  });

  it('[spec] tasks/get returns error for unknown task', async () => {
    const resp = await handler.handle({
      jsonrpc: '2.0',
      id: 3,
      method: 'tasks/get',
      params: { taskId: uuidv4() },
    });
    expect(resp.error?.code).toBe(A2A_ERROR_CODES.TASK_NOT_FOUND);
  });

  it('[spec] tasks/cancel transitions task to canceled', async () => {
    const submit = await handler.handle({
      jsonrpc: '2.0', id: 1, method: 'tasks/send', params: {},
    });
    const taskId = (submit.result as { id: string })?.id;
    const cancel = await handler.handle({
      jsonrpc: '2.0', id: 2, method: 'tasks/cancel', params: { taskId },
    });
    expect((cancel.result as { status?: { state: string } })?.status?.state).toBe('canceled');
  });

  it('[spec] unknown method returns METHOD_NOT_FOUND', async () => {
    const resp = await handler.handle({
      jsonrpc: '2.0', id: 1, method: 'tasks/unknown', params: {},
    });
    expect(resp.error?.code).toBe(A2A_ERROR_CODES.METHOD_NOT_FOUND);
  });

  it('[spec] invalid JSON-RPC returns INVALID_REQUEST', async () => {
    const resp = await handler.handle({ method: 'tasks/send' });
    expect(resp.error?.code).toBe(A2A_ERROR_CODES.INVALID_REQUEST);
  });

  it('[spec] non-object request returns INVALID_REQUEST', async () => {
    const resp = await handler.handle('not an object');
    expect(resp.error?.code).toBe(A2A_ERROR_CODES.INVALID_REQUEST);
  });
});
