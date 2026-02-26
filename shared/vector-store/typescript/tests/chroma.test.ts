/**
 * ChromaDB adapter integration tests (TypeScript / Vitest).
 *
 * Spins up a real ChromaDB container via @testcontainers/chromadb and exercises
 * every operation in the VectorStoreAdapter interface contract.
 *
 * Run:
 *   cd shared/vector-store/typescript
 *   pnpm test
 *
 * Requirements:
 *   docker daemon running locally
 *   pnpm install
 *
 * A mock embedding function replaces Ollama so no external service is required.
 */

import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { GenericContainer, type StartedTestContainer } from "testcontainers";
import { ChromaAdapter } from "../src/adapters/chroma.js";
import type { MemoryItem } from "../src/models.js";

// ---------------------------------------------------------------------------
// Mock embedding (deterministic, no Ollama required)
// ---------------------------------------------------------------------------

const MOCK_DIMENSIONS = 16;

function mockEmbed(text: string): number[] {
  const encoder = new TextEncoder();
  const bytes = encoder.encode(text);
  const floats: number[] = [];
  for (let i = 0; i < MOCK_DIMENSIONS; i++) {
    floats.push(Math.sin(Number(bytes[i % bytes.length]) + i));
  }
  const norm = Math.sqrt(floats.reduce((s, v) => s + v * v, 0)) || 1;
  return floats.map((v) => v / norm);
}

