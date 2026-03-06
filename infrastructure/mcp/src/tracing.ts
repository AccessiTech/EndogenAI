/**
 * W3C Trace Context utilities for MCPContext envelope propagation.
 * See shared/utils/tracing.md for the full spec.
 */

import type { TraceContext } from './types.js';

/** Pattern from shared/schemas/mcp-context.schema.json */
const TRACEPARENT_RE = /^00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$/;

/** Generate a cryptographically random hex string of the given byte length. */
function randomHex(bytes: number): string {
  const arr = new Uint8Array(bytes);
  crypto.getRandomValues(arr);
  return Array.from(arr, (b) => b.toString(16).padStart(2, '0')).join('');
}

/** Parse a traceparent string, returning null if invalid. */
export function parseTraceparent(raw: string | null | undefined): string | null {
  if (!raw || !TRACEPARENT_RE.test(raw)) return null;
  return raw;
}

/** Create a new root traceparent (new traceId + root spanId, sampled). */
export function createRootTraceparent(): string {
  return `00-${randomHex(16)}-${randomHex(8)}-01`;
}

/**
 * Derive a child traceparent from a parent — same traceId, new spanId.
 * If parent is absent or invalid, returns a new root traceparent.
 */
export function createChildTraceparent(parent: string | null | undefined): string {
  if (!parent || !TRACEPARENT_RE.test(parent)) return createRootTraceparent();
  const parts = parent.split('-');
  const traceId = parts[1];
  const flags = parts[3];
  const spanId = randomHex(8);
  return `00-${traceId}-${spanId}-${flags}`;
}

/**
 * Extract a TraceContext from HTTP request headers, or generate a fresh one.
 * Call at the MCP server boundary for every incoming HTTP request.
 */
export function extractOrCreateTraceContext(
  headers: Record<string, string | string[] | undefined>
): TraceContext {
  const raw = Array.isArray(headers['traceparent'])
    ? headers['traceparent'][0]
    : headers['traceparent'];
  const traceparent = parseTraceparent(raw) ?? createRootTraceparent();
  const tracestate = Array.isArray(headers['tracestate'])
    ? headers['tracestate'][0]
    : headers['tracestate'];
  return tracestate ? { traceparent, tracestate } : { traceparent };
}

/**
 * Build a child TraceContext from a parent envelope's traceContext.
 * Use when the MCP broker constructs outbound messages.
 */
export function childTraceContext(parent: TraceContext | undefined): TraceContext {
  return { traceparent: createChildTraceparent(parent?.traceparent) };
}
