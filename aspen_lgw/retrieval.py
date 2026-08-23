"""Doc retrieval backends for doc_assist.

Default: in-memory keyword corpus (CI/offline).
Optional: pgvector when ASPEN_PGVECTOR_DSN is set and deps exist.
Never required for make smoke.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class DocHit:
    id: str
    text: str
    score: float = 0.0


# Lab corpus — same content as original doc_assist hardcode
DEFAULT_CORPUS: list[dict[str, str]] = [
    {"id": "sop-estop", "text": "E-stop: freeze motion, notify lead, dual-auth before resume."},
    {"id": "sop-thermal", "text": "Overtemp: reduce duty cycle 50%, check coolant, log sensor id."},
    {"id": "sop-handoff", "text": "Shift handoff: write what changed, open alarms, safe defaults."},
]


class Retriever(Protocol):
    def search(self, query: str, k: int = 3) -> list[DocHit]: ...


class InMemoryRetriever:
    def __init__(self, corpus: list[dict[str, str]] | None = None):
        self.corpus = list(corpus or DEFAULT_CORPUS)

    def search(self, query: str, k: int = 3) -> list[DocHit]:
        q = (query or "").lower()
        hits: list[DocHit] = []
        for doc in self.corpus:
            score = float(sum(1 for w in q.split() if w and w in doc["text"].lower()))
            if score:
                hits.append(DocHit(id=doc["id"], text=doc["text"], score=score))
        hits.sort(key=lambda h: -h.score)
        return hits[:k]


class PgvectorRetriever:
    """Optional pgvector backend.

    Expects env ASPEN_PGVECTOR_DSN (postgres URL) and table:
      aspen_sop_chunks(id text primary key, text text, embedding vector)
    Falls back to empty hits on any error (caller may chain memory).
    """

    def __init__(self, dsn: str | None = None):
        self.dsn = dsn or os.environ.get("ASPEN_PGVECTOR_DSN", "")
        self._ok = False
        self._err: str | None = None
        if not self.dsn:
            self._err = "no DSN"
            return
        try:
            import psycopg  # type: ignore
        except ImportError:
            self._err = "psycopg not installed"
            return
        try:
            self._psycopg = psycopg
            with psycopg.connect(self.dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            self._ok = True
        except Exception as e:
            self._err = f"{type(e).__name__}: {e}"

    @property
    def available(self) -> bool:
        return self._ok

    def search(self, query: str, k: int = 3) -> list[DocHit]:
        if not self._ok:
            return []
        # Keyword fallback on SQL without requiring embedding model in CI.
        # Real embedding path can replace this when model keys are budgeted.
        try:
            with self._psycopg.connect(self.dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, text,
                               (CASE WHEN lower(text) LIKE %s THEN 2 ELSE 1 END)::float AS score
                        FROM aspen_sop_chunks
                        WHERE lower(text) LIKE %s OR lower(id) LIKE %s
                        ORDER BY score DESC
                        LIMIT %s
                        """,
                        (f"%{(query or '').lower()}%", f"%{(query or '').lower()}%", f"%{(query or '').lower()}%", k),
                    )
                    rows = cur.fetchall()
            return [DocHit(id=r[0], text=r[1], score=float(r[2])) for r in rows]
        except Exception:
            return []


class CascadingRetriever:
    """Try primary (optional pgvector), then memory."""

    def __init__(self, primary: Retriever | None = None, fallback: Retriever | None = None):
        self.primary = primary
        self.fallback = fallback or InMemoryRetriever()

    def search(self, query: str, k: int = 3) -> list[DocHit]:
        if self.primary is not None:
            hits = self.primary.search(query, k=k)
            if hits:
                return hits
        return self.fallback.search(query, k=k)


def default_retriever() -> Retriever:
    """Build env-aware retriever. Memory always works."""
    dsn = os.environ.get("ASPEN_PGVECTOR_DSN", "").strip()
    if dsn:
        pg = PgvectorRetriever(dsn)
        if pg.available:
            return CascadingRetriever(primary=pg, fallback=InMemoryRetriever())
    return InMemoryRetriever()
