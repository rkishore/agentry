import json
from pathlib import Path

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from agentry.application.eval_runner import EvalRunner
from agentry.application.pipeline import RagPipeline
from agentry.core.models import Document, EvalCase
from agentry.infrastructure.audit import JsonlAuditSink
from agentry.infrastructure.chroma_store import ChromaVectorStore
from agentry.infrastructure.chunking import FixedSizeChunker
from agentry.infrastructure.embedders import FakeEmbedder
from agentry.infrastructure.grading import NormalizedMatchGrader
from agentry.infrastructure.llm import FakeLlmClient
from agentry.infrastructure.retriever import DenseRetriever
from agentry.infrastructure.tracing import OtelTracer

_FIXTURES = Path(__file__).parent / "fixtures"
_REQUIRED_EVENTS = [
    "RunStarted",
    "RetrievalCompleted",
    "LlmCallCompleted",
    "AnswerProduced",
    "EvalCompleted",
]


def Slice_FakesAndInMemoryExporter_ProducesScoreEventStreamAndSpan(tmp_path):
    # Tracer wired to an in-memory exporter so we can assert spans were emitted.
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = OtelTracer(provider.get_tracer("agentry-test"))

    embedder = FakeEmbedder()
    store = ChromaVectorStore()
    chunker = FixedSizeChunker()

    for txt in sorted(_FIXTURES.glob("*.txt")):
        document = Document(doc_id=txt.stem, text=txt.read_text(encoding="utf-8"))
        chunks = chunker.chunk(document)
        store.add(chunks, embedder.embed([chunk.text for chunk in chunks]))

    audit_path = tmp_path / "run.jsonl"
    audit = JsonlAuditSink(audit_path)
    pipeline = RagPipeline(
        retriever=DenseRetriever(embedder, store),
        llm=FakeLlmClient(),
        audit=audit,
        tracer=tracer,
    )
    runner = EvalRunner(pipeline=pipeline, grader=NormalizedMatchGrader(), audit=audit)

    case_data = json.loads((_FIXTURES / "eval.json").read_text(encoding="utf-8"))
    cases = [
        EvalCase(
            case_id=case_data["case_id"],
            question=case_data["question"],
            expected=case_data["expected"],
        )
    ]

    results, aggregate = runner.run(cases)

    # (a) a numeric EvalResult score, identical to Sprint 0 (behavior preserved).
    assert isinstance(aggregate, float)
    assert results and isinstance(results[0].score, float)
    assert aggregate == 1.0

    # (b) an append-only typed event stream carrying the required payload.
    records = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    types = [record["event_type"] for record in records]
    for required in _REQUIRED_EVENTS:
        assert required in types

    llm_record = next(r for r in records if r["event_type"] == "LlmCallCompleted")
    assert llm_record["prompt"]
    assert llm_record["model"]
    assert "prompt_tokens" in llm_record
    assert "completion_tokens" in llm_record
    assert "latency_ms" in llm_record
    assert llm_record["output"]

    retrieval_record = next(r for r in records if r["event_type"] == "RetrievalCompleted")
    assert isinstance(retrieval_record["chunk_ids"], list)
    assert retrieval_record["chunk_ids"]

    eval_record = next(r for r in records if r["event_type"] == "EvalCompleted")
    assert "passed" in eval_record
    assert "score" in eval_record

    # (c) at least one OTel span was emitted.
    assert len(exporter.get_finished_spans()) >= 1
