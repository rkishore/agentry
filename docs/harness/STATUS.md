# Harness status

A shared, reviewable snapshot of where the sprint harness stands — read by the Planner (to author
the next contract), the Generator (to resume), and the Evaluator (to verify). The contracts in this
directory remain the source of truth for scope; this file just records position and open items.

_Last updated: 2026-06-26._

## Sprint ledger

"Generator (self-report)" is the Generator's own gate run — a self-report, **not** independent
verification. "Evaluator (verified)" is the verdict from a separate Evaluator session; it is the
authoritative one. Keep the two columns distinct so the Evaluator's independence is visible.

| Sprint | Scope | Generator (self-report) | Evaluator (verified) | Commit |
| --- | --- | --- | --- | --- |
| 00 | Eval-first hexagonal skeleton (RAG slice, typed event stream, audit, tracing) | ✅ six gates green | ⏳ pending | `a71dcf9` |
| 01 | Rename `app/`→`entrypoints/`; migrate `LlmClient` to `list[Message]` (behavior-preserving) | ✅ six gates green, fixture eval still `1.0` | ⏳ pending | `1b39238` |
| 02 | First feature sprint (see below) | — contract not yet written | — | — |

When the Evaluator runs, record its verdict here as `✅ PASS` / `❌ FAIL (gate N: …)` with the gate
output it saw.

Branch: `main` (sprint work lands directly on main, matching the harness flow).

## Next: Sprint 02

The Planner authors `docs/harness/sprint-02-contract.md` before the Generator runs. Previewed scope
(from the sprint-01 contract footer):

- **FinanceBench ingestion** — 150-case open set + PDFs; real chunking.
- **Retrieval-recall metric** — score retrieved chunks against gold evidence, separate from answer
  accuracy.
- **Structured output extraction** — system message instructs `<answer>`/`<evidence>`/`<page>` tags;
  deterministic parser fills `Answer.fields`.
- **Real grading** — field-aware + numeric-tolerance (groundwork for Ragas).
- Likely: split `AGENTRY_USE_FAKES` into independent embedder/LLM axes.

## Open items carried forward (Generator-reported, unverified)

- **`openai`/`anthropic` are installed in the venv** (they weren't in sprint 00). With the real SDK
  stubs present, mypy strict rejects plain message-dict lists, so `OpenAiLlmClient` /
  `AnthropicLlmClient` annotate `self._client: Any` (same pattern as the Chroma collection).
- **`deferred.md` "remove the Message-shape line" (sprint-01 contract) was a no-op** — no such line
  existed in the Phase 3 item. End-state is correct; flagged for the Planner, contract left unedited.
- **`AGENTRY_USE_FAKES` couples the embedder and LLM axes** — one flag selects both; sprint 02
  previews splitting them so retrieval can be tuned against a fake LLM.
