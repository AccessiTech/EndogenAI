/**
 * @accessitech/vector-store — public barrel export.
 *
 * @example
 * ```ts
 * import { ChromaAdapter, ensureCollection } from "@accessitech/vector-store";
 *
 * const adapter = new ChromaAdapter({ host: "localhost", port: 8000 });
 * await adapter.connect();
 * await ensureCollection(adapter, "brain.knowledge");
 * ```
 */

export { ChromaAdapter } from "./adapters/chroma.js";
export { AdapterError, ensureCollection } from "./interface.js";
export type { VectorStoreAdapter } from "./interface.js";
export type {
  ChromaConfig,
  CollectionInfo,
  CreateCollectionRequest,
  CreateCollectionResponse,
  DeleteRequest,
  DeleteResponse,
  DropCollectionRequest,
  DropCollectionResponse,
  EmbeddingConfig,
  EmbeddingProvider,
  Layer,
  ListCollectionsResponse,
  MemoryItem,
  MemoryType,
  QueryRequest,
  QueryResponse,
  QueryResult,
  UpsertRequest,
  UpsertResponse,
} from "./models.js";
export { COLLECTION_NAME_RE, DEFAULT_CHROMA_CONFIG, DEFAULT_EMBEDDING_CONFIG } from "./models.js";
