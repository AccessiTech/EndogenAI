/**
 * Capability Registry for the EndogenAI MCP infrastructure.
 * Modules register their capabilities here so the context broker can route messages.
 */

import type { Capability } from './types.js';

export class CapabilityRegistry {
  private capabilities = new Map<string, Capability>();

  /** Register or update a module's capabilities. */
  register(capability: Capability): void {
    const entry: Capability = {
      ...capability,
      registeredAt: new Date().toISOString(),
    };
    this.capabilities.set(capability.moduleId, entry);
  }

  /** Deregister a module by ID. Returns true if removed. */
  deregister(moduleId: string): boolean {
    return this.capabilities.delete(moduleId);
  }

  /** Look up a module's capabilities by ID. */
  get(moduleId: string): Capability | undefined {
    return this.capabilities.get(moduleId);
  }

  /** Returns all registered modules that accept the given content type. */
  findByAcceptedContentType(contentType: string): Capability[] {
    return Array.from(this.capabilities.values()).filter((cap) =>
      cap.accepts.includes(contentType),
    );
  }

  /** Returns all registered capabilities. */
  list(): Capability[] {
    return Array.from(this.capabilities.values());
  }

  /** Returns the number of registered modules. */
  size(): number {
    return this.capabilities.size;
  }

  /** Clears all registrations (for testing). */
  clear(): void {
    this.capabilities.clear();
  }
}
