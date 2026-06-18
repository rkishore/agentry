# Gates

The project-local definition of "done." These are the runnable checks the Evaluator executes
against the Generator's output. Every gate must pass — a single failure fails the sprint.

## Gate commands

All gates run through `make` (which wraps `uv run`). The Evaluator runs commands; it does not
judge from reading code.

| Gate | Command | Pass criterion |
| --- | --- | --- |
| 1 — Static | `make install` then `make lint` then `make typecheck` | install succeeds; ruff zero errors; mypy strict exits 0 |
| 2 — Tests | `make test` | pytest exits 0, all green, **no skipped tests** |
| 3 — Boundaries | `make boundaries` | import-linter reports all contracts kept |
| 4 — Deliverables | `find`/`grep` against the contract | every named file path and type exists |
| 5 — No scope creep | review tree vs. contract | no files/types outside the contract (auto-fail only if they break boundaries or APIs) |
| 6 — Vertical slice | `make slice` and `test_slice_e2e.py` | see below |

### Make targets

```make
install:    uv sync
lint:       uv run ruff check . && uv run ruff format --check .
typecheck:  uv run mypy src
test:       uv run pytest
boundaries: uv run lint-imports
slice:      uv run python -m agentry.entrypoints.cli ingest tests/fixtures \
         && uv run python -m agentry.entrypoints.cli query "$(shell cat tests/fixtures/eval.json | python -c 'import sys,json;print(json.load(sys.stdin)["question"])')" \
         && uv run python -m agentry.entrypoints.cli eval tests/fixtures/eval.json
```

### Gate 6 — what the slice must prove

`test_slice_e2e.py` (hermetic: `FakeEmbedder` + `FakeLlmClient` + in-memory OTel exporter) asserts,
in one run:
1. a numeric `EvalResult` score is produced over `tests/fixtures/eval.json`;
2. the `JsonlAuditSink` file holds an append-only typed event stream for the run containing at
   least `RunStarted`, `RetrievalCompleted`, `LlmCallCompleted`, `AnswerProduced`, `EvalCompleted`,
   collectively carrying prompt, retrieved chunk IDs, model id, tokens, latency, output, eval verdict;
3. at least one OTel span was emitted.

`README.md` documents the manual `make slice` run against the **real** embedder + LLM (needs
`OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in the environment, matching `AGENTRY_LLM_PROVIDER`).

## Architecture-boundary table

| Package | May import | Must NOT import |
| --- | --- | --- |
| `agentry.core` | stdlib only (`dataclasses`, `typing`) | any third-party; `application`, `infrastructure`, `entrypoints` |
| `agentry.application` | `agentry.core` | `infrastructure`, `entrypoints`; benchmark/domain libs |
| `agentry.infrastructure` | `agentry.core` + own tech libs | `agentry.application`, `agentry.entrypoints` |
| `agentry.entrypoints` | `core`, `application`, `infrastructure` | — |
| `tests` | all | — |

`application` and `infrastructure` are **independent siblings** — neither may import the other.

## import-linter contracts (canonical; goes in `pyproject.toml`)

```toml
[tool.importlinter]
root_package = "agentry"

[[tool.importlinter.contracts]]
name = "Hexagonal layers"
type = "layers"
layers = [
    "agentry.entrypoints",
    "agentry.application | agentry.infrastructure",
    "agentry.core",
]

[[tool.importlinter.contracts]]
name = "Core is dependency-free"
type = "forbidden"
source_modules = ["agentry.core"]
forbidden_modules = [
    "chromadb",
    "sentence_transformers",
    "openai",
    "anthropic",
    "opentelemetry",
    "langfuse",
    "pydantic",
]
```

The `layers` contract enforces the dependency direction and the sibling independence of
`application`/`infrastructure`. The `forbidden` contract enforces the zero-third-party rule for
`core` against the known heavy packages; reviewers still eyeball `core` for any other stray import,
since enumerating every third-party package is not feasible.

## Naming and test conventions

- **Ports** (in `core/ports.py`): role name, no `I` prefix — `Embedder`, `VectorStore`, `Retriever`,
  `LlmClient`, `Grader`, `AuditSink`, `Tracer`.
- **Adapters** (in `infrastructure/`): tech prefix — `ChromaVectorStore`,
  `SentenceTransformerEmbedder`, `OpenAiLlmClient`, `AnthropicLlmClient`, `JsonlAuditSink`,
  `OtelTracer`. Fakes are
  prefixed `Fake` and live with their adapter or in a test module.
- **Tests**: `MethodOrScenario_Condition_ExpectedResult`
  (e.g. `RagPipeline_NoChunksRetrieved_EmitsAnswerProducedWithEmptyFields`).
- **No copyright header** on source files; MIT `LICENSE` at the repo root covers licensing.

## On scope (Gate 5)

The Generator implements the active contract exactly. Work belonging to later phases is listed in
`deferred.md` and must not appear in code — not as stubs, not as TODOs, not as "while I'm here"
additions. Extra files are flagged in the Evaluator report and auto-fail only if they cross a
boundary or change a public interface.
