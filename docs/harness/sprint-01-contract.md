## Sprint goal

Tidy the foundation before real features land on it: rename the outer layer and migrate the
`LlmClient` port from a single prompt string to a list of messages. **Behavior-preserving** —
no new capability, no event-schema change. Proven by the Gate 6 slice producing the *same*
result it did in Sprint 0 (fixture eval score `1.0`).

This sprint is deliberately refactor-only. FinanceBench ingestion, structured extraction, and
real grading are Sprint 2 — kept separate so this sprint's diffs prove "structure changed,
behavior did not."

## Deliverables

**Rename `app/` → `entrypoints/`**
- `src/agentry/app/` becomes `src/agentry/entrypoints/` (directory + package). All imports across
  the codebase update accordingly. CLI is now runnable as `python -m agentry.entrypoints.cli`.
- `composition.py` and `cli.py` move unchanged in content except for the rename and any internal
  import paths.

**`Message` value object + port migration**
- `src/agentry/core/models.py` — add `Message` (frozen dataclass; `role: Literal["system",
  "user", "assistant"]`, `content: str`; primitives only, stays stdlib-only, imports nothing
  third-party).
- `src/agentry/core/ports.py` — change `LlmClient.complete` from
  `complete(self, prompt: str) -> LlmCompletion` to
  `complete(self, messages: list[Message]) -> LlmCompletion`.
- `src/agentry/infrastructure/llm.py` — update all three adapters to accept `list[Message]`:
  `OpenAiLlmClient` maps to the OpenAI messages array; `AnthropicLlmClient` maps to Anthropic's
  messages + top-level `system` parameter; `FakeLlmClient` produces its grounded answer from the
  messages (unchanged behavior).
- `src/agentry/application/pipeline.py` — `build_prompt()` is renamed `build_messages()` and
  returns `list[Message]` (a system message + a user message carrying the question and retrieved
  context). The pipeline passes messages to `complete()`.

**Docs + config updated for the rename**
- `pyproject.toml` — the import-linter `layers` contract uses `agentry.entrypoints` in place of
  `agentry.app`.
- `docs/harness/gates.md` — architecture-boundary table and import-linter block updated to
  `agentry.entrypoints`.
- `CLAUDE.md` — layer description and any `agentry.app` references updated.
- `docs/harness/deferred.md` — remove the `Message`-shape line from the Phase 3 item (it lands now).

**Tests**
- Existing tests updated for the new signature and the rename.
- `test_models.py` — add a `Message` construction/validation test.
- The slice e2e test still passes and asserts the **same** eval score as Sprint 0.

## Pragmatic decisions

- **Refactor isolated from features.** No FinanceBench, no extraction, no grading change this
  sprint. The whole point is a clean behavior-preserving diff.
- **`entrypoints/` is the chosen name** for the outer layer (composition root + CLI / driving
  edge), replacing the near-homograph `app/` that read too close to `application/`.
- **`Message` is primitives-only**, with `role` as a stdlib `Literal` (type safety without taking
  a dependency; `core` stays dependency-free).
- **`LlmCallCompleted.prompt` is unchanged.** The pipeline flattens the message list to a string
  (e.g. `role: content` lines) for that field, so the audit event schema is identical to Sprint 0.
  The event records the full prompt context as before; only the port's input shape changed.
- **Model selection stays per-client-instance** (the `model` is still a return field, not a call
  argument). Per-step / per-call model routing remains a Phase 3 concern.

## Evaluator success criteria

All must be true. A single failure fails the sprint.

- **Gate 1 — Static.** `make install`, `make lint` (ruff zero errors), `make typecheck`
  (mypy strict, 0 issues).
- **Gate 2 — Tests.** `make test` green, no skipped tests. Independently confirm the test count
  with `grep -rohE "def [A-Za-z0-9]+_[A-Za-z0-9]+_[A-Za-z0-9]+" tests/ | wc -l` matching pytest's
  reported count (the custom collection glob can silently drop tests otherwise).
- **Gate 3 — Boundaries.** `make boundaries` passes with the contract referencing
  `agentry.entrypoints`. No `agentry.app` references remain anywhere
  (`grep -rn "agentry.app\b" .` returns nothing outside history).
- **Gate 4 — Deliverables present.** `Message` type, renamed package, updated signature, and all
  doc/config edits exist.
- **Gate 5 — No scope creep.** No feature work pulled in from Sprint 2 / `deferred.md`.
- **Gate 6 — Behavior preserved.** `make slice` runs and the fixture eval score is **identical to
  Sprint 0 (`1.0`)**; the typed event stream still emits the same five event types with the same
  schema. Manually, `AGENTRY_USE_FAKES=0 make slice` still answers correctly.

---

### Sprint 2 preview (not for this sprint)

The first feature sprint, where the core gets written by hand and produces the first meaningful
number:
- **FinanceBench ingestion** — load the 150-case open-source set + PDFs; real chunking.
- **Retrieval-recall metric** — score retrieved chunks against FinanceBench gold evidence,
  separately from answer accuracy.
- **Structured output extraction** — system message instructs `<answer>`/`<evidence>`/`<page>`
  tags; deterministic parser fills `Answer.fields`.
- **Real grading** — field-aware + numeric-tolerance grading (and the groundwork for Ragas).
- Likely also: split `AGENTRY_USE_FAKES` into independent embedder/LLM axes (the coupling noted
  in the Sprint-0 amendment), so retrieval can be tuned against a fake LLM.
