"""Fixed-size chunking adapter."""

from __future__ import annotations

from agentry.core.models import Chunk, Document


class FixedSizeChunker:
    """Splits a document into fixed-size character windows with optional overlap."""

    def __init__(self, chunk_size: int = 512, overlap: int = 0) -> None:
        self._chunk_size = chunk_size
        self._overlap = overlap

    def chunk(self, document: Document) -> list[Chunk]:
        text = document.text
        if not text:
            return [Chunk(chunk_id=f"{document.doc_id}-0", doc_id=document.doc_id, text="")]

        step = max(1, self._chunk_size - self._overlap)
        chunks: list[Chunk] = []
        start = 0
        index = 0
        while start < len(text):
            piece = text[start : start + self._chunk_size]
            chunks.append(
                Chunk(
                    chunk_id=f"{document.doc_id}-{index}",
                    doc_id=document.doc_id,
                    text=piece,
                )
            )
            index += 1
            start += step
        return chunks
