from agentry.core.models import (
    Answer,
    AnswerProduced,
    EvalResult,
    LlmCallCompleted,
    RetrievalCompleted,
)


def Answer_NoFields_DefaultsToEmptyDict():
    answer = Answer(text="hello")
    assert answer.text == "hello"
    assert answer.fields == {}


def Answer_TwoInstances_DoNotShareFieldsDict():
    first = Answer(text="a")
    second = Answer(text="b")
    assert first.fields is not second.fields


def RunEventSubtypes_Constructed_CarryRunIdAndPayload():
    retrieval = RetrievalCompleted(run_id="r1", chunk_ids=["c0", "c1"])
    assert retrieval.run_id == "r1"
    assert retrieval.chunk_ids == ["c0", "c1"]

    call = LlmCallCompleted(
        run_id="r1",
        prompt="p",
        model="m",
        prompt_tokens=3,
        completion_tokens=4,
        latency_ms=1.5,
        output="o",
    )
    assert call.model == "m"
    assert call.latency_ms == 1.5

    produced = AnswerProduced(run_id="r1", answer="o", fields={})
    assert produced.fields == {}


def EvalResult_Constructed_HoldsVerdictAndScore():
    result = EvalResult(
        case_id="c",
        question="q",
        answer="a",
        expected="a",
        passed=True,
        score=1.0,
    )
    assert result.passed is True
    assert result.score == 1.0
