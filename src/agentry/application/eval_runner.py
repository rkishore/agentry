"""The eval runner: run cases through the pipeline, grade, audit, and aggregate."""

from __future__ import annotations

from uuid import uuid4

from agentry.application.pipeline import RagPipeline
from agentry.core.models import EvalCase, EvalCompleted, EvalResult
from agentry.core.ports import AuditSink, Grader


class EvalRunner:
    """Runs a list of :class:`EvalCase` and returns graded results plus an aggregate score."""

    def __init__(self, pipeline: RagPipeline, grader: Grader, audit: AuditSink) -> None:
        self._pipeline = pipeline
        self._grader = grader
        self._audit = audit

    def run(self, cases: list[EvalCase]) -> tuple[list[EvalResult], float]:
        """Run every case, emitting an ``EvalCompleted`` event each, and aggregate scores."""
        results: list[EvalResult] = []
        for case in cases:
            run_id = uuid4().hex
            answer = self._pipeline.run(case.question, run_id=run_id)
            passed, score = self._grader.grade(answer.text, case.expected)
            self._audit.emit(
                EvalCompleted(run_id=run_id, case_id=case.case_id, passed=passed, score=score)
            )
            results.append(
                EvalResult(
                    case_id=case.case_id,
                    question=case.question,
                    answer=answer.text,
                    expected=case.expected,
                    passed=passed,
                    score=score,
                )
            )
        aggregate = sum(r.score for r in results) / len(results) if results else 0.0
        return results, aggregate
