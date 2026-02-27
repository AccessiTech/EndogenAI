/**
 * JSON Schema validation for MCPContext envelopes.
 * Compiles the canonical shared/schemas/mcp-context.schema.json — single source of truth.
 */

import Ajv from 'ajv';
import addFormats from 'ajv-formats';
import type { MCPContext } from './types.js';
import mcpContextSchema from '../../../shared/schemas/mcp-context.schema.json';

const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);

const validateFn = ajv.compile(mcpContextSchema as object);

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
