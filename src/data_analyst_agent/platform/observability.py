"""Minimal tracing and metrics instrumentation for platform execution."""

from __future__ import annotations

from typing import Any


class ObservabilityManager:
    """Collects spans and simple counters for tracing platform execution."""

    def __init__(self) -> None:
        self._spans: list[dict[str, Any]] = []
        self._metrics: dict[str, int] = {"events": 0}

    def start_span(self, name: str, *, metadata: dict[str, Any] | None = None) -> str:
        span_id = f"{name}-{len(self._spans) + 1}"
        span = {"id": span_id, "name": name, "metadata": metadata or {}, "events": [], "status": "running"}
        self._spans.append(span)
        return span_id

    def record_event(self, span_id: str, event: str, payload: dict[str, Any] | None = None) -> None:
        for span in self._spans:
            if span["id"] == span_id:
                span["events"].append({"event": event, "payload": payload or {}})
                self._metrics["events"] += 1
                return

    def finish_span(self, span_id: str, *, success: bool) -> None:
        for span in self._spans:
            if span["id"] == span_id:
                span["status"] = "succeeded" if success else "failed"
                return

    def get_trace(self, name: str) -> list[dict[str, Any]]:
        return [span for span in self._spans if span["name"] == name]

    def metrics(self) -> dict[str, int]:
        return dict(self._metrics)
