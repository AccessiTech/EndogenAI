/**
 * TypeScript types derived from:
 *   - shared/schemas/a2a-message.schema.json
 *   - shared/schemas/a2a-task.schema.json
 *
 * Aligned with A2A Project specification v0.3.0
 * https://github.com/a2aproject/A2A/releases/tag/v0.3.0
 * Spec commit: 2d3dc909972d9680b974e0fc9a1354c1ba8f519d
 */

/** Reference to a specific agent instance. */
export interface AgentRef {
  /** Canonical agent/module identifier. */
  id: string;
  /** Human-readable display name. */
  name?: string;
  /** Base URL for the agent's A2A endpoint. */
  url?: string;
}

/** W3C Trace Context */
export interface TraceContext {
  traceparent: string;
  tracestate?: string;
}

// ── Message Part types ──────────────────────────────────────────────────────────────────

export interface TextPart {
  type: 'text';
  text: string;
  mimeType?: string;
}

export interface DataPart {
  type: 'data';
  data: Record<string, unknown>;
  schema?: Record<string, unknown>;
}

export interface FilePart {
  type: 'file';
  file: {
    mimeType: string;
    uri?: string;
    bytes?: string; // base64
    name?: string;
  };
}

export interface FunctionCallPart {
  type: 'function_call';
  functionCall: {
    id: string;
    name: string;
    args: Record<string, unknown>;
  };
}

export interface FunctionResultPart {
  type: 'function_result';
  functionResult: {
    id: string;
    name: string;
    response: unknown;
  };
}

export type Part =
  | TextPart
  | DataPart
  | FilePart
  | FunctionCallPart
  | FunctionResultPart;

// ── A2AMessage ────────────────────────────────────────────────────────────────────────

/** A2A message envelope. */
export interface A2AMessage {
  /** UUID v4 */
  id: string;
  /** Message origin role */
  role: 'user' | 'agent' | 'system';
  /** Ordered content parts */
  parts: Part[];
  /** ISO 8601 UTC timestamp */
  timestamp: string;
  /** Associated task ID */
  taskId?: string;
  /** Sending agent */
  sender?: AgentRef;
  /** Target agent */
  recipient?: AgentRef;
  /** W3C trace context */
  traceContext?: { traceparent: string; tracestate?: string };
  /** Arbitrary annotations */
  metadata?: Record<string, string>;
}

// ── A2ATask ───────────────────────────────────────────────────────────────────────────

/** Task lifecycle states */
export type TaskState =
  | 'submitted'
  | 'working'
  | 'input-required'
  | 'completed'
  | 'failed'
  | 'canceled';

/** Terminal task states */
export const TERMINAL_STATES: ReadonlySet<TaskState> = new Set([
  'completed',
  'failed',
  'canceled',
]);

export interface TaskStatus {
  state: TaskState;
  /** Optional contextual message for the current state */
  message?: string | A2AMessage;
}

export interface TaskError {
  code: string;
  message: string;
  retryable: boolean;
  details?: Record<string, unknown>;
}

export interface Artifact {
  id: string;
  name: string;
  parts: Part[];
  metadata?: Record<string, string>;
}

export interface InputRequest {
  message: string;
  inputSchema?: Record<string, unknown>;
}

/** A2A task — top-level unit of agent work. */
export interface A2ATask {
  /** UUID v4 */
  id: string;
  /** Cognitive session scope */
  sessionId?: string;
  /** Current lifecycle state */
  status: TaskStatus;
  /** ISO 8601 UTC creation timestamp */
  createdAt: string;
  /** ISO 8601 UTC last-updated timestamp */
  updatedAt: string;
  /** Agent currently executing the task */
  assignedAgent?: AgentRef;
  /** Agent or user who submitted the task */
  requester?: AgentRef;
  /** Ordered message history */
  history: A2AMessage[];
  /** Output artifacts (populated on completion) */
  artifacts: Artifact[];
  /** Error details (populated on failure) */
  error?: TaskError;
  /** Input request details (populated when input-required) */
  inputRequest?: InputRequest;
  /** W3C trace context */
  traceContext?: TraceContext;
  /** Arbitrary annotations */
  metadata?: Record<string, string>;
}

// ── Agent card ─────────────────────────────────────────────────────────────────────────

export interface AgentSkill {
  id: string;
  name: string;
  description?: string;
}

export interface AgentMCPCapabilities {
  accepts: string[];
  emits: string[];
  version: string;
}

/** Agent card served at /.well-known/agent-card.json */
export interface AgentCard {
  id: string;
  name: string;
  version: string;
  description?: string;
  url?: string;
  skills: AgentSkill[];
  mcp?: AgentMCPCapabilities;
}

// ── JSON-RPC transport ───────────────────────────────────────────────────────────────────

export interface A2ARequest {
  jsonrpc: '2.0';
  id: string | number;
  method: string;
  params?: Record<string, unknown>;
}

export interface A2AResponse<T = unknown> {
  jsonrpc: '2.0';
  id: string | number | null;
  result?: T;
  error?: { code: number; message: string; data?: unknown };
}
