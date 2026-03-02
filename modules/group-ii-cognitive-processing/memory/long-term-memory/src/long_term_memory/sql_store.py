"""SQLite-backed structured fact store for long-term memory.

Default backend: SQLite (embedded).
Production backend: PostgreSQL (configurable via indexing.config.json).

Schema:
    facts(
        fact_id TEXT PRIMARY KEY,
        entity_id TEXT NOT NULL,
        predicate TEXT NOT NULL,
        object_value TEXT NOT NULL,
        importance REAL DEFAULT 0.5,
        source_item_id TEXT,
        created_at TEXT NOT NULL
    )
"""

from __future__ import annotations

import asyncio
import sqlite3
import uuid

import structlog

from long_term_memory.models import SemanticFact

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS facts (
    fact_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object_value TEXT NOT NULL,
    importance REAL NOT NULL DEFAULT 0.5,
    source_item_id TEXT,
    created_at TEXT NOT NULL
)
"""

_CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_entity_id ON facts(entity_id)
"""


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


class SQLFactStore:
    """Async-compatible SQLite fact store using asyncio.to_thread for I/O."""

    def __init__(self, db_path: str = "/tmp/endogenai_ltm_facts.db") -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = _connect(self._db_path)
            self._conn.execute(_CREATE_TABLE_SQL)
            self._conn.execute(_CREATE_INDEX_SQL)
            self._conn.commit()
        return self._conn

    def _sync_write_fact(self, fact: SemanticFact, fact_id: str) -> str:
        conn = self._get_conn()
        # Upsert: if (entity_id, predicate, object_value) already exists, update importance.
        cursor = conn.execute(
            "SELECT fact_id FROM facts WHERE entity_id = ? AND predicate = ? AND object_value = ?",
            (fact.entity_id, fact.predicate, fact.object_value),
        )
        existing = cursor.fetchone()
        if existing:
            existing_id = str(existing["fact_id"])
            conn.execute(
                "UPDATE facts SET importance = MAX(importance, ?) WHERE fact_id = ?",
                (fact.importance, existing_id),
            )
            conn.commit()
            return existing_id
        conn.execute(
            "INSERT INTO facts (fact_id, entity_id, predicate, object_value, importance, source_item_id, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                fact_id,
                fact.entity_id,
                fact.predicate,
                fact.object_value,
                fact.importance,
                fact.source_item_id,
                fact.created_at,
            ),
        )
        conn.commit()
        return fact_id

    def _sync_query_facts(self, entity_id: str) -> list[SemanticFact]:
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM facts WHERE entity_id = ? ORDER BY importance DESC",
            (entity_id,),
        )
        rows = cursor.fetchall()
        facts: list[SemanticFact] = []
        for row in rows:
            facts.append(
                SemanticFact(
                    entity_id=str(row["entity_id"]),
                    predicate=str(row["predicate"]),
                    object_value=str(row["object_value"]),
                    importance=float(row["importance"]),
                    source_item_id=row["source_item_id"],
                    created_at=str(row["created_at"]),
                )
            )
        return facts

    async def write_fact(self, fact: SemanticFact) -> str:
        """Upsert a semantic fact; update importance if predicate+object already present.

        Returns:
            The fact_id of the created or existing record.
        """
        fact_id = str(uuid.uuid4())
        result: str = await asyncio.to_thread(self._sync_write_fact, fact, fact_id)
        logger.debug("sql_fact_written", entity_id=fact.entity_id, predicate=fact.predicate)
        return result

    async def query_facts(self, entity_id: str) -> list[SemanticFact]:
        """Return all facts for an entity, ordered by importance descending."""
        return await asyncio.to_thread(self._sync_query_facts, entity_id)
