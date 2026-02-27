/**
 * @accessitech/a2a — EndogenAI A2A Infrastructure
 *
 * Public API surface:
 * - Types: A2AMessage, A2ATask, AgentCard, Part, etc.
 * - validate: validateA2AMessage, validateA2ATask, isA2AMessage, isA2ATask
 * - TaskOrchestrator
 * - A2ARequestHandler
 * - createA2AServer
 */

export * from './types.js';
export * from './validate.js';
export { TaskOrchestrator } from './orchestrator.js';
export { A2ARequestHandler, A2A_ERROR_CODES } from './handler.js';
export { createA2AServer } from './server.js';
export type { A2AServerConfig, A2AServerInstance } from './server.js';
