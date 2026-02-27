/**
 * TypeScript types derived from shared/schemas/mcp-context.schema.json
 *
 * These are the canonical EndogenAI Module Context Protocol (MCP) types.
 * All module-to-module communication uses MCPContext envelopes.
 */

/** Reference to a specific EndogenAI module. */
export interface ModuleRef {
  /** Canonical module identifier (e.g. 'sensory-input', 'working-memory'). */
  moduleId: string;
  /** Architectural layer the module belongs to. */
  layer: string;
}

/** W3C Trace Context for distributed tracing. */
export interface TraceContext {
  /** W3C traceparent header value. */
  traceparent: string;
  /** Optional W3C tracestate for vendor-specific metadata. */
  tracestate?: string;
}

/** Valid payload types for an MCPContext. */
export type MCPPayload =
  | Record<string, unknown>
  | string
  | unknown[]
  | number
  | boolean
  | null;

/** MCP context envelope — canonical message format for all module-to-module communication. */
export interface MCPContext {
  /** UUID v4 */
  id: string;
  /** Schema version in use (e.g. "0.1.0") */
  version: string;
  /** ISO 8601 UTC timestamp */
  timestamp: string;
  /** Originating module */
  source: ModuleRef;
  /** Optional target module (omit for broadcast) */
  destination?: ModuleRef;
  /** W3C trace context for distributed tracing */
  traceContext?: TraceContext;
  /** MIME-like descriptor for payload format */
  contentType: string;
  /** Message content */
  payload: MCPPayload;
  /** UUID linking this to a parent context */
  correlationId?: string;
  /** Cognitive session scope */
  sessionId?: string;
  /** Associated A2A task ID */
  taskId?: string;
  /** Routing priority 0–10, default 5 */
  priority?: number;
  /** Arbitrary string annotations */
  metadata?: Record<string, string>;
}

/** Describes a module's capabilities for the registry. */
export interface Capability {
  moduleId: string;
  layer: string;
  /** Content types this module accepts */
  accepts: string[];
  /** Content types this module emits */
  emits: string[];
  version: string;
  /** Optional HTTP endpoint URL */
  url?: string;
  /** ISO 8601 timestamp of last registration */
  registeredAt?: string;
}

/** Module sync state */
export type SyncState = 'idle' | 'syncing' | 'error';

/** Tracks the runtime state of a registered module. */
export interface ModuleState {
  moduleId: string;
  layer: string;
  state: SyncState;
  /** ISO 8601 timestamp of last heartbeat */
  lastSeen: string;
  metadata?: Record<string, string>;
}

/** Handler function type for MCPContext messages */
export type MCPContextHandler = (context: MCPContext) => Promise<void>;
