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
| 00 | Eval-first hexagonal skeleton (RAG slice, typed event stream, audit, tracing) | ✅ six gates green | ✅ PASS (2026-06-26) | `a71dcf9` |
| 01 | Rename `app/`→`entrypoints/`; migrate `LlmClient` to `list[Message]` (behavior-preserving) | ✅ six gates green, fixture eval still `1.0` | ✅ PASS (2026-06-26) | `1b39238` |
| 02 | First feature sprint (see below) | — contract not yet written | — | — |

When the Evaluator runs, record its verdict here as `✅ PASS` / `❌ FAIL (gate N: …)` with the gate
output it saw.

Branch: `main` (sprint work lands directly on main, matching the harness flow).

### Evaluator verdict — 2026-06-26 (independent session)

Each sprint verified at its own commit (`git checkout <commit>`, full gate set run from that tree).
Verdict is from observed command output only; Generator self-reports and the unverified carry-forward
notes were treated as claims to check.

**Sprint 00 (`a71dcf9`) — ✅ PASS, six gates green:**
- Gate 1: `make install` ok; ruff `All checks passed` + `24 files already formatted`; mypy strict `Success: no issues found in 19 source files`.
- Gate 2: `13 passed` in pytest, no skips; test-count cross-check `grep -rohE "def …" tests/ | wc -l` = `13` (matches collected).
- Gate 3: import-linter `Contracts: 2 kept, 0 broken` (`Hexagonal layers`, `Core is dependency-free`); contract references `agentry.app`, correct for this sprint.
- Gate 4: all named types present — 13 core models, 7 ports, 11 infra adapters, `app/` package (`composition.py`, `cli.py`).
- Gate 5: no files/types outside contract observed.
- Gate 6: `make slice` → `aggregate_score=1.0`; `test_slice_e2e.py` passes (CLI runs as `agentry.app.cli`).

**Sprint 01 (`1b39238`) — ✅ PASS, six gates green:**
- Gate 1: `make install` ok; ruff `All checks passed` + `24 files already formatted`; mypy strict `Success: no issues found in 19 source files`.
- Gate 2: `15 passed`, no skips; test-count cross-check = `15` (matches collected).
- Gate 3: import-linter `Contracts: 2 kept, 0 broken` with contract referencing `agentry.entrypoints`; `grep -rn "agentry.app\b"` finds **zero** refs in code/config/active docs (only the two historical contract files mention it).
- Gate 4: `entrypoints/` package, `Message` frozen dataclass (`role: Literal[...]`, `content: str`), `LlmClient.complete(self, messages: list[Message])` across port + all three adapters, `build_messages()` returning `list[Message]`, and doc/config edits all present.
- Gate 5: no scope creep; source tree is the Sprint-0 file set with `app/`→`entrypoints/` only. No FinanceBench/extraction/grading work.
- Gate 6: `make slice` → `aggregate_score=1.0`, **identical to Sprint 0**; `test_slice_e2e.py` asserts the five event types + ≥1 OTel span; `LlmCallCompleted.prompt` preserved via `_flatten()` (`role: content` lines).

**Carry-forward items (independently checked):**
1. ⚠️ **Partially refuted.** The `self._client: Any` annotations exist (`llm.py:26,50`) and Gate 1 is green — but the claim "`openai`/`anthropic` are installed in the venv" is **not reproduced** under the canonical gate. After `make install` (`uv sync`, no `[real]` extra), `uv pip list` shows neither, and `importlib.util.find_spec` returns `None` for both. mypy strict passes via `ignore_missing_imports = true` (pyproject mypy override) on absent SDKs — not because real stubs are present. The annotation is real and harmless; the stated *cause* doesn't match the gate environment. Non-blocking (no gate fails), flagged for the Planner.
2. ✅ **Confirmed.** `deferred.md` contains no `Message`-shape line (`grep -i message` → none); the contract's "remove" step was a no-op and the end-state is correct.
3. ✅ **Confirmed.** A single `_use_fakes()` (`composition.py:26`) gates both `_select_embedder()` and `_select_llm()` — the embedder and LLM axes are coupled, as noted.

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
