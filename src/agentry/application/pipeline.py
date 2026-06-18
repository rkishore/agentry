"""The RAG pipeline: retrieve then answer, emitting the typed event stream in a trace span."""

from __future__ import annotations

import time

from agentry.core.models import (
    Answer,
    AnswerProduced,
    LlmCallCompleted,
    Message,
    RetrievalCompleted,
    RetrievedChunk,
    RunStarted,
)
from agentry.core.ports import AuditSink, LlmClient, Retriever, Tracer

_SYSTEM_PROMPT = "You are a helpful assistant. Answer the question using only the provided context."


def build_messages(question: str, chunks: list[RetrievedChunk]) -> list[Message]:
    """Assemble a grounded system + user message pair from the context and the question."""
    context = "\n".join(rc.chunk.text for rc in chunks)
    user_content = f"Context:\n{context}\n\nQuestion: {question}"
    return [
        Message(role="system", content=_SYSTEM_PROMPT),
        Message(role="user", content=user_content),
    ]


def _flatten(messages: list[Message]) -> str:
    """Flatten messages to ``role: content`` lines for the unchanged audit prompt field."""
    return "\n".join(f"{message.role}: {message.content}" for message in messages)


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

            messages = build_messages(question, retrieved)
            started = time.perf_counter()
            completion = self._llm.complete(messages)
            latency_ms = (time.perf_counter() - started) * 1000.0
            self._audit.emit(
                LlmCallCompleted(
                    run_id=run_id,
                    prompt=_flatten(messages),
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
