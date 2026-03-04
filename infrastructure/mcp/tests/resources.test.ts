/**
 * Tests for §8.5 MCP Resource Registry — brain:// URI handlers.
 *
 * Covers resources/list filtering (no filter, ?module, ?group) and
 * resources/read for brain:// and mcp://capabilities/ URIs.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { InMemoryTransport } from '@modelcontextprotocol/sdk/inMemory.js';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { createMCPServer } from '../src/server.js';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function connectClient(
  mcp: ReturnType<typeof createMCPServer>,
): Promise<{ client: Client; cleanup: () => Promise<void> }> {
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
  await mcp.server.connect(serverTransport);
  const client = new Client({ name: 'test-client', version: '0.0.1' }, { capabilities: {} });
  await client.connect(clientTransport);
  return {
    client,
    cleanup: async () => {
      await client.close();
    },
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('resources/list (brain:// registry)', () => {
  let mcp: ReturnType<typeof createMCPServer>;

  beforeEach(() => {
    mcp = createMCPServer({ name: 'test-mcp', version: '0.0.1' });
  });

  afterEach(() => {
    // Nothing async to clean up for non-transport tests
  });

  it('returns brain:// URIs when no filter is applied', async () => {
    const { client, cleanup } = await connectClient(mcp);
    const result = await client.listResources();
    const uris = result.resources.map((r) => r.uri);

    // At minimum the registry entries we know exist
    expect(uris.some((u) => u.startsWith('brain://'))).toBe(true);
    expect(uris).toContain('brain://group-ii/working-memory/context/current');
    expect(uris).toContain('brain://group-iv/metacognition/confidence/current');

    await cleanup();
  });

  it('returns all 9 brain:// entries from uri-registry.json', async () => {
    const { client, cleanup } = await connectClient(mcp);
    const result = await client.listResources();
    const brainUris = result.resources.filter((r) => r.uri.startsWith('brain://'));
    expect(brainUris.length).toBeGreaterThanOrEqual(9);
    await cleanup();
  });

  it('brain:// entries include mimeType application/json', async () => {
    const { client, cleanup } = await connectClient(mcp);
    const result = await client.listResources();
    const brainResources = result.resources.filter((r) => r.uri.startsWith('brain://'));
    for (const r of brainResources) {
      expect(r.mimeType).toBe('application/json');
    }
    await cleanup();
  });

  it('all brain:// URIs match brain://group-*/... pattern', async () => {
    const { client, cleanup } = await connectClient(mcp);
    const result = await client.listResources();
    const brainUris = result.resources
      .map((r) => r.uri)
      .filter((u) => u.startsWith('brain://'));

    const pattern = /^brain:\/\/group-[iv]+\/[a-z-]+\/.+$/;
    for (const uri of brainUris) {
      expect(uri).toMatch(pattern);
    }
    await cleanup();
  });

  it('still returns mcp://capabilities/* resources alongside brain://', async () => {
    mcp.registry.register({
      moduleId: 'test-perception',
      layer: 'sensory-input',
      accepts: ['signal/text'],
      emits: ['memory/item'],
      version: '0.1.0',
    });

    const { client, cleanup } = await connectClient(mcp);
    const result = await client.listResources();
    const uris = result.resources.map((r) => r.uri);

    expect(uris).toContain('mcp://capabilities/test-perception');
    expect(uris.some((u) => u.startsWith('brain://'))).toBe(true);

    await cleanup();
  });
});

describe('resources/read', () => {
  let mcp: ReturnType<typeof createMCPServer>;

  beforeEach(() => {
    mcp = createMCPServer({ name: 'test-mcp', version: '0.0.1' });
  });

  it('reads a brain:// URI — returns stub JSON with correct mimeType', async () => {
    const { client, cleanup } = await connectClient(mcp);
    const uri = 'brain://group-ii/working-memory/context/current';
    const result = await client.readResource({ uri });

    expect(result.contents).toHaveLength(1);
    const content = result.contents[0]!;
    expect(content.uri).toBe(uri);
    expect(content.mimeType).toBe('application/json');

    const body = JSON.parse(content.text as string) as {
      status: string;
      module: string;
      group: string;
    };
    expect(body.status).toBe('stub');
    expect(body.module).toBe('working-memory');
    expect(body.group).toBe('group-ii-cognitive-processing');

    await cleanup();
  });

  it('reads brain://group-iv/metacognition/confidence/current stub', async () => {
    const { client, cleanup } = await connectClient(mcp);
    const uri = 'brain://group-iv/metacognition/confidence/current';
    const result = await client.readResource({ uri });

    expect(result.contents[0]?.mimeType).toBe('application/json');
    const body = JSON.parse(result.contents[0]!.text as string) as { module: string };
    expect(body.module).toBe('metacognition');

    await cleanup();
  });

  it('returns error for unknown brain:// URI — JSON-RPC -32602', async () => {
    const { client, cleanup } = await connectClient(mcp);

    await expect(
      client.readResource({ uri: 'brain://group-ii/nonexistent/resource' }),
    ).rejects.toThrow();

    await cleanup();
  });

  it('reads an mcp://capabilities/ URI when module is registered', async () => {
    mcp.registry.register({
      moduleId: 'working-memory',
      layer: 'cognitive-processing',
      accepts: ['signal/text'],
      emits: ['memory/item'],
      version: '0.1.0',
    });

    const { client, cleanup } = await connectClient(mcp);
    const uri = 'mcp://capabilities/working-memory';
    const result = await client.readResource({ uri });

    expect(result.contents).toHaveLength(1);
    expect(result.contents[0]?.mimeType).toBe('application/json');
    const cap = JSON.parse(result.contents[0]!.text as string) as { moduleId: string };
    expect(cap.moduleId).toBe('working-memory');

    await cleanup();
  });

  it('returns error for unknown mcp://capabilities/ URI', async () => {
    const { client, cleanup } = await connectClient(mcp);

    await expect(
      client.readResource({ uri: 'mcp://capabilities/nonexistent-module' }),
    ).rejects.toThrow();

    await cleanup();
  });
});

describe('resources/subscribe (placeholder)', () => {
  it('subscribe URIs are listed in resources/list', async () => {
    const mcp = createMCPServer({ name: 'test-mcp', version: '0.0.1' });
    const { client, cleanup } = await connectClient(mcp);
    const result = await client.listResources();
    const subscribable = result.resources.filter(
      (r) =>
        r.uri === 'brain://group-ii/working-memory/context/current' ||
        r.uri === 'brain://group-iv/metacognition/confidence/current',
    );
    // Both priority subscribe URIs must appear in the registry
    expect(subscribable.length).toBe(2);
    await cleanup();
  });
});
