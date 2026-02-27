/**
 * State synchronisation primitives for the EndogenAI MCP infrastructure.
 * Tracks the runtime state of all registered modules.
 */

import type { ModuleState, SyncState } from './types.js';

export class StateSynchronizer {
  private states = new Map<string, ModuleState>();

  /** Upsert the state for a module. */
  setState(
    moduleId: string,
    layer: string,
    state: SyncState,
    metadata?: Record<string, string>,
  ): void {
    this.states.set(moduleId, {
      moduleId,
      layer,
      state,
      lastSeen: new Date().toISOString(),
      metadata,
    });
  }

  /** Record a heartbeat (sets state to 'idle', updates lastSeen). */
  heartbeat(moduleId: string, layer: string): void {
    const existing = this.states.get(moduleId);
    this.states.set(moduleId, {
      moduleId,
      layer,
      state: 'idle',
      lastSeen: new Date().toISOString(),
      metadata: existing?.metadata,
    });
  }

  /** Get the current state of a module. */
  getState(moduleId: string): ModuleState | undefined {
    return this.states.get(moduleId);
  }

  /** Returns all module states. */
  listStates(): ModuleState[] {
    return Array.from(this.states.values());
  }

  /** Returns modules that haven't sent a heartbeat within the given TTL (ms). */
  stale(ttlMs: number): ModuleState[] {
    const cutoff = Date.now() - ttlMs;
    return Array.from(this.states.values()).filter(
      (s) => new Date(s.lastSeen).getTime() < cutoff,
    );
  }

  /** Remove a module from state tracking. */
  remove(moduleId: string): boolean {
    return this.states.delete(moduleId);
  }

  /** Clear all state (for testing). */
  clear(): void {
    this.states.clear();
  }
}
