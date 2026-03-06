/**
 * Unit tests for W3C Trace Context utilities (src/tracing.ts).
 */

import { describe, it, expect } from 'vitest';
import {
  parseTraceparent,
  createRootTraceparent,
  createChildTraceparent,
  extractOrCreateTraceContext,
  childTraceContext,
} from '../src/tracing.js';

const VALID_TRACEPARENT = '00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01';
const TRACEPARENT_RE = /^00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$/;

describe('parseTraceparent', () => {
  it('returns a valid traceparent unchanged', () => {
    expect(parseTraceparent(VALID_TRACEPARENT)).toBe(VALID_TRACEPARENT);
  });

  it('returns null for null input', () => {
    expect(parseTraceparent(null)).toBeNull();
  });

  it('returns null for undefined input', () => {
    expect(parseTraceparent(undefined)).toBeNull();
  });

  it('returns null for an invalid traceparent', () => {
    expect(parseTraceparent('not-a-traceparent')).toBeNull();
  });

  it('returns null for a traceparent with wrong version byte', () => {
    expect(parseTraceparent('01-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01')).toBeNull();
  });
});

describe('createRootTraceparent', () => {
  it('generates a valid traceparent', () => {
    expect(createRootTraceparent()).toMatch(TRACEPARENT_RE);
  });

  it('generates unique values each call', () => {
    const a = createRootTraceparent();
    const b = createRootTraceparent();
    expect(a).not.toBe(b);
  });

  it('always has flags 01 (sampled)', () => {
    expect(createRootTraceparent().endsWith('-01')).toBe(true);
  });
});

describe('createChildTraceparent', () => {
  it('produces a valid traceparent from a valid parent', () => {
    const child = createChildTraceparent(VALID_TRACEPARENT);
    expect(child).toMatch(TRACEPARENT_RE);
  });

  it('inherits the parent traceId', () => {
    const child = createChildTraceparent(VALID_TRACEPARENT);
    const parentTraceId = VALID_TRACEPARENT.split('-')[1];
    const childTraceId = child.split('-')[1];
    expect(childTraceId).toBe(parentTraceId);
  });

  it('generates a new spanId (different from parent)', () => {
    const child = createChildTraceparent(VALID_TRACEPARENT);
    const parentSpanId = VALID_TRACEPARENT.split('-')[2];
    const childSpanId = child.split('-')[2];
    expect(childSpanId).not.toBe(parentSpanId);
  });

  it('falls back to a new root traceparent when parent is null', () => {
    const result = createChildTraceparent(null);
    expect(result).toMatch(TRACEPARENT_RE);
  });

  it('falls back to a new root traceparent when parent is invalid', () => {
    const result = createChildTraceparent('invalid');
    expect(result).toMatch(TRACEPARENT_RE);
  });
});

describe('extractOrCreateTraceContext', () => {
  it('extracts a valid traceparent from headers', () => {
    const ctx = extractOrCreateTraceContext({ traceparent: VALID_TRACEPARENT });
    expect(ctx.traceparent).toBe(VALID_TRACEPARENT);
  });

  it('generates a fresh traceparent when header is absent', () => {
    const ctx = extractOrCreateTraceContext({});
    expect(ctx.traceparent).toMatch(TRACEPARENT_RE);
  });

  it('generates a fresh traceparent when header is invalid', () => {
    const ctx = extractOrCreateTraceContext({ traceparent: 'bad' });
    expect(ctx.traceparent).toMatch(TRACEPARENT_RE);
  });

  it('includes tracestate when present', () => {
    const ctx = extractOrCreateTraceContext({
      traceparent: VALID_TRACEPARENT,
      tracestate: 'vendor=abc',
    });
    expect(ctx.tracestate).toBe('vendor=abc');
  });

  it('omits tracestate when absent', () => {
    const ctx = extractOrCreateTraceContext({ traceparent: VALID_TRACEPARENT });
    expect(ctx.tracestate).toBeUndefined();
  });

  it('handles array-valued traceparent header (takes first element)', () => {
    const ctx = extractOrCreateTraceContext({ traceparent: [VALID_TRACEPARENT, 'other'] });
    expect(ctx.traceparent).toBe(VALID_TRACEPARENT);
  });
});

describe('childTraceContext', () => {
  it('returns a TraceContext with a valid traceparent', () => {
    const parent = { traceparent: VALID_TRACEPARENT };
    const child = childTraceContext(parent);
    expect(child.traceparent).toMatch(TRACEPARENT_RE);
  });

  it('child inherits parent traceId', () => {
    const parent = { traceparent: VALID_TRACEPARENT };
    const child = childTraceContext(parent);
    expect(child.traceparent.split('-')[1]).toBe(VALID_TRACEPARENT.split('-')[1]);
  });

  it('handles undefined parent gracefully', () => {
    const child = childTraceContext(undefined);
    expect(child.traceparent).toMatch(TRACEPARENT_RE);
  });
});
