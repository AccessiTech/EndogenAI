/**
 * A2A Request Handler.
 *
 * Processes incoming JSON-RPC 2.0 requests conforming to the A2A protocol.
 * Supported methods:
 *   - tasks/send      — submit a task with an initial message
 *   - tasks/get       — retrieve a task by ID
 *   - tasks/cancel    — cancel a running task
 *   - tasks/addMessage — append a message to an active task
 *
 * Aligned with A2A specification v0.3.0
 * https://github.com/a2aproject/A2A/releases/tag/v0.3.0
 */

import type { TaskOrchestrator } from './orchestrator.js';
import type { AgentRef, TraceContext, A2ARequest, A2AResponse } from './types.js';

/** JSON-RPC error codes */
export const A2A_ERROR_CODES = {
  PARSE_ERROR: -32700,
  INVALID_REQUEST: -32600,
  METHOD_NOT_FOUND: -32601,
  INVALID_PARAMS: -32602,
  INTERNAL_ERROR: -32603,
  TASK_NOT_FOUND: -32001,
  TASK_TERMINAL: -32002,
} as const;

export class A2ARequestHandler {
  constructor(private readonly orchestrator: TaskOrchestrator) {}

  /**
   * Handle a JSON-RPC 2.0 request.
   * Returns a JSON-RPC response object.
   */
  async handle(raw: unknown): Promise<A2AResponse> {
    // Validate basic JSON-RPC shape
    if (!raw || typeof raw !== 'object') {
      return this.errorResponse(null, A2A_ERROR_CODES.INVALID_REQUEST, 'Request must be an object');
    }

    const req = raw as Partial<A2ARequest>;

    if (req.jsonrpc !== '2.0' || !req.method) {
      return this.errorResponse(
        req.id ?? null,
        A2A_ERROR_CODES.INVALID_REQUEST,
        'Invalid JSON-RPC 2.0 request',
      );
    }

    const id = req.id ?? null;
    const params = (req.params ?? {}) as Record<string, unknown>;

    try {
      switch (req.method) {
        case 'tasks/send': {
          const task = this.orchestrator.submit({
            initialMessage: params['message'],
            requester: params['requester'] as AgentRef | undefined,
            assignedAgent: params['assignedAgent'] as AgentRef | undefined,
            sessionId: params['sessionId'] as string | undefined,
            traceContext: params['traceContext'] as TraceContext | undefined,
            metadata: params['metadata'] as Record<string, string> | undefined,
          });
          return this.successResponse(id, task);
        }

        case 'tasks/get': {
          const taskId = params['taskId'] as string | undefined;
          if (!taskId) {
            return this.errorResponse(id, A2A_ERROR_CODES.INVALID_PARAMS, 'Missing taskId');
          }
          const task = this.orchestrator.get(taskId);
          if (!task) {
            return this.errorResponse(
              id,
              A2A_ERROR_CODES.TASK_NOT_FOUND,
              `Task not found: ${taskId}`,
            );
          }
          return this.successResponse(id, task);
        }

        case 'tasks/cancel': {
          const taskId = params['taskId'] as string | undefined;
          if (!taskId) {
            return this.errorResponse(id, A2A_ERROR_CODES.INVALID_PARAMS, 'Missing taskId');
          }
          const task = this.orchestrator.cancel(taskId);
          return this.successResponse(id, task);
        }

        case 'tasks/addMessage': {
          const taskId = params['taskId'] as string | undefined;
          if (!taskId) {
            return this.errorResponse(id, A2A_ERROR_CODES.INVALID_PARAMS, 'Missing taskId');
          }
          const task = this.orchestrator.addMessage(taskId, params['message']);
          return this.successResponse(id, task);
        }

        default:
          return this.errorResponse(
            id,
            A2A_ERROR_CODES.METHOD_NOT_FOUND,
            `Method not found: ${req.method}`,
          );
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      const code = message.includes('terminal')
        ? A2A_ERROR_CODES.TASK_TERMINAL
        : message.includes('not found')
          ? A2A_ERROR_CODES.TASK_NOT_FOUND
          : A2A_ERROR_CODES.INTERNAL_ERROR;
      return this.errorResponse(id, code, message);
    }
  }

  private successResponse<T>(id: string | number | null, result: T): A2AResponse<T> {
    return { jsonrpc: '2.0', id: id ?? null, result };
  }

  private errorResponse(
    id: string | number | null | undefined,
    code: number,
    message: string,
  ): A2AResponse {
    return { jsonrpc: '2.0', id: id ?? null, error: { code, message } };
  }
}
