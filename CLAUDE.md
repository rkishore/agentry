# agentry — agent operating rules

`agentry` is a hand-built, eval-first agentic system, grown in phases and measured against
public benchmarks (FinanceBench first, then SOP-Bench). This file is the standing contract for
any coding agent (Claude Code, and later Codex) working in this repo. Read it, then read the
active sprint contract, before writing anything.

## The harness

Work proceeds in sprints under a three-role harness:
- **Planner** writes the sprint contract (happens outside this repo; lands in `docs/harness/`).
- **Generator** (you, by default) implements the active contract.
- **Evaluator** runs the gates in `docs/harness/gates.md` and passes/fails the sprint.

The **active contract** is the highest-numbered `docs/harness/sprint-NN-contract.md`.

## Prime directive

Implement the active sprint contract **exactly — no more, no less.** Every file and type the
contract lists must exist; nothing outside it should. If something seems missing or wrong,
stop and flag it for the human rather than inventing scope. Do not pull work forward from
later phases — that work lives in `docs/harness/deferred.md` and stays there until its sprint.

## Architecture (non-negotiable)

Hexagonal layering under `src/agentry/`:
- `core/` — pure domain: dataclasses + `typing.Protocol` ports. **Zero third-party imports.**
- `application/` — orchestration. Imports `core` **only**.
- `infrastructure/` — adapters (Chroma, embedders, LLM client, audit sink, tracer). Imports
  `core` plus its own tech libs **only** — never `application`, never `app`.
- `app/` — composition root + CLI. May import all inner layers.

Dependency arrows point inward. `application` and `infrastructure` are independent siblings —
neither imports the other. Domain- and benchmark-specific code (FinanceBench loaders, finance
graders, future SOP tools) lives in `app`/`infrastructure`, **never** in `core`/`application`.
These boundaries are machine-enforced (Gate 3); a violation fails the sprint even if it compiles.

## Conventions

- **Tooling:** `uv` for everything (`uv sync`, `uv run …`).
- **Ports** are named by role with no `I` prefix (`Embedder`, not `IEmbedder`). **Adapters**
  carry a tech prefix (`ChromaVectorStore`, `SentenceTransformerEmbedder`, `OpenAiLlmClient`, `AnthropicLlmClient`).
- **Tests** use `MethodOrScenario_Condition_ExpectedResult` naming.
- **No secrets in code.** The human sets `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` in their own
  environment and picks the provider with `AGENTRY_LLM_PROVIDER` (`openai` | `anthropic`, default
  `openai`). Tests use fakes (`FakeEmbedder`, `FakeLlmClient`) and make no network calls.
- **No TODO comments.** Anything not in the active contract goes to `docs/harness/deferred.md`.
- **No new dependencies** without adding them to `pyproject.toml` with a one-line rationale, and
  never into `core`.
- **No frameworks yet** (LangChain / LlamaIndex / LangGraph). They arrive later as adapters behind
  existing ports; building by hand now is the point.

## Definition of done

A sprint is done only when all gates in `docs/harness/gates.md` pass:

```
make install      # uv sync
make lint         # ruff check + format --check
make typecheck    # mypy strict
make test         # pytest, all green, no skips
make boundaries   # import-linter
make slice        # the vertical-slice run (Gate 6)
```

Green across all six, or the sprint is not done. Report any extra files/types you created and why.

## Git discipline

- The sprint contract is committed **first**, alone, before implementation.
- Small, conventional commits (`feat:`, `chore:`, `test:`…).
- One squashed/marked sprint commit once the gates are green.

## How to work a sprint

1. Read this file, then the active `sprint-NN-contract.md`, then `gates.md`.
2. Scaffold or implement only what the contract names.
3. Run the gates locally; iterate until green.
4. Flag anything ambiguous to the human instead of guessing scope.
