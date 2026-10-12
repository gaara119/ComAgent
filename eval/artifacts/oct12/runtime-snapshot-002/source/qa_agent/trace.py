"""Request-local tool traces, without synthetic reasoning or shared mutable state."""
from __future__ import annotations

from contextlib import contextmanager
from functools import wraps
from inspect import BoundArguments, iscoroutinefunction, signature
from time import perf_counter
from typing import Any, Callable
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


# Tool summaries are deliberately explicit. Never serialize function arguments:
# an executor argument contains a credential-bearing connection string.
_SUMMARY_FIELDS = frozenset({"sql", "db_id", "row_count", "columns", "truncated"})


def _safe_summary(summary: dict[str, Any], trace: TraceRecorder) -> dict[str, Any]:
    def safe(value: Any) -> Any:
        if isinstance(value, str):
            return sanitize_error(value, trace.settings)
        if isinstance(value, list):
            return [safe(item) for item in value]
        if value is None or isinstance(value, (bool, int, float)):
            return value
        raise TypeError("Tool trace summaries accept only strings, numbers, booleans, lists and null")

    return {key: safe(value) for key, value in summary.items() if key in _SUMMARY_FIELDS}


def traced(
    name: str,
    *,
    input_summary: Callable[[BoundArguments], dict[str, Any]] | None = None,
    output_summary: Callable[[Any], dict[str, Any]] | None = None,
):
    """Record one tool step in its explicit request-local ``trace`` argument.

    Only opted-in, allowlisted summary fields are captured. The function still
    runs normally when no recorder is supplied; return values and exceptions
    propagate unchanged. Sync and async tools use the same Step protocol.
    """
    def decorate(function):
        function_signature = signature(function)

        def recorder_and_input(args, kwargs):
            arguments = function_signature.bind(*args, **kwargs)
            arguments.apply_defaults()
            trace = arguments.arguments.get("trace")
            if trace is None:
                return None, {}
            if not isinstance(trace, TraceRecorder):
                raise TypeError("trace must be a TraceRecorder or None")
            summary = input_summary(arguments) if input_summary else {}
            return trace, _safe_summary(summary, trace)

        if iscoroutinefunction(function):
            @wraps(function)
            async def async_wrapper(*args, **kwargs):
                trace, summary = recorder_and_input(args, kwargs)
                if trace is None:
                    return await function(*args, **kwargs)
                with trace.step(name, summary) as step:
                    result = await function(*args, **kwargs)
                    step.output_summary = _safe_summary(output_summary(result) if output_summary else {}, trace)
                    return result
            return async_wrapper

        @wraps(function)
        def sync_wrapper(*args, **kwargs):
            trace, summary = recorder_and_input(args, kwargs)
            if trace is None:
                return function(*args, **kwargs)
            with trace.step(name, summary) as step:
                result = function(*args, **kwargs)
                step.output_summary = _safe_summary(output_summary(result) if output_summary else {}, trace)
                return result
        return sync_wrapper
    return decorate