// Patch the global fetch to intercept Ollama embedding calls
const _realFetch = globalThis.fetch;
globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
  const url = typeof input === "string" ? input : input.toString();
  if (url.includes("/api/embed")) {
    const body = JSON.parse((init?.body as string) ?? "{}") as { input: string[] };
    const embeddings = (body.input ?? []).map(mockEmbed);
    return new Response(JSON.stringify({ embeddings }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  }
  return _realFetch(input, init);
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeItem(collectionName: string, content: string): MemoryItem {
  return {
    id: crypto.randomUUID(),
    collectionName,
    content,
    type: "working",
    sourceModule: "test",
    importanceScore: 0.7,
    createdAt: new Date().toISOString(),
    accessCount: 0,
    metadata: {},
    tags: [],
    relatedIds: [],
  };
}

// ---------------------------------------------------------------------------
// Container setup
// ---------------------------------------------------------------------------

let container: StartedTestContainer;
let adapter: ChromaAdapter;
const TEST_COLLECTION = "brain.working-memory";
const ALT_COLLECTION = "brain.episodic-memory";

beforeAll(async () => {
  container = await new GenericContainer("chromadb/chroma:latest").withExposedPorts(8000).start();

  const host = container.getHost();
  const port = container.getMappedPort(8000);

  adapter = new ChromaAdapter(
    { mode: "http", host, port },
    { provider: "ollama", model: "mock", baseUrl: "http://mock-ollama" },
  );
  await adapter.connect();
}, 120_000);

afterAll(async () => {
  await adapter.close();
  await container.stop();
});

// ---------------------------------------------------------------------------
// Collection lifecycle
// ---------------------------------------------------------------------------

describe("collection lifecycle", () => {
  it("createCollection creates a new collection", async () => {
    const resp = await adapter.createCollection({ collectionName: TEST_COLLECTION });
    expect(resp.collectionName).toBe(TEST_COLLECTION);
    expect(resp.created).toBe(true);
  });

  it("createCollection is idempotent", async () => {
    await adapter.createCollection({ collectionName: TEST_COLLECTION });
    const resp = await adapter.createCollection({ collectionName: TEST_COLLECTION });
    expect(resp.created).toBe(false);
  });

  it("listCollections includes created collection", async () => {
    await adapter.createCollection({ collectionName: TEST_COLLECTION });
    const resp = await adapter.listCollections();
    const names = resp.collections.map((c) => c.name);
    expect(names).toContain(TEST_COLLECTION);
  });

  it("dropCollection removes the collection", async () => {
    await adapter.createCollection({ collectionName: ALT_COLLECTION });
    const resp = await adapter.dropCollection({ collectionName: ALT_COLLECTION });
    expect(resp.dropped).toBe(true);

    const list = await adapter.listCollections();
    expect(list.collections.map((c) => c.name)).not.toContain(ALT_COLLECTION);
  });

  it("dropCollection returns dropped=false for nonexistent collection", async () => {
    const resp = await adapter.dropCollection({ collectionName: "brain.long-term-memory" });
    expect(resp.dropped).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Upsert
// ---------------------------------------------------------------------------

describe("upsert", () => {
  it("upserts a single item and populates embedding", async () => {
    await adapter.createCollection({ collectionName: TEST_COLLECTION });
    const item = makeItem(TEST_COLLECTION, "Hello EndogenAI TypeScript adapter");
    const resp = await adapter.upsert({ collectionName: TEST_COLLECTION, items: [item] });

    expect(resp.upsertedIds).toContain(item.id);
    expect(item.embedding).toBeDefined();
    expect(item.embedding!.length).toBe(MOCK_DIMENSIONS);
  });

  it("upserts multiple items", async () => {
    await adapter.createCollection({ collectionName: TEST_COLLECTION });
    const items = Array.from({ length: 5 }, (_, i) => makeItem(TEST_COLLECTION, `Batch item ${i}`));
    const resp = await adapter.upsert({ collectionName: TEST_COLLECTION, items });
    expect(resp.upsertedIds.length).toBe(5);
    expect(new Set(resp.upsertedIds).size).toBe(5);
  });
});

// ---------------------------------------------------------------------------
// Query
// ---------------------------------------------------------------------------

describe("query", () => {
  it("returns query results ordered by score", async () => {
    await adapter.createCollection({ collectionName: TEST_COLLECTION });
    const items = [
      "vector databases enable semantic search",
      "neural networks learn representations",
      "the cat sat on the mat",
      "cosine similarity measures angle between vectors",
    ].map((text) => makeItem(TEST_COLLECTION, text));
    await adapter.upsert({ collectionName: TEST_COLLECTION, items });

    const resp = await adapter.query({
      collectionName: TEST_COLLECTION,
      queryText: "embedding similarity retrieval",
      nResults: 3,
    });

    expect(resp.results.length).toBeLessThanOrEqual(3);
    const scores = resp.results.map((r) => r.score);
    const sorted = [...scores].sort((a, b) => b - a);
    expect(scores).toEqual(sorted);
  });

  it("respects nResults limit", async () => {
    await adapter.createCollection({ collectionName: TEST_COLLECTION });
    const items = Array.from({ length: 10 }, (_, i) =>
      makeItem(TEST_COLLECTION, `TS record number ${i}`),
    );
    await adapter.upsert({ collectionName: TEST_COLLECTION, items });

    const resp = await adapter.query({
      collectionName: TEST_COLLECTION,
      queryText: "record",
      nResults: 4,
    });
    expect(resp.results.length).toBeLessThanOrEqual(4);
  });
});

// ---------------------------------------------------------------------------
// Delete
// ---------------------------------------------------------------------------

describe("delete", () => {
  it("deletes items by id", async () => {
    await adapter.createCollection({ collectionName: TEST_COLLECTION });
    const item = makeItem(TEST_COLLECTION, "TypeScript item to delete");
    await adapter.upsert({ collectionName: TEST_COLLECTION, items: [item] });

    const resp = await adapter.delete({ collectionName: TEST_COLLECTION, ids: [item.id] });
    expect(resp.deletedIds).toContain(item.id);

    const query = await adapter.query({
      collectionName: TEST_COLLECTION,
      queryText: "TypeScript item to delete",
      nResults: 10,
    });
    const returnedIds = query.results.map((r) => r.item.id);
    expect(returnedIds).not.toContain(item.id);
  });
});
