/**
 * Schema validation for A2AMessage and A2ATask.
 * Compiles the canonical shared/schemas/ files — single source of truth.
 * a2a-task.schema.json references a2a-message.schema.json via $ref so both
 * schemas are registered with Ajv before compilation.
 */

import Ajv from 'ajv';
import addFormats from 'ajv-formats';
import type { A2AMessage, A2ATask } from './types.js';
import a2aMessageSchema from '../../../shared/schemas/a2a-message.schema.json';
import a2aTaskSchema from '../../../shared/schemas/a2a-task.schema.json';

const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);

// Register a2a-message schema so the $ref inside a2a-task.schema.json resolves.
ajv.addSchema(a2aMessageSchema as object, 'a2a-message.schema.json');

const validateMessageFn = ajv.compile(a2aMessageSchema as object);
const validateTaskFn = ajv.compile(a2aTaskSchema as object);

/** Validates an unknown value as an A2AMessage. Throws on failure. */
export function validateA2AMessage(value: unknown): A2AMessage {
  if (!validateMessageFn(value)) {
    throw new Error(`Invalid A2AMessage: ${ajv.errorsText(validateMessageFn.errors)}`);
  }
  return value as unknown as A2AMessage;
}

/** Validates an unknown value as an A2ATask. Throws on failure. */
export function validateA2ATask(value: unknown): A2ATask {
  if (!validateTaskFn(value)) {
    throw new Error(`Invalid A2ATask: ${ajv.errorsText(validateTaskFn.errors)}`);
  }
  return value as unknown as A2ATask;
}

/** Type guard for A2AMessage. */
export function isA2AMessage(value: unknown): value is A2AMessage {
  return validateMessageFn(value) === true;
}

/** Type guard for A2ATask. */
export function isA2ATask(value: unknown): value is A2ATask {
  return validateTaskFn(value) === true;
}
