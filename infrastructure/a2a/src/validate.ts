/**
 * Schema validation for A2AMessage and A2ATask.
 * Derived from shared/schemas/a2a-message.schema.json and a2a-task.schema.json.
 */

import Ajv from 'ajv';
import addFormats from 'ajv-formats';
import type { A2AMessage, A2ATask } from './types.js';

const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);

/** Inline schema derived from shared/schemas/a2a-message.schema.json */
const a2aMessageSchema = {
  type: 'object',
  required: ['id', 'role', 'parts', 'timestamp'],
  properties: {
    id: { type: 'string', format: 'uuid' },
    role: { type: 'string', enum: ['user', 'agent', 'system'] },
    parts: { type: 'array', minItems: 1, items: { type: 'object' } },
    timestamp: { type: 'string', format: 'date-time' },
    taskId: { type: 'string' },
    sender: { type: 'object', required: ['id'], properties: { id: { type: 'string' } } },
    recipient: { type: 'object', required: ['id'], properties: { id: { type: 'string' } } },
    metadata: { type: 'object', additionalProperties: { type: 'string' } },
  },
};

/** Inline schema derived from shared/schemas/a2a-task.schema.json */
const a2aTaskSchema = {
  type: 'object',
  required: ['id', 'status', 'createdAt', 'updatedAt'],
  properties: {
    id: { type: 'string', format: 'uuid' },
    status: {
      type: 'object',
      required: ['state'],
      properties: {
        state: {
          type: 'string',
          enum: ['submitted', 'working', 'input-required', 'completed', 'failed', 'canceled'],
        },
      },
    },
    createdAt: { type: 'string', format: 'date-time' },
    updatedAt: { type: 'string', format: 'date-time' },
  },
};

const validateMessageFn = ajv.compile(a2aMessageSchema);
const validateTaskFn = ajv.compile(a2aTaskSchema);

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
