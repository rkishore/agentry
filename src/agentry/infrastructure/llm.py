"""LLM client adapters: OpenAI, Anthropic, and a grounded fake."""

from __future__ import annotations

from typing import Any

from agentry.core.models import LlmCompletion, Message

_CONTEXT_MARKER = "Context:"
_QUESTION_MARKER = "\n\nQuestion:"


def _last_user_content(messages: list[Message]) -> str:
    for message in reversed(messages):
        if message.role == "user":
            return message.content
    return messages[-1].content if messages else ""


class OpenAiLlmClient:
    """LlmClient backed by the OpenAI Chat Completions API."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        from openai import OpenAI

        self._client: Any = OpenAI()
        self._model = model

    def complete(self, messages: list[Message]) -> LlmCompletion:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": message.role, "content": message.content} for message in messages],
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

        self._client: Any = Anthropic()
        self._model = model

    def complete(self, messages: list[Message]) -> LlmCompletion:
        system = "\n".join(m.content for m in messages if m.role == "system")
        conversation = [
            {"role": m.role, "content": m.content} for m in messages if m.role != "system"
        ]
        kwargs: dict[str, object] = {
            "model": self._model,
            "max_tokens": 1024,
            "messages": conversation,
        }
        if system:
            kwargs["system"] = system
        response = self._client.messages.create(**kwargs)
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

    def complete(self, messages: list[Message]) -> LlmCompletion:
        text = self._grounded_answer(_last_user_content(messages))
        prompt_tokens = sum(len(message.content.split()) for message in messages)
        return LlmCompletion(
            text=text,
            model=self.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=len(text.split()),
        )

    @staticmethod
    def _grounded_answer(user_content: str) -> str:
        if _CONTEXT_MARKER not in user_content:
            return user_content.strip()
        start = user_content.index(_CONTEXT_MARKER) + len(_CONTEXT_MARKER)
        end = (
            user_content.index(_QUESTION_MARKER)
            if _QUESTION_MARKER in user_content
            else len(user_content)
        )
        return user_content[start:end].strip()
