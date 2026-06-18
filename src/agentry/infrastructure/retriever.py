"""Dense retrieval adapter: embed the query, then nearest-neighbour search the store."""

from __future__ import annotations

from agentry.core.models import RetrievedChunk
from agentry.core.ports import Embedder, VectorStore


class DenseRetriever:
    """Top-k dense retrieval over a :class:`VectorStore` using an :class:`Embedder`."""

    def __init__(self, embedder: Embedder, store: VectorStore) -> None:
        self._embedder = embedder
        self._store = store

    def retrieve(self, query: str, top_k: int) -> list[RetrievedChunk]:
        embedding = self._embedder.embed([query])[0]
        return self._store.query(embedding, top_k)
