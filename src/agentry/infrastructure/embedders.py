"""Embedder adapters: a real sentence-transformer and a deterministic fake."""

from __future__ import annotations

import hashlib

_DEFAULT_DIM = 384


class SentenceTransformerEmbedder:
    """384-dim local embedder backed by a sentence-transformers model (no API key)."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(list(texts), convert_to_numpy=True)
        return [[float(value) for value in row] for row in vectors]


class FakeEmbedder:
    """Deterministic, hash-based embedder. Same text always maps to the same vector."""

    def __init__(self, dim: int = _DEFAULT_DIM) -> None:
        self._dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        counter = 0
        while len(values) < self._dim:
            block = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
            for byte in block:
                values.append(byte / 255.0)
                if len(values) >= self._dim:
                    break
            counter += 1
        return values[: self._dim]
