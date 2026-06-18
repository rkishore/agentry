import contextlib

from agentry.application.eval_runner import EvalRunner
from agentry.application.pipeline import RagPipeline
from agentry.core.models import Chunk, EvalCase, LlmCompletion, RetrievedChunk
from agentry.infrastructure.grading import NormalizedMatchGrader


class _StubRetriever:
    def retrieve(self, query, top_k):
        return [RetrievedChunk(chunk=Chunk("c0", "d", "Paris is the capital."), score=1.0)]


class _AnswerLlm:
    def __init__(self, text):
        self._text = text

    def complete(self, messages):
        return LlmCompletion(text=self._text, model="stub", prompt_tokens=1, completion_tokens=1)


class _RecordingSink:
    def __init__(self):
        self.events = []

    def emit(self, event):
        self.events.append(event)


class _NullTracer:
    def span(self, name):
        return contextlib.nullcontext()


def _runner(answer_text, sink):
    pipeline = RagPipeline(
        retriever=_StubRetriever(),
        llm=_AnswerLlm(answer_text),
        audit=sink,
        tracer=_NullTracer(),
    )
    return EvalRunner(pipeline=pipeline, grader=NormalizedMatchGrader(), audit=sink)


def EvalRunner_AllCasesPass_ReturnsAggregateOfOne():
    sink = _RecordingSink()
    runner = _runner("The capital of France is Paris.", sink)

    results, aggregate = runner.run(
        [EvalCase(case_id="c1", question="capital of France?", expected="Paris")]
    )

    assert aggregate == 1.0
    assert results[0].passed is True
    assert isinstance(aggregate, float)


def EvalRunner_CaseFails_EmitsEvalCompletedWithZeroScore():
    sink = _RecordingSink()
    runner = _runner("I do not know.", sink)

    results, aggregate = runner.run(
        [EvalCase(case_id="c1", question="capital of France?", expected="Paris")]
    )

    assert aggregate == 0.0
    assert results[0].passed is False
    completed = [e for e in sink.events if type(e).__name__ == "EvalCompleted"]
    assert len(completed) == 1
    assert completed[0].score == 0.0


def EvalRunner_NoCases_ReturnsZeroAggregate():
    sink = _RecordingSink()
    runner = _runner("anything", sink)

    results, aggregate = runner.run([])

    assert results == []
    assert aggregate == 0.0
