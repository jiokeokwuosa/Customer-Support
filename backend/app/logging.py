"""Structured logging helpers (structlog).

Bind turn context once per request/step so logs include session_id, turn_id,
step name, and optional latency_ms without repeating fields in every call.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

import structlog
from structlog.typing import FilteringBoundLogger

_log_context: ContextVar[dict[str, Any] | None] = ContextVar(
    "log_context",
    default=None,
)


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog for JSON-friendly structured output."""
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper(), logging.INFO),
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _merge_bound_context,  # type: ignore[list-item]
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO),
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _merge_bound_context(
    _logger: logging.Logger,
    _method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    bound = _log_context.get() or {}
    if bound:
        event_dict = {**bound, **event_dict}
    return event_dict


def get_logger(name: str) -> FilteringBoundLogger:
    return structlog.get_logger(name)  # type: ignore[no-any-return]


def bind_log_context(**fields: Any) -> None:
    """Add fields included on every log until cleared or replaced."""
    current = (_log_context.get() or {}).copy()
    current.update(fields)
    _log_context.set(current)


def clear_log_context() -> None:
    _log_context.set(None)


def log_event(logger: FilteringBoundLogger, event: str, **fields: Any) -> None:
    logger.info(event, **fields)


@contextmanager
def log_step(
    logger: FilteringBoundLogger,
    *,
    step: str,
    **fields: Any,
) -> Iterator[None]:
    """Log step start/end with latency_ms."""
    started = time.perf_counter()
    log_event(logger, "step_started", step=step, **fields)
    try:
        yield
    except Exception:
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        log_event(
            logger,
            "step_failed",
            step=step,
            latency_ms=latency_ms,
            **fields,
        )
        raise
    else:
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        log_event(
            logger,
            "step_completed",
            step=step,
            latency_ms=latency_ms,
            **fields,
        )
