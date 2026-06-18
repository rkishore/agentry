import json

from agentry.core.models import RetrievalCompleted, RunStarted
from agentry.infrastructure.audit import JsonlAuditSink


def JsonlAuditSink_EmitEvents_WritesOneTaggedJsonLinePerEvent(tmp_path):
    path = tmp_path / "run.jsonl"
    sink = JsonlAuditSink(path)

    sink.emit(RunStarted(run_id="r1", question="What?"))
    sink.emit(RetrievalCompleted(run_id="r1", chunk_ids=["c0", "c1"]))

    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2

    first = json.loads(lines[0])
    assert first["event_type"] == "RunStarted"
    assert first["run_id"] == "r1"
    assert first["question"] == "What?"

    second = json.loads(lines[1])
    assert second["event_type"] == "RetrievalCompleted"
    assert second["chunk_ids"] == ["c0", "c1"]


def JsonlAuditSink_EmitTwice_AppendsRatherThanOverwrites(tmp_path):
    path = tmp_path / "nested" / "run.jsonl"
    sink = JsonlAuditSink(path)

    sink.emit(RunStarted(run_id="r1", question="first"))
    sink.emit(RunStarted(run_id="r2", question="second"))

    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["run_id"] == "r1"
    assert json.loads(lines[1])["run_id"] == "r2"
