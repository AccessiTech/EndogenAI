/**
 * Context Broker for the EndogenAI MCP infrastructure.
 * Routes MCPContext messages to registered handlers, enforcing validation
 * and trace propagation rules defined in docs/protocols/mcp.md.
 */

import { v4 as uuidv4 } from 'uuid';
import { validateMCPContext } from './validate.js';
import { CapabilityRegistry } from './registry.js';
import { StateSynchronizer } from './sync.js';
import type { MCPContext, MCPContextHandler } from './types.js';

export class ContextBroker {
  private handlers = new Map<string, MCPContextHandler[]>();
  private broadcastHandlers: MCPContextHandler[] = [];

  constructor(
    public readonly registry: CapabilityRegistry,
    public readonly sync: StateSynchronizer,
  ) {}

  /**
   * Subscribe a handler to directed messages for a specific module ID.
   * Used when context has an explicit destination.moduleId.
   */
  subscribe(moduleId: string, handler: MCPContextHandler): void {
    const existing = this.handlers.get(moduleId) ?? [];
    this.handlers.set(moduleId, [...existing, handler]);
  }

  /** Subscribe to all broadcast messages (no destination). */
  subscribeBroadcast(handler: MCPContextHandler): void {
    this.broadcastHandlers.push(handler);
  }

  /** Unsubscribe all handlers for a module. */
  unsubscribe(moduleId: string): void {
    this.handlers.delete(moduleId);
  }

  /**
   * Publish an MCPContext message.
   * Validates the envelope, updates source module state, and routes to subscribers.
   */
  async publish(raw: unknown): Promise<void> {
    const context = validateMCPContext(raw);

    // Record heartbeat for the source module
    this.sync.heartbeat(context.source.moduleId, context.source.layer);

    const destination = context.destination?.moduleId;

    if (destination) {
      // Directed message — send to registered handlers for that module
      const destHandlers = this.handlers.get(destination) ?? [];
      await Promise.all(destHandlers.map((h) => h(context)));
    } else {
      // Broadcast — deliver to all broadcast subscribers
      await Promise.all(this.broadcastHandlers.map((h) => h(context)));

      // Also route to capability-matched modules
      const matched = this.registry.findByAcceptedContentType(context.contentType);
      for (const cap of matched) {
        const capHandlers = this.handlers.get(cap.moduleId) ?? [];
        await Promise.all(capHandlers.map((h) => h(context)));
      }
    }
  }

  /**
   * Build a reply MCPContext from a received one.
   * Preserves correlationId, traceContext, sessionId, and taskId per the MCP spec.
   */
  buildReply(
    original: MCPContext,
    source: { moduleId: string; layer: string },
    contentType: string,
    payload: MCPContext['payload'],
  ): MCPContext {
    return {
      id: uuidv4(),
      version: original.version,
      timestamp: new Date().toISOString(),
      source,
      destination: original.source,
      traceContext: original.traceContext,
      contentType,
      payload,
      correlationId: original.id,
      sessionId: original.sessionId,
      taskId: original.taskId,
      priority: original.priority ?? 5,
    };
  }
}
