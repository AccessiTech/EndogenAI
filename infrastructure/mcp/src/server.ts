/**
 * MCP Server for the EndogenAI infrastructure.
 *
 * Uses @modelcontextprotocol/sdk to expose the capability registry and context
 * broker as MCP tools and resources. All cognitive modules connect to this server
 * to register capabilities, publish MCPContext messages, and query the registry.
 *
 * Tools provided:
 *   - register_capability   — register a module's capabilities
 *   - deregister_capability — remove a module from the registry
 *   - publish_context       — publish an MCPContext message
 *   - list_states           — query all module sync states
 *
 * Resources provided:
 *   - mcp://capabilities/{moduleId} — read a module's capability entry
 */

import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import {
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { CapabilityRegistry } from './registry.js';
import { ContextBroker } from './broker.js';
import { StateSynchronizer } from './sync.js';
import type { Capability } from './types.js';

// ---------------------------------------------------------------------------
// brain:// URI Registry — loaded once at import time
// ---------------------------------------------------------------------------

interface BrainResource {
  uri: string;
  module: string;
  group: string;
  type: string;
  mimeType: string;
  description: string;
  accessControl: string[];
  parameters?: Array<{ name: string; type: string; description: string }>;
}

function loadBrainResources(): BrainResource[] {
  try {
    // Resolve relative to this source file: src/ → mcp/ → infrastructure/ → workspace root
    const __dirname = dirname(fileURLToPath(import.meta.url));
    const registryPath = join(__dirname, '..', '..', '..', 'resources', 'uri-registry.json');
    const raw = readFileSync(registryPath, 'utf-8');
    const parsed = JSON.parse(raw) as { resources: BrainResource[] };
    return parsed.resources ?? [];
  } catch {
    // Registry file not present — return empty list gracefully
    return [];
  }
}

const BRAIN_RESOURCES: BrainResource[] = loadBrainResources();

export interface MCPServerConfig {
  name?: string;
  version?: string;
}

export interface MCPServerInstance {
  server: Server;
  registry: CapabilityRegistry;
  broker: ContextBroker;
  sync: StateSynchronizer;
}

/**
 * Creates and configures the EndogenAI MCP server.
 * Returns the server instance with registry, broker, and sync attached.
 */
export function createMCPServer(config: MCPServerConfig = {}): MCPServerInstance {
  const registry = new CapabilityRegistry();
  const sync = new StateSynchronizer();
  const broker = new ContextBroker(registry, sync);

  const server = new Server(
    {
      name: config.name ?? 'endogenai-mcp',
      version: config.version ?? '0.1.0',
    },
    {
      capabilities: {
        resources: {},
        tools: {},
      },
    },
  );

  // ── Tools (discovery) ──────────────────────────────────────────────────────

  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
      tools: [
        {
          name: 'register_capability',
          description: "Register a module's capabilities with the MCP capability registry.",
          inputSchema: {
            type: 'object' as const,
            required: ['moduleId', 'layer', 'accepts', 'emits', 'version'],
            properties: {
              moduleId: { type: 'string' },
              layer: { type: 'string' },
              accepts: { type: 'array', items: { type: 'string' } },
              emits: { type: 'array', items: { type: 'string' } },
              version: { type: 'string' },
              url: { type: 'string' },
            },
          },
        },
        {
          name: 'deregister_capability',
          description: 'Remove a module from the capability registry.',
          inputSchema: {
            type: 'object' as const,
            required: ['moduleId'],
            properties: { moduleId: { type: 'string' } },
          },
        },
        {
          name: 'publish_context',
          description: 'Publish an MCPContext message through the context broker.',
          inputSchema: {
            type: 'object' as const,
            description: 'A valid MCPContext envelope (see mcp-context.schema.json).',
          },
        },
        {
          name: 'list_states',
          description: 'List the current synchronisation state of all registered modules.',
          inputSchema: { type: 'object' as const, properties: {} },
        },
      ],
    };
  });

  // ── Resources ──────────────────────────────────────────────────────────────

  server.setRequestHandler(ListResourcesRequestSchema, async (request) => {
    const params = request.params as { group?: string; module?: string } | undefined;
    const groupFilter = params?.group;
    const moduleFilter = params?.module;

    // mcp://capabilities/* — always returned (no group/module filter applies)
    const capabilities = registry.list();
    const capResources = capabilities.map((cap) => ({
      uri: `mcp://capabilities/${cap.moduleId}`,
      name: `${cap.moduleId} capability`,
      description: [
        `Layer: ${cap.layer}`,
        `Accepts: ${cap.accepts.join(', ')}`,
        `Emits: ${cap.emits.join(', ')}`,
      ].join(' | '),
      mimeType: 'application/json',
    }));

    // brain:// resources — optional group / module filtering
    let brainResources = BRAIN_RESOURCES;
    if (groupFilter) {
      brainResources = brainResources.filter((r) => r.group === groupFilter);
    }
    if (moduleFilter) {
      brainResources = brainResources.filter((r) => r.module === moduleFilter);
    }

    return {
      resources: [
        ...capResources,
        ...brainResources.map((r) => ({
          uri: r.uri,
          name: `${r.module} — ${r.uri.split('/').pop()}`,
          description: r.description,
          mimeType: r.mimeType,
        })),
      ],
    };
  });

  server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
    const uri = request.params.uri;

    // brain:// resources — return stub content (live data from running modules)
    // TODO(Phase 9): live SSE subscription emission via resources/subscribe is deferred.
    // Currently returns a static stub; real-time push requires the module to be running
    // and the MCP server to support resources/subscribe notification dispatch.
    if (uri.startsWith('brain://')) {
      const entry = BRAIN_RESOURCES.find((r) => r.uri === uri);
      if (!entry) {
        throw new Error(`Unknown brain:// resource: ${uri}`);
      }
      return {
        contents: [
          {
            uri,
            mimeType: 'application/json',
            text: JSON.stringify({
              status: 'stub',
              message: 'Live data available when module is running',
              resource: entry.uri,
              module: entry.module,
              group: entry.group,
            }),
          },
        ],
      };
    }

    // mcp://capabilities/* — existing handler
    const moduleId = uri.replace('mcp://capabilities/', '');
    const cap = registry.get(moduleId);
    if (!cap) {
      throw new Error(`Capability not found for module: ${moduleId}`);
    }
    return {
      contents: [
        {
          uri,
          mimeType: 'application/json',
          text: JSON.stringify(cap, null, 2),
        },
      ],
    };
  });

  // ── Tools ───────────────────────────────────────────────────────────────────

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    switch (name) {
      case 'register_capability': {
        const cap = args as unknown as Capability;
        registry.register(cap);
        sync.heartbeat(cap.moduleId, cap.layer);
        return {
          content: [
            { type: 'text', text: `Registered capability for module: ${cap.moduleId}` },
          ],
        };
      }

      case 'deregister_capability': {
        const { moduleId } = args as { moduleId: string };
        const removed = registry.deregister(moduleId);
        sync.remove(moduleId);
        return {
          content: [
            {
              type: 'text',
              text: removed
                ? `Deregistered module: ${moduleId}`
                : `Module not found: ${moduleId}`,
            },
          ],
        };
      }

      case 'publish_context': {
        await broker.publish(args);
        return {
          content: [{ type: 'text', text: 'Context published successfully.' }],
        };
      }

      case 'list_states': {
        const states = sync.listStates();
        return {
          content: [{ type: 'text', text: JSON.stringify(states, null, 2) }],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  });

  return { server, registry, broker, sync };
}
