# Deferred work

Work that belongs to later phases. It must not appear in code — not as stubs, not as TODOs,
not as "while I'm here" additions — until its sprint opens.

- **Phase 1:** real FinanceBench ingestion; structured output extraction (XML-tag extractor +
  field-aware grading via `Answer.fields`); Ragas + numeric-tolerance + LLM-judge grading
- **Phase 2:** hybrid retrieval (BM25 + dense); reranking (MMR / Cohere / bge / mxbai)
- **Phase 3 (agentic / SOP-Bench):** step-machine executor; control tools (`complete_step`,
  `request_clarification`); context trimming; circuit breakers / guard rails; structural approval
  gates; expanded `RunEvent` taxonomy (step/tool/approval events); per-step model routing
  (cheap/non-thinking for deterministic steps, escalate on judgment); MCP-native tools
- **Phase 4:** pgvector and Pinecone `VectorStore` adapters; additional `LlmClient` backends behind
  the existing port — OpenRouter (OpenAI-compatible; possibly just a `base_url` change) and a
  unifying `LiteLlmClient` (collapses multiple providers into one adapter; add `litellm` to the
  forbidden-imports list for `core`); framework adapters (LangGraph / LlamaIndex) behind existing
  ports for measured comparison
- **Phase 5:** Langfuse wiring; Terraform + ECS Fargate deployment
