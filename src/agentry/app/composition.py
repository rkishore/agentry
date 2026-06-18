"""Composition root: wires adapters into the application services.

Selects fake vs. real adapters via ``AGENTRY_USE_FAKES`` and the LLM provider via
``AGENTRY_LLM_PROVIDER``. Defaults to fakes so the slice and tests run hermetically.
"""

from __future__ import annotations

import os

from agentry.application.eval_runner import EvalRunner
from agentry.application.pipeline import RagPipeline
from agentry.core.ports import AuditSink, Embedder, LlmClient, Tracer, VectorStore
from agentry.infrastructure.audit import JsonlAuditSink
from agentry.infrastructure.chroma_store import ChromaVectorStore
from agentry.infrastructure.chunking import FixedSizeChunker
from agentry.infrastructure.embedders import FakeEmbedder, SentenceTransformerEmbedder
from agentry.infrastructure.grading import NormalizedMatchGrader
from agentry.infrastructure.llm import AnthropicLlmClient, FakeLlmClient, OpenAiLlmClient
from agentry.infrastructure.retriever import DenseRetriever
from agentry.infrastructure.tracing import OtelTracer

_FALSEY = {"0", "false", "no"}


def _use_fakes() -> bool:
    return os.environ.get("AGENTRY_USE_FAKES", "1").lower() not in _FALSEY


def _select_embedder() -> Embedder:
    if _use_fakes():
        return FakeEmbedder()
    return SentenceTransformerEmbedder()


def _select_llm() -> LlmClient:
    if _use_fakes():
        return FakeLlmClient()
    provider = os.environ.get("AGENTRY_LLM_PROVIDER", "openai").lower()
    if provider == "anthropic":
        return AnthropicLlmClient()
    return OpenAiLlmClient()


def _build_vector_store() -> VectorStore:
    return ChromaVectorStore(path=os.environ.get("AGENTRY_CHROMA_PATH", "./chroma"))


def _build_chunker() -> FixedSizeChunker:
    return FixedSizeChunker()


def _build_audit() -> AuditSink:
    return JsonlAuditSink(os.environ.get("AGENTRY_AUDIT_PATH", "./audit/run.jsonl"))


def _build_tracer() -> Tracer:
    from opentelemetry.sdk.trace import TracerProvider

    provider = TracerProvider()
    return OtelTracer(provider.get_tracer("agentry"))


def build_pipeline(audit: AuditSink | None = None) -> RagPipeline:
    """Assemble the RAG pipeline from the configured adapters."""
    sink = audit if audit is not None else _build_audit()
    retriever = DenseRetriever(_select_embedder(), _build_vector_store())
    return RagPipeline(
        retriever=retriever,
        llm=_select_llm(),
        audit=sink,
        tracer=_build_tracer(),
    )


def build_eval_runner() -> EvalRunner:
    """Assemble the eval runner, sharing one audit sink with its pipeline."""
    sink = _build_audit()
    pipeline = build_pipeline(audit=sink)
    return EvalRunner(pipeline=pipeline, grader=NormalizedMatchGrader(), audit=sink)
