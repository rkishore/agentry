"""Pure domain models: documents, retrieval, answers, evals, and the run-event stream.

Zero third-party imports — stdlib ``dataclasses`` only.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Document:
    """A source document prior to chunking."""

    doc_id: str
    text: str


@dataclass(frozen=True)
class Chunk:
    """A slice of a :class:`Document` suitable for embedding and retrieval."""

    chunk_id: str
    doc_id: str
    text: str


@dataclass(frozen=True)
class RetrievedChunk:
    """A chunk returned by retrieval, with its relevance score."""

    chunk: Chunk
    score: float


@dataclass(frozen=True)
class Answer:
    """A generated answer.

    ``fields`` is the forward-compat seam for Phase-1 structured extraction; it
    defaults to an empty mapping in this sprint.
    """

    text: str
    fields: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class LlmCompletion:
    """The result of a single LLM call, carrying the metadata the audit stream records."""

    text: str
    model: str
    prompt_tokens: int
    completion_tokens: int


@dataclass(frozen=True)
class EvalCase:
    """A single evaluation case: a question and its expected answer."""

    case_id: str
    question: str
    expected: str


@dataclass(frozen=True)
class EvalResult:
    """The graded outcome of running an :class:`EvalCase` through the pipeline."""

    case_id: str
    question: str
    answer: str
    expected: str
    passed: bool
    score: float


@dataclass(frozen=True)
class RunEvent:
    """Base type for the typed run-event stream. Every event carries a ``run_id``."""

    run_id: str


@dataclass(frozen=True)
class RunStarted(RunEvent):
    """A pipeline run has begun for a given question."""

    question: str


@dataclass(frozen=True)
class RetrievalCompleted(RunEvent):
    """Retrieval finished; carries the ordered ids of the retrieved chunks."""

    chunk_ids: list[str]


@dataclass(frozen=True)
class LlmCallCompleted(RunEvent):
    """A single LLM call finished; carries prompt, model, tokens, latency, and output."""

    prompt: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    output: str


@dataclass(frozen=True)
class AnswerProduced(RunEvent):
    """The pipeline produced a final answer."""

    answer: str
    fields: dict[str, str]


@dataclass(frozen=True)
class EvalCompleted(RunEvent):
    """An eval case was graded; carries the verdict and score."""

    case_id: str
    passed: bool
    score: float
