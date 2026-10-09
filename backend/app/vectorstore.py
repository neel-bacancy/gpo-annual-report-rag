"""ChromaDB persistent store. We supply our own embeddings, so Chroma only indexes and searches."""

from __future__ import annotations

from dataclasses import dataclass

import chromadb

from app.chunking import Chunk
from app.config import Settings


@dataclass
class Hit:
    id: str
    text: str
    body: str
    section: str
    page_start: int
    page_end: int
    similarity: float


class VectorStore:
    def __init__(self, settings: Settings):
        self.client = chromadb.PersistentClient(path=str(settings.chroma_dir))
        self.name = settings.collection_name

    def _collection(self):
        return self.client.get_or_create_collection(self.name, metadata={"hnsw:space": "cosine"})

    def rebuild(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        """Drop and recreate the collection so re-ingesting never leaves stale or duplicate chunks."""
        try:
            self.client.delete_collection(self.name)
        except Exception:
            pass
        col = self._collection()
        col.add(
            ids=[c.id for c in chunks],
            embeddings=vectors,
            documents=[c.text for c in chunks],
            metadatas=[{
                "body": c.body,
                "section": c.section,
                "page_start": c.page_start,
                "page_end": c.page_end,
                "tokens": c.tokens,
                "has_table": c.has_table,
            } for c in chunks],
        )

    def count(self) -> int:
        return self._collection().count()

    def search(self, vector: list[float], k: int) -> list[Hit]:
        res = self._collection().query(query_embeddings=[vector], n_results=k)
        hits = []
        for id_, doc, meta, dist in zip(res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]):
            hits.append(Hit(
                id=id_,
                text=doc,
                body=meta["body"],
                section=meta["section"],
                page_start=meta["page_start"],
                page_end=meta["page_end"],
                similarity=1.0 - dist,  # cosine distance -> similarity
            ))
        return hits
