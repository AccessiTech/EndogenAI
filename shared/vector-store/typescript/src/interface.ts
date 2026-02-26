/**
 * VectorStoreAdapter — abstract interface for EndogenAI vector store adapters.
 *
 * All backend implementations (ChromaAdapter, QdrantAdapter) must implement
 * every method. Adapters own the embedding step — callers never supply raw vectors.
 *
 * @example
 * ```ts
 * class MyAdapter implements VectorStoreAdapter {
 *   async upsert(req: UpsertRequest): Promise<UpsertResponse> { ... }
 *   // ...
 * }
 * ```
 */

import type {
  CollectionInfo,
  CreateCollectionRequest,
  CreateCollectionResponse,
  DeleteRequest,
  DeleteResponse,
  DropCollectionRequest,
  DropCollectionResponse,
  ListCollectionsResponse,
  QueryRequest,
  QueryResponse,
  UpsertRequest,
  UpsertResponse,
} from "./models.js";

export interface VectorStoreAdapter {
  /** Optional: establish a connection / warm up client. Called once at startup. */
  connect?(): Promise<void>;

  /** Optional: release resources. Called at shutdown. */
  close?(): Promise<void>;

  /** Insert or update MemoryItems. Generates embeddings internally. */
  upsert(request: UpsertRequest): Promise<UpsertResponse>;

  /** Semantic similarity search. Embeds queryText internally. */
  query(request: QueryRequest): Promise<QueryResponse>;

  /** Delete MemoryItems by ID. Missing IDs are silently ignored. */
  delete(request: DeleteRequest): Promise<DeleteResponse>;

  /** Create a collection. Idempotent — no error if already exists. */
  createCollection(request: CreateCollectionRequest): Promise<CreateCollectionResponse>;

  /** Permanently delete a collection and all its records. */
  dropCollection(request: DropCollectionRequest): Promise<DropCollectionResponse>;

  /** Return all collections present in the backend. */
  listCollections(): Promise<ListCollectionsResponse>;
}

/** Convenience helper: create collection if it does not exist. Returns true if created. */
export async function ensureCollection(
  adapter: VectorStoreAdapter,
  collectionName: string,
): Promise<boolean> {
  const resp = await adapter.createCollection({ collectionName });
  return resp.created;
}

/** Raised by adapter implementations for unrecoverable backend errors. */
export class AdapterError extends Error {
  constructor(
    message: string,
    public readonly backend: string,
    public readonly retryable: boolean = false,
  ) {
    super(message);
    this.name = "AdapterError";
  }
}
