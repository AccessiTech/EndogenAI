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
export { createMCPServer } from './server.js';
export type { MCPServerConfig, MCPServerInstance } from './server.js';
