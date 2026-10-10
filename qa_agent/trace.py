"""Request-local tool traces, without synthetic reasoning or shared mutable state."""
from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter
from uuid import uuid4

from qa_agent.config import Settings, sanitize_error
from qa_agent.schemas import Step


class TraceRecorder:
    def __init__(self, trace_id: str | None = None, settings: Settings | None = None):
        self.trace_id = trace_id or str(uuid4())
        self.settings = settings
        self.steps: list[Step] = []
        self.llm_attempts = 0
        self.started = perf_counter()

    @property
    def latency_ms(self) -> int:
        return round((perf_counter() - self.started) * 1000)

    @contextmanager
    def step(self, name: str, input_summary: dict | None = None):
        record = Step(name=name, input_summary=input_summary or {})
        self.steps.append(record)
        started = perf_counter()
        try:
            yield record
        except Exception as exc:
            record.status = "error"
            record.output_summary["error"] = sanitize_error(exc, self.settings)
            raise
        finally:
            record.latency_ms = round((perf_counter() - started) * 1000)
