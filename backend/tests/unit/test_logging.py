import json

import pytest
import structlog

from app.logging import (
    bind_log_context,
    clear_log_context,
    configure_logging,
    get_logger,
    log_step,
)


@pytest.fixture(autouse=True)
def reset_logging(capsys: pytest.CaptureFixture[str]) -> None:
    clear_log_context()
    structlog.reset_defaults()
    yield
    clear_log_context()
    structlog.reset_defaults()
    capsys.readouterr()


def test_log_step_emits_started_and_completed_with_latency(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging("INFO")
    logger = get_logger("test")
    bind_log_context(session_id="sess-1", turn_id="turn-1")

    with log_step(logger, step="triage"):
        pass

    output = capsys.readouterr().out.strip().splitlines()
    assert len(output) == 2

    started = json.loads(output[0])
    completed = json.loads(output[1])

    assert started["event"] == "step_started"
    assert started["step"] == "triage"
    assert started["session_id"] == "sess-1"
    assert started["turn_id"] == "turn-1"

    assert completed["event"] == "step_completed"
    assert completed["step"] == "triage"
    assert "latency_ms" in completed
    assert completed["latency_ms"] >= 0


def test_log_step_emits_failed_on_exception(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging("INFO")
    logger = get_logger("test")

    with pytest.raises(RuntimeError), log_step(logger, step="draft"):
        raise RuntimeError("boom")

    output = capsys.readouterr().out.strip().splitlines()
    failed = json.loads(output[-1])
    assert failed["event"] == "step_failed"
    assert failed["step"] == "draft"
