/**
 * well-known.ts — HTTP handler for /.well-known/oauth-protected-resource
 *
 * Serves the OAuth 2.0 Protected Resource Metadata document as specified by
 * RFC 9728. This document tells OAuth clients which authorization servers
 * protect this resource server.
 *
 * Usage:
 *   import { createWellKnownRouter } from './well-known.js'
 *   const handler = createWellKnownRouter()
 *   // attach to a Node http.Server via server.on('request', handler)
 *
 * Environment variables:
 *   MCP_SERVER_URI     — canonical URI of this resource server (default: http://localhost:8000)
 *   AUTH_SERVER_URL    — Authorization Server base URL (default: http://localhost:3001)
 */

import type { IncomingMessage, ServerResponse } from 'node:http'

export interface ProtectedResourceMetadata {
  resource: string
  authorization_servers: string[]
  bearer_methods_supported: string[]
  resource_documentation: string
}

/**
 * Build the protected-resource metadata document from environment variables.
 */
export function buildProtectedResourceMetadata(): ProtectedResourceMetadata {
  const resource = process.env.MCP_SERVER_URI ?? 'http://localhost:8000'
  const authServer = process.env.AUTH_SERVER_URL ?? 'http://localhost:3001'
  return {
    resource,
    authorization_servers: [authServer],
    bearer_methods_supported: ['header'],
    resource_documentation: `${authServer}/docs`,
  }
}

/**
 * Node http request handler that serves /.well-known/oauth-protected-resource.
 * Returns true if the request was handled, false if it should be passed on.
 */
export function handleWellKnownRequest(
  req: IncomingMessage,
  res: ServerResponse,
): boolean {
  if (req.url === '/.well-known/oauth-protected-resource') {
    const body = JSON.stringify(buildProtectedResourceMetadata())
    res.writeHead(200, {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(body),
      'Cache-Control': 'no-store',
    })
    res.end(body)
    return true
  }
  return false
}
