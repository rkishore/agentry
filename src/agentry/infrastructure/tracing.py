"""OpenTelemetry tracer adapter."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, cast


class OtelTracer:
    """Wraps an OpenTelemetry tracer, exposing spans as context managers."""

    def __init__(self, tracer: Any) -> None:
        self._tracer = tracer

    def span(self, name: str) -> AbstractContextManager[Any]:
        return cast(
            "AbstractContextManager[Any]",
            self._tracer.start_as_current_span(name),
        )
