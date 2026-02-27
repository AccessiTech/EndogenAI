/**
 * MCP + A2A Adapter Bridge.
 *
 * Enables modules to participate in both MCP context exchange and A2A task
 * delegation without duplicated logic. The bridge:
 *
 * 1. Accepts an A2A task initial message and publishes it as an MCPContext
 *    to the MCP context broker (A2A \u2192 MCP direction).
 *
 * 2. Subscribes to MCP context replies for the configured replyTargetModuleId
 *    and writes them back to the originating A2A task as completion artifacts
 *    (MCP \u2192 A2A direction).
 *
 * 3. `sendAndRoute` provides a single call that:
 *    - Submits an A2A task
 *    - Transitions it to 'working'
 *    - Publishes the initial message through MCP
 *    - Returns the task and context IDs for downstream tracking
 */

import { v4 as uuidv4 } from 'uuid';
import type { ContextBroker, MCPContext } from '@accessitech/mcp';
import type {
  TaskOrchestrator,
  A2AMessage,
  A2ATask,
  AgentRef,
} from '@accessitech/a2a';
import { TERMINAL_STATES } from '@accessitech/a2a';
import type { BridgeConfig, BridgeSendResult } from './types.js';

export class MCPToA2ABridge {
  private readonly config: Required<BridgeConfig>;

  constructor(
    private readonly broker: ContextBroker,
    private readonly orchestrator: TaskOrchestrator,
    config: BridgeConfig,
  ) {
    this.config = {
      contentType: 'application/json',
      ...config,
    };

    // Subscribe to MCP replies and route them back to their A2A tasks
    this.broker.subscribe(this.config.replyTargetModuleId, async (ctx) => {
      await this.onMCPReply(ctx);
    });
  }

  /**
   * Submit an A2A task, start work, and publish the initial message as an MCPContext.
   * Returns the task ID and the published context ID.
   */
  async sendAndRoute(options: {
    message: A2AMessage;
    requester?: AgentRef;
    assignedAgent?: AgentRef;
    sessionId?: string;
    metadata?: Record<string, string>;
  }): Promise<BridgeSendResult & { task: A2ATask; context: MCPContext }> {
    // 1. Create the A2A task
    const task = this.orchestrator.submit({
      initialMessage: options.message,
      requester: options.requester,
      assignedAgent: options.assignedAgent,
      sessionId: options.sessionId,
      metadata: options.metadata,
    });

    // 2. Transition to working
    this.orchestrator.startWork(task.id);

    // 3. Build and publish the MCPContext
    const context: MCPContext = {
      id: uuidv4(),
      version: '0.1.0',
      timestamp: new Date().toISOString(),
      source: this.config.source,
      contentType: this.config.contentType,
      payload: {
        taskId: task.id,
        message: options.message as unknown as Record<string, unknown>,
      },
      taskId: task.id,
      sessionId: task.sessionId,
      priority: 5,
    };

    await this.broker.publish(context);

    return {
      taskId: task.id,
      contextId: context.id,
      task: this.orchestrator.get(task.id)!,
      context,
    };
  }

  /**
   * Handle an inbound MCP reply and route it back to the originating A2A task.
   * If the reply carries a taskId, the task is completed with the reply payload as an artifact.
   */
  private async onMCPReply(ctx: MCPContext): Promise<void> {
    const taskId = ctx.taskId;
    if (!taskId) return;

    const task = this.orchestrator.get(taskId);
    if (!task || TERMINAL_STATES.has(task.status.state)) return;

    const artifact = {
      id: uuidv4(),
      name: 'mcp-reply',
      parts: [
        {
          type: 'data' as const,
          data: {
            contextId: ctx.id,
            contentType: ctx.contentType,
            payload: ctx.payload as Record<string, unknown>,
          },
        },
      ],
      metadata: {
        mcpContextId: ctx.id,
        mcpContentType: ctx.contentType,
      },
    };

    this.orchestrator.complete(taskId, [artifact]);
  }
}
