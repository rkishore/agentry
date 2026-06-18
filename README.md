# agentry

An eval-first agentic system, built by hand in phases and measured against public benchmarks
(FinanceBench first, then SOP-Bench). Evals, observability, and audit logging are load-bearing
from the first commit.

## Architecture

Hexagonal (ports-and-adapters) layering under `src/agentry/`, dependency arrows pointing inward:

| Layer | Responsibility | May import |
| --- | --- | --- |
| `core/` | pure domain — dataclasses + `typing.Protocol` ports | stdlib only |
| `application/` | orchestration (`RagPipeline`, `EvalRunner`) | `core` only |
| `infrastructure/` | adapters (Chroma, embedders, LLM clients, audit, tracer) | `core` + own tech libs |
| `app/` | composition root + CLI | all inner layers |

`application` and `infrastructure` are independent siblings. Boundaries are machine-enforced with
import-linter (`make boundaries`).

## Setup

```bash
make install      # uv sync
```

## Gates

The project-local definition of done (see `docs/harness/gates.md`):

```bash
make lint         # ruff check + format --check
make typecheck    # mypy strict (src)
make test         # pytest, all green, no skips
make boundaries   # import-linter
make slice        # the vertical-slice run
```

## The vertical slice

`make slice` ingests the fixture docs, answers the fixture question, and scores the fixture eval
case, writing a typed run-event audit stream and emitting trace spans along the way.

By default the slice runs **hermetically** on fakes (`FakeEmbedder` + `FakeLlmClient`), needing no
API key and making no network calls. The hermetic end-to-end path is also asserted by
`tests/test_slice_e2e.py` (which additionally captures spans via an in-memory OTel exporter).

### Running the slice against the real embedder + LLM

Set the provider, supply the matching key, and turn fakes off:

```bash
export AGENTRY_USE_FAKES=0
export AGENTRY_LLM_PROVIDER=openai        # or: anthropic
export OPENAI_API_KEY=...                 # or: ANTHROPIC_API_KEY=...
uv sync --extra real                      # installs sentence-transformers, openai, anthropic
make slice
```

The real embedder is a local 384-dim sentence-transformer (no key); the LLM provider is selected
by `AGENTRY_LLM_PROVIDER`. Keys are read from the environment and never committed.

### Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `AGENTRY_USE_FAKES` | `1` | use fake embedder/LLM (hermetic); set `0` for real adapters |
| `AGENTRY_LLM_PROVIDER` | `openai` | `openai` or `anthropic` (real mode only) |
| `AGENTRY_CHROMA_PATH` | `./chroma` | persistent Chroma directory |
| `AGENTRY_AUDIT_PATH` | `./audit/run.jsonl` | append-only run-event log |

## License

MIT — see `LICENSE`.
