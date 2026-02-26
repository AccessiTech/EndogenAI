/**
 * Shared TypeScript models for the EndogenAI vector store adapter.
 *
 * These mirror the JSON schemas in shared/vector-store/*.schema.json
 * and shared/types/memory-item.schema.json.
 */

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

export const COLLECTION_NAME_RE = /^brain\.[a-z][a-z0-9-]*$/;

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

export type EmbeddingProvider = "ollama" | "openai" | "cohere" | "huggingface";

export type MemoryType = "working" | "short-term" | "long-term" | "episodic";

export type Layer =
  | "sensory"
  | "subcortical"
  | "limbic"
  | "memory"
  | "prefrontal"
  | "motor"
  | "cerebellum";

// ---------------------------------------------------------------------------
// Config types
// ---------------------------------------------------------------------------

export interface EmbeddingConfig {
  provider: EmbeddingProvider;
  model: string;
  baseUrl: string;
  dimensions?: number;
  batchSize?: number;
  timeoutMs?: number;
}

export const DEFAULT_EMBEDDING_CONFIG: EmbeddingConfig = {
  provider: "ollama",
  model: "nomic-embed-text",
  baseUrl: "http://localhost:11434",
  batchSize: 32,
  timeoutMs: 30_000,
};

export interface ChromaConfig {
  mode: "http" | "embedded";
  host?: string;
  port?: number;
  ssl?: boolean;
  headers?: Record<string, string>;
  persistDirectory?: string;
  tenant?: string;
  database?: string;
}

export const DEFAULT_CHROMA_CONFIG: ChromaConfig = {
  mode: "http",
  host: "localhost",
  port: 8000,
  ssl: false,
  tenant: "default_tenant",
  database: "default_database",
};

// ---------------------------------------------------------------------------
// Domain types
// ---------------------------------------------------------------------------

export interface MemoryItem {
  id: string;
  collectionName: string;
  content: string;
  type: MemoryType;
  sourceModule: string;
  importanceScore: number;
  createdAt: string;
  updatedAt?: string;
  expiresAt?: string;
  accessCount: number;
  lastAccessedAt?: string;
  metadata: Record<string, unknown>;
  tags: string[];
  /** Populated by adapter after embedding. Do not set manually. */
  embedding?: number[];
  embeddingModel?: string;
  parentId?: string;
  relatedIds: string[];
}

// ---------------------------------------------------------------------------
// Operations — request / response
// ---------------------------------------------------------------------------

export interface UpsertRequest {
  collectionName: string;
  items: MemoryItem[];
}

export interface UpsertResponse {
  upsertedIds: string[];
}

export interface QueryRequest {
  collectionName: string;
  queryText: string;
  nResults?: number;
  where?: Record<string, unknown>;
  whereDocument?: string;
}

export interface QueryResult {
  item: MemoryItem;
  /** Cosine similarity in [0, 1]. Higher = more similar. */
  score: number;
}

export interface QueryResponse {
  results: QueryResult[];
}

export interface DeleteRequest {
  collectionName: string;
  ids: string[];
}

export interface DeleteResponse {
  deletedIds: string[];
}

export interface CreateCollectionRequest {
  collectionName: string;
  metadata?: Record<string, string>;
}

export interface CreateCollectionResponse {
  collectionName: string;
  /** True if newly created; false if it already existed. */
  created: boolean;
}

export interface DropCollectionRequest {
  collectionName: string;
}

export interface DropCollectionResponse {
  collectionName: string;
  dropped: boolean;
}

export interface CollectionInfo {
  name: string;
  count?: number;
  metadata?: Record<string, string>;
}

export interface ListCollectionsResponse {
  collections: CollectionInfo[];
}
