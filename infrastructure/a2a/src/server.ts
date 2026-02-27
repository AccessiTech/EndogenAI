/**
 * A2A HTTP Server for the EndogenAI infrastructure.
 *
 * Exposes two endpoints:
 *   GET  /.well-known/agent-card.json  — agent identity and capabilities
 *   POST /                             — JSON-RPC 2.0 A2A task methods
 *
 * Aligned with A2A specification v0.3.0
 * https://github.com/a2aproject/A2A/releases/tag/v0.3.0
 * Spec commit: 2d3dc909972d9680b974e0fc9a1354c1ba8f519d
 */

import { createServer, type IncomingMessage, type ServerResponse } from 'node:http';
import { TaskOrchestrator } from './orchestrator.js';
import { A2ARequestHandler } from './handler.js';
import type { AgentCard } from './types.js';

export interface A2AServerConfig {
  port?: number;
  agentCard: AgentCard;
}

export interface A2AServerInstance {
  orchestrator: TaskOrchestrator;
  handler: A2ARequestHandler;
  agentCard: AgentCard;
  /** Start listening. Returns the bound port. */
  listen(port?: number): Promise<number>;
  /** Stop the server. */
  close(): Promise<void>;
}

/**
 * Creates and configures the EndogenAI A2A server.
 */
export function createA2AServer(config: A2AServerConfig): A2AServerInstance {
  const orchestrator = new TaskOrchestrator();
  const handler = new A2ARequestHandler(orchestrator);
  const { agentCard } = config;

  const httpServer = createServer(async (req: IncomingMessage, res: ServerResponse) => {
    // CORS preflight
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
      res.writeHead(204);
      res.end();
      return;
    }

    // Agent card endpoint
    if (req.method === 'GET' && req.url === '/.well-known/agent-card.json') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(agentCard, null, 2));
      return;
    }

    // JSON-RPC A2A endpoint
    if (req.method === 'POST' && req.url === '/') {
      let body = '';
      req.on('data', (chunk: Buffer) => {
        body += chunk.toString();
      });
      req.on('end', async () => {
        let parsed: unknown;
        try {
          parsed = JSON.parse(body);
        } catch {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(
            JSON.stringify({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'Parse error' } }),
          );
          return;
        }

        const response = await handler.handle(parsed);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(response));
      });
      return;
    }

    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not found' }));
  });

  return {
    orchestrator,
    handler,
    agentCard,
    listen(port?: number): Promise<number> {
      return new Promise((resolve, reject) => {
        const p = port ?? config.port ?? 0;
        httpServer.listen(p, () => {
          const addr = httpServer.address();
          const boundPort = addr && typeof addr === 'object' ? addr.port : p;
          resolve(boundPort);
        });
        httpServer.once('error', reject);
      });
    },
    close(): Promise<void> {
      return new Promise((resolve, reject) => {
        httpServer.close((err) => (err ? reject(err) : resolve()));
      });
    },
  };
}
