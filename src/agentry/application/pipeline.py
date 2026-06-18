"""The RAG pipeline: retrieve then answer, emitting the typed event stream in a trace span."""

from __future__ import annotations

import time

from agentry.core.models import (
    Answer,
    AnswerProduced,
    LlmCallCompleted,
    RetrievalCompleted,
    RetrievedChunk,
    RunStarted,
)
from agentry.core.ports import AuditSink, LlmClient, Retriever, Tracer


def build_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    """Assemble a grounded prompt from the retrieved context and the question."""
    context = "\n".join(rc.chunk.text for rc in chunks)
    return f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"


class RagPipeline:
    """Retrieve relevant chunks, answer with the LLM, and audit every step."""

    def __init__(
        self,
        retriever: Retriever,
        llm: LlmClient,
        audit: AuditSink,
        tracer: Tracer,
        top_k: int = 5,
    ) -> None:
        self._retriever = retriever
        self._llm = llm
        self._audit = audit
        self._tracer = tracer
        self._top_k = top_k

    def run(self, question: str, run_id: str) -> Answer:
        """Run one question end-to-end, emitting the run-event stream within a span."""
        with self._tracer.span("rag.run"):
            self._audit.emit(RunStarted(run_id=run_id, question=question))

            retrieved = self._retriever.retrieve(question, self._top_k)
            chunk_ids = [rc.chunk.chunk_id for rc in retrieved]
            self._audit.emit(RetrievalCompleted(run_id=run_id, chunk_ids=chunk_ids))

            prompt = build_prompt(question, retrieved)
            started = time.perf_counter()
            completion = self._llm.complete(prompt)
            latency_ms = (time.perf_counter() - started) * 1000.0
            self._audit.emit(
                LlmCallCompleted(
                    run_id=run_id,
                    prompt=prompt,
                    model=completion.model,
                    prompt_tokens=completion.prompt_tokens,
                    completion_tokens=completion.completion_tokens,
                    latency_ms=latency_ms,
                    output=completion.text,
                )
            )

            answer = Answer(text=completion.text)
            self._audit.emit(
                AnswerProduced(run_id=run_id, answer=answer.text, fields=answer.fields)
            )
            return answer
