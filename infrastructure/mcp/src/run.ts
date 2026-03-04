/**
 * Standalone HTTP entry point for the EndogenAI MCP server.
 *
 * Binds `createMCPServer()` to the MCP Streamable HTTP 2025-06-18 transport
 * and listens on PORT (default 8080).
 *
 * Usage:
 *   pnpm dev          # tsx watch src/run.ts
 *   pnpm start        # node dist/run.js
 */

import { createServer } from 'node:http';
import { randomUUID } from 'node:crypto';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { createMCPServer } from './server.js';

const port = Number(process.env.MCP_PORT ?? 8080);

const { server } = createMCPServer();

const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: () => randomUUID(),
});

await server.connect(transport);

const httpServer = createServer(async (req, res) => {
  // Health check — unauthenticated, no MCP involvement
  if (req.method === 'GET' && req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', service: 'endogenai-mcp' }));
    return;
  }

  await transport.handleRequest(req, res);
});

httpServer.listen(port, () => {
  console.log(`MCP server listening on http://localhost:${port}`);
});
