"""Deterministic grading adapter: normalized exact/substring match."""

from __future__ import annotations

import re

_NON_ALNUM = re.compile(r"[^a-z0-9\s]")
_WHITESPACE = re.compile(r"\s+")


class NormalizedMatchGrader:
    """Passes when the normalized expected value equals or is contained in the answer."""

    def grade(self, answer: str, expected: str) -> tuple[bool, float]:
        normalized_answer = self._normalize(answer)
        normalized_expected = self._normalize(expected)
        passed = bool(normalized_expected) and (
            normalized_answer == normalized_expected or normalized_expected in normalized_answer
        )
        return passed, 1.0 if passed else 0.0

    @staticmethod
    def _normalize(text: str) -> str:
        lowered = _NON_ALNUM.sub(" ", text.lower())
        return _WHITESPACE.sub(" ", lowered).strip()
