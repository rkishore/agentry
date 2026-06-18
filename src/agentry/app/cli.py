"""CLI entrypoint: ``ingest``, ``query``, and ``eval`` commands.

Run as ``python -m agentry.app.cli <command>``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from uuid import uuid4

from agentry.app import composition
from agentry.core.models import Document, EvalCase


def _load_documents(directory: str) -> list[Document]:
    root = Path(directory)
    documents: list[Document] = []
    for path in sorted(root.glob("*.txt")):
        documents.append(Document(doc_id=path.stem, text=path.read_text(encoding="utf-8")))
    return documents


def _load_cases(path: str) -> list[EvalCase]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    records = raw if isinstance(raw, list) else [raw]
    cases: list[EvalCase] = []
    for index, record in enumerate(records):
        cases.append(
            EvalCase(
                case_id=str(record.get("case_id", f"case-{index}")),
                question=str(record["question"]),
                expected=str(record["expected"]),
            )
        )
    return cases


def _ingest(directory: str) -> None:
    chunker = composition._build_chunker()
    embedder = composition._select_embedder()
    store = composition._build_vector_store()
    documents = _load_documents(directory)
    for document in documents:
        chunks = chunker.chunk(document)
        embeddings = embedder.embed([chunk.text for chunk in chunks])
        store.add(chunks, embeddings)
    print(f"Ingested {len(documents)} document(s) into the vector store.")


def _query(question: str) -> None:
    pipeline = composition.build_pipeline()
    answer = pipeline.run(question, run_id=uuid4().hex)
    print(answer.text)


def _eval(path: str) -> None:
    runner = composition.build_eval_runner()
    results, aggregate = runner.run(_load_cases(path))
    for result in results:
        print(f"{result.case_id}: passed={result.passed} score={result.score}")
    print(f"aggregate_score={aggregate}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentry")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest a directory of .txt documents")
    ingest_parser.add_argument("directory")

    query_parser = subparsers.add_parser("query", help="Answer a single question")
    query_parser.add_argument("question")

    eval_parser = subparsers.add_parser("eval", help="Run an eval JSON file")
    eval_parser.add_argument("path")

    args = parser.parse_args(argv)
    if args.command == "ingest":
        _ingest(args.directory)
    elif args.command == "query":
        _query(args.question)
    elif args.command == "eval":
        _eval(args.path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
