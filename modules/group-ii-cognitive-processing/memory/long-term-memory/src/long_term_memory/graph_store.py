"""Knowledge graph adapter for long-term memory.

Default backend: Kuzu (embedded graph DB).
Production backend: Neo4j (configurable via indexing.config.json).

Provides entity-node and directed-edge storage for structured
factual associations between semantic memory items.
"""

from __future__ import annotations

from typing import Any

import structlog

from long_term_memory.models import GraphEdge

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class KuzuGraphStore:
    """Kuzu-backed knowledge graph store.

    Lazily initialises the Kuzu database on first use.
    Schema:
      - Node table ``Entity(entity_id STRING, label STRING)``
      - Edge table ``Relation(strength DOUBLE, predicate STRING, source_item_id STRING)``
    """

    def __init__(self, db_path: str = "/tmp/endogenai_ltm.kuzu") -> None:
        self._db_path = db_path
        self._db: Any = None
        self._conn: Any = None

    def _ensure_connected(self) -> None:
        """Lazily initialise and connect to the Kuzu database."""
        if self._conn is not None:
            return
        try:
            import kuzu

            self._db = kuzu.Database(self._db_path)
            self._conn = kuzu.Connection(self._db)
            self._init_schema()
        except ImportError:
            logger.warning("kuzu_not_installed", msg="Kuzu is not installed; graph store disabled.")

    def _execute(self, query: str, params: dict[str, object] | None = None) -> Any:
        """Execute a Cypher query; returns the Kuzu QueryResult."""
        self._ensure_connected()
        if self._conn is None:
            return None
        if params:
            return self._conn.execute(query, params)
        return self._conn.execute(query)

    def _init_schema(self) -> None:
        """Create tables if they do not exist."""
        self._execute(
            "CREATE NODE TABLE IF NOT EXISTS Entity(entity_id STRING, label STRING, PRIMARY KEY(entity_id))"
        )
        self._execute(
            "CREATE REL TABLE IF NOT EXISTS Relation"
            "(FROM Entity TO Entity, predicate STRING, strength DOUBLE, source_item_id STRING)"
        )

    def write_edge(
        self,
        src: str,
        predicate: str,
        dst: str,
        strength: float = 1.0,
        source_item_id: str | None = None,
    ) -> None:
        """Create or update an edge between two entity nodes.

        Both the source and target entity nodes are created if they do not exist.
        """
        # Upsert source and target nodes
        self._execute(
            "MERGE (e:Entity {entity_id: $id}) ON CREATE SET e.label = $id",
            {"id": src},
        )
        self._execute(
            "MERGE (e:Entity {entity_id: $id}) ON CREATE SET e.label = $id",
            {"id": dst},
        )
        # Create edge
        source_id = source_item_id or ""
        self._execute(
            "MATCH (s:Entity {entity_id: $src}), (t:Entity {entity_id: $dst}) "
            "CREATE (s)-[:Relation {predicate: $pred, strength: $strength, source_item_id: $sid}]->(t)",
            {"src": src, "dst": dst, "pred": predicate, "strength": strength, "sid": source_id},
        )
        logger.debug("graph_edge_written", src=src, predicate=predicate, dst=dst)

    def query_neighbours(self, entity_id: str, depth: int = 1) -> list[GraphEdge]:
        """Return neighbouring edges up to `depth` hops from `entity_id`.

        For depth=1 a single-hop query returns relation properties directly.
        For depth>1 the variable-length path is UNWIND-ed into individual hop
        relations; source_entity_id is the traversal root and target_entity_id
        is the terminal node of the full path.
        """
        if depth < 1 or depth > 3:
            raise ValueError(f"depth must be between 1 and 3, got {depth}")
        if depth == 1:
            query = (
                "MATCH (s:Entity {entity_id: $eid})-[r:Relation]->(t:Entity) "
                "RETURN s.entity_id, r.predicate, r.strength, r.source_item_id, t.entity_id"
            )
        else:
            query = (
                f"MATCH (s:Entity {{entity_id: $eid}})-[r:Relation*1..{depth}]->(t:Entity) "
                "UNWIND r AS rel "
                "RETURN s.entity_id, rel.predicate, rel.strength, rel.source_item_id, t.entity_id"
            )
        result = self._execute(query, {"eid": entity_id})
        edges: list[GraphEdge] = []
        if result is None:
            return edges
        while result.has_next():
            row = result.get_next()
            edges.append(
                GraphEdge(
                    source_entity_id=str(row[0]),
                    predicate=str(row[1]),
                    strength=float(row[2]) if row[2] is not None else 1.0,
                    source_item_id=str(row[3]) if row[3] else None,
                    target_entity_id=str(row[4]),
                )
            )
        return edges
