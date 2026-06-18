"""Ports: the role-named ``typing.Protocol`` interfaces the outer layers implement.

No ``I`` prefix; adapters carry the tech prefix instead. Stdlib + ``agentry.core`` only.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Protocol

from agentry.core.models import (
    Chunk,
    LlmCompletion,
    RetrievedChunk,
    RunEvent,
)


class Embedder(Protocol):
    """Turns text into dense vectors."""

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class VectorStore(Protocol):
    """Stores chunk embeddings and answers nearest-neighbour queries."""

    def add(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None: ...

    def query(self, embedding: list[float], top_k: int) -> list[RetrievedChunk]: ...


class Retriever(Protocol):
    """Retrieves the most relevant chunks for a query."""

    def retrieve(self, query: str, top_k: int) -> list[RetrievedChunk]: ...


class LlmClient(Protocol):
    """Completes a prompt, returning the text plus call metadata."""

    def complete(self, prompt: str) -> LlmCompletion: ...


class Grader(Protocol):
    """Grades an answer against an expected value, returning ``(passed, score)``."""

    def grade(self, answer: str, expected: str) -> tuple[bool, float]: ...


class AuditSink(Protocol):
    """Receives the typed run-event stream."""

    def emit(self, event: RunEvent) -> None: ...


class Tracer(Protocol):
    """Opens a trace span as a context manager."""

    def span(self, name: str) -> AbstractContextManager[Any]: ...
