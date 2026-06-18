import contextlib

from agentry.application.pipeline import RagPipeline
from agentry.core.models import Answer, Chunk, LlmCompletion, RetrievedChunk


class _StubRetriever:
    def __init__(self, chunks):
        self._chunks = chunks

    def retrieve(self, query, top_k):
        return self._chunks[:top_k]


class _StubLlm:
    def complete(self, prompt):
        return LlmCompletion(
            text="The capital of France is Paris.",
            model="stub-llm",
            prompt_tokens=len(prompt.split()),
            completion_tokens=3,
        )


class _RecordingSink:
    def __init__(self):
        self.events = []

    def emit(self, event):
        self.events.append(event)


class _NullTracer:
    def __init__(self):
        self.spans = []

    def span(self, name):
        self.spans.append(name)
        return contextlib.nullcontext()


def _chunk(chunk_id, text):
    return RetrievedChunk(chunk=Chunk(chunk_id=chunk_id, doc_id="d", text=text), score=1.0)


def RagPipeline_Run_EmitsOrderedEventStreamAndOpensSpan():
    retriever = _StubRetriever([_chunk("c0", "Paris is the capital of France.")])
    sink = _RecordingSink()
    tracer = _NullTracer()
    pipeline = RagPipeline(retriever=retriever, llm=_StubLlm(), audit=sink, tracer=tracer)

    answer = pipeline.run("What is the capital of France?", run_id="run-1")

    assert isinstance(answer, Answer)
    emitted = [type(event).__name__ for event in sink.events]
    assert emitted == [
        "RunStarted",
        "RetrievalCompleted",
        "LlmCallCompleted",
        "AnswerProduced",
    ]
    assert tracer.spans == ["rag.run"]


def RagPipeline_Run_RetrievalEventCarriesChunkIds():
    retriever = _StubRetriever([_chunk("c0", "a"), _chunk("c1", "b")])
    sink = _RecordingSink()
    pipeline = RagPipeline(retriever=retriever, llm=_StubLlm(), audit=sink, tracer=_NullTracer())

    pipeline.run("q", run_id="run-2")

    retrieval = next(e for e in sink.events if type(e).__name__ == "RetrievalCompleted")
    assert retrieval.chunk_ids == ["c0", "c1"]


def RagPipeline_Run_LlmEventCarriesModelTokensAndOutput():
    sink = _RecordingSink()
    pipeline = RagPipeline(
        retriever=_StubRetriever([_chunk("c0", "Paris")]),
        llm=_StubLlm(),
        audit=sink,
        tracer=_NullTracer(),
    )

    pipeline.run("q", run_id="run-3")

    call = next(e for e in sink.events if type(e).__name__ == "LlmCallCompleted")
    assert call.model == "stub-llm"
    assert call.completion_tokens == 3
    assert "Paris" in call.output
    assert call.latency_ms >= 0.0
