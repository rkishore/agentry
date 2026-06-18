"""LLM client adapters: OpenAI, Anthropic, and a grounded fake."""

from __future__ import annotations

from agentry.core.models import LlmCompletion

_CONTEXT_MARKER = "Context:"
_QUESTION_MARKER = "\n\nQuestion:"


class OpenAiLlmClient:
    """LlmClient backed by the OpenAI Chat Completions API."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        from openai import OpenAI

        self._client = OpenAI()
        self._model = model

    def complete(self, prompt: str) -> LlmCompletion:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.choices[0].message.content or ""
        usage = response.usage
        return LlmCompletion(
            text=text,
            model=self._model,
            prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
        )


class AnthropicLlmClient:
    """LlmClient backed by the Anthropic Messages API."""

    def __init__(self, model: str = "claude-sonnet-4-6") -> None:
        from anthropic import Anthropic

        self._client = Anthropic()
        self._model = model

    def complete(self, prompt: str) -> LlmCompletion:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )
        usage = response.usage
        return LlmCompletion(
            text=text,
            model=self._model,
            prompt_tokens=getattr(usage, "input_tokens", 0) or 0,
            completion_tokens=getattr(usage, "output_tokens", 0) or 0,
        )


class FakeLlmClient:
    """Deterministic LlmClient that grounds its answer in the retrieved context."""

    model = "fake-llm-v0"

    def complete(self, prompt: str) -> LlmCompletion:
        text = self._grounded_answer(prompt)
        return LlmCompletion(
            text=text,
            model=self.model,
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(text.split()),
        )

    @staticmethod
    def _grounded_answer(prompt: str) -> str:
        if _CONTEXT_MARKER not in prompt:
            return prompt.strip()
        start = prompt.index(_CONTEXT_MARKER) + len(_CONTEXT_MARKER)
        end = prompt.index(_QUESTION_MARKER) if _QUESTION_MARKER in prompt else len(prompt)
        return prompt[start:end].strip()
