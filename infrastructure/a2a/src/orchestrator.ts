/**
 * Task Orchestrator for the EndogenAI A2A infrastructure.
 *
 * Manages the full lifecycle of A2ATask objects:
 *   submitted → working → { input-required → working | completed | failed | canceled }
 *
 * Aligned with A2A specification v0.3.0
 * https://github.com/a2aproject/A2A/releases/tag/v0.3.0
 */

import { v4 as uuidv4 } from 'uuid';
import { validateA2AMessage } from './validate.js';
import { TERMINAL_STATES } from './types.js';
import type {
  A2ATask,
  A2AMessage,
  Artifact,
  TaskError,
  AgentRef,
  InputRequest,
  TraceContext,
} from './types.js';

export class TaskOrchestrator {
  private tasks = new Map<string, A2ATask>();

  /**
   * Submit a new task. Returns the created A2ATask in 'submitted' state.
   */
  submit(options: {
    requester?: AgentRef;
    assignedAgent?: AgentRef;
    sessionId?: string;
    initialMessage?: unknown;
    traceContext?: TraceContext;
    metadata?: Record<string, string>;
  }): A2ATask {
    const now = new Date().toISOString();
    const task: A2ATask = {
      id: uuidv4(),
      status: { state: 'submitted' },
      createdAt: now,
      updatedAt: now,
      history: [],
      artifacts: [],
      sessionId: options.sessionId,
      requester: options.requester,
      assignedAgent: options.assignedAgent,
      traceContext: options.traceContext,
      metadata: options.metadata,
    };

    if (options.initialMessage !== undefined) {
      const msg = validateA2AMessage(options.initialMessage);
      task.history.push({ ...msg, taskId: task.id });
    }

    this.tasks.set(task.id, task);
    return task;
  }

  /** Get a task by ID. */
  get(taskId: string): A2ATask | undefined {
    return this.tasks.get(taskId);
  }

  /** Returns all tasks. */
  list(): A2ATask[] {
    return Array.from(this.tasks.values());
  }

  /** Transition task to 'working'. Throws if already terminal. */
  startWork(taskId: string): A2ATask {
    return this.transition(taskId, 'working');
  }

  /** Append a message to the task history and return the updated task. */
  addMessage(taskId: string, message: unknown): A2ATask {
    const task = this.requireTask(taskId);
    this.requireNonTerminal(task);
    const msg = validateA2AMessage(message);
    task.history.push({ ...msg, taskId });
    task.updatedAt = new Date().toISOString();
    return task;
  }

  /** Mark the task as requiring additional input. */
  requestInput(taskId: string, inputRequest: InputRequest): A2ATask {
    const task = this.requireTask(taskId);
    this.requireNonTerminal(task);
    task.status = { state: 'input-required' };
    task.inputRequest = inputRequest;
    task.updatedAt = new Date().toISOString();
    return task;
  }

  /** Complete the task with output artifacts. */
  complete(taskId: string, artifacts: Artifact[]): A2ATask {
    const task = this.requireTask(taskId);
    this.requireNonTerminal(task);
    task.status = { state: 'completed' };
    task.artifacts = artifacts;
    task.inputRequest = undefined;
    task.updatedAt = new Date().toISOString();
    return task;
  }

  /** Fail the task with an error. */
  fail(taskId: string, error: TaskError): A2ATask {
    const task = this.requireTask(taskId);
    this.requireNonTerminal(task);
    task.status = { state: 'failed' };
    task.error = error;
    task.updatedAt = new Date().toISOString();
    return task;
  }

  /** Cancel the task. */
  cancel(taskId: string): A2ATask {
    const task = this.requireTask(taskId);
    this.requireNonTerminal(task);
    task.status = { state: 'canceled' };
    task.updatedAt = new Date().toISOString();
    return task;
  }

  /** Return count of tasks. */
  size(): number {
    return this.tasks.size;
  }

  /** Clear all tasks (for testing). */
  clear(): void {
    this.tasks.clear();
  }

  // ── Private helpers ──────────────────────────────────────────────────────────────

  private requireTask(taskId: string): A2ATask {
    const task = this.tasks.get(taskId);
    if (!task) throw new Error(`Task not found: ${taskId}`);
    return task;
  }

  private requireNonTerminal(task: A2ATask): void {
    if (TERMINAL_STATES.has(task.status.state)) {
      throw new Error(
        `Task ${task.id} is in terminal state '${task.status.state}' and cannot be modified.`,
      );
    }
  }

  private transition(taskId: string, state: A2ATask['status']['state']): A2ATask {
    const task = this.requireTask(taskId);
    this.requireNonTerminal(task);
    task.status = { state };
    task.updatedAt = new Date().toISOString();
    return task;
  }
}
