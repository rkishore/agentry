"""Chroma-backed VectorStore adapter."""

from __future__ import annotations

from typing import Any

from agentry.core.models import Chunk, RetrievedChunk


class ChromaVectorStore:
    """Stores chunk embeddings in Chroma; persistent when given a path, else in-memory."""

    def __init__(self, path: str | None = None, collection: str = "agentry") -> None:
        import chromadb
        from chromadb.config import Settings

        settings = Settings(anonymized_telemetry=False, allow_reset=True)
        client: Any = (
            chromadb.PersistentClient(path=path, settings=settings)
            if path
            else chromadb.EphemeralClient(settings=settings)
        )
        self._collection: Any = client.get_or_create_collection(name=collection)

    def add(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        if not chunks:
            return
        self._collection.add(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            embeddings=embeddings,
            metadatas=[{"doc_id": chunk.doc_id} for chunk in chunks],
        )

    def query(self, embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        count = self._collection.count()
        if count == 0:
            return []
        result = self._collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, count),
        )
        ids = result["ids"][0]
        documents = result["documents"][0]
        metadatas = result["metadatas"][0]
        distances = result["distances"][0]

        retrieved: list[RetrievedChunk] = []
        for chunk_id, document, metadata, distance in zip(
            ids, documents, metadatas, distances, strict=False
        ):
            chunk = Chunk(
                chunk_id=str(chunk_id),
                doc_id=str(metadata.get("doc_id", "")),
                text=str(document),
            )
            retrieved.append(RetrievedChunk(chunk=chunk, score=1.0 / (1.0 + float(distance))))
        return retrieved
