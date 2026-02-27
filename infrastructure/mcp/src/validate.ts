/**
 * JSON Schema validation for MCPContext envelopes.
 * Uses Ajv to validate against the canonical mcp-context.schema.json fields.
 */

import Ajv from 'ajv';
import addFormats from 'ajv-formats';
import type { MCPContext } from './types.js';

const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);

/** Schema inline-derived from shared/schemas/mcp-context.schema.json */
const mcpContextSchema = {
  $schema: 'http://json-schema.org/draft-07/schema#',
  type: 'object',
  required: ['id', 'version', 'timestamp', 'source', 'payload', 'contentType'],
  properties: {
    id: { type: 'string', format: 'uuid' },
    version: { type: 'string', pattern: '^\\d+\\.\\d+\\.\\d+$' },
    timestamp: { type: 'string', format: 'date-time' },
    source: {
      type: 'object',
      required: ['moduleId', 'layer'],
      properties: {
        moduleId: { type: 'string' },
        layer: { type: 'string' },
      },
    },
    destination: {
      type: 'object',
      required: ['moduleId', 'layer'],
      properties: {
        moduleId: { type: 'string' },
        layer: { type: 'string' },
      },
    },
    contentType: { type: 'string' },
    payload: {},
    correlationId: { type: 'string', format: 'uuid' },
    sessionId: { type: 'string' },
    taskId: { type: 'string' },
    priority: { type: 'integer', minimum: 0, maximum: 10 },
    metadata: {
      type: 'object',
      additionalProperties: { type: 'string' },
    },
    traceContext: {
      type: 'object',
      required: ['traceparent'],
      properties: {
        traceparent: { type: 'string' },
        tracestate: { type: 'string' },
      },
    },
  },
} as const;

const validateFn = ajv.compile(mcpContextSchema);

/**
 * Validates an unknown value as an MCPContext envelope.
 * Throws a detailed error if validation fails.
 */
export function validateMCPContext(value: unknown): MCPContext {
  const valid = validateFn(value);
  if (!valid) {
    const errors = ajv.errorsText(validateFn.errors);
    throw new Error(`Invalid MCPContext: ${errors}`);
  }
  return value as MCPContext;
}

/**
 * Type-guard returning true if value is a valid MCPContext.
 */
export function isMCPContext(value: unknown): value is MCPContext {
  return validateFn(value) === true;
}
