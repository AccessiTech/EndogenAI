/**
 * @accessitech/mcp — EndogenAI MCP Infrastructure
 *
 * Public API surface:
 * - Types: MCPContext, ModuleRef, Capability, ModuleState, etc.
 * - validate: validateMCPContext, isMCPContext
 * - CapabilityRegistry
 * - StateSynchronizer
 * - ContextBroker
 * - createMCPServer
 */

export * from './types.js';
export * from './validate.js';
export { CapabilityRegistry } from './registry.js';
export { StateSynchronizer } from './sync.js';
export { ContextBroker } from './broker.js';
export { createMCPServer, sendResourceNotification } from './server.js';
export type { MCPServerConfig, MCPServerInstance } from './server.js';
export {
  buildProtectedResourceMetadata,
  handleWellKnownRequest,
} from './well-known.js';
export type { ProtectedResourceMetadata } from './well-known.js';
export {
  parseTraceparent,
  createRootTraceparent,
  createChildTraceparent,
  extractOrCreateTraceContext,
  childTraceContext,
} from './tracing.js';
