"""
Unit tests for the typing engine, keystroke evaluator, metrics calculator, and session state machine.
"""

import pytest
from src.contracts.types import (
    KeystrokeInput,
    TypingMode,
    ErrorHandlingMode,
    TypingSessionState,
    SessionId,
    UserId,
    DocumentId,
    ChapterId,
    SectionId,
)
from src.core.typing.evaluator import KeystrokeEvaluator
from src.core.typing.metrics import MetricsCalculator
from src.core.typing.session import TypingSessionManager


def test_keystroke_evaluator():
    target = "Hello"
    evaluator = KeystrokeEvaluator(target_text=target)

    # Correct stroke
    s1 = KeystrokeInput(timestamp_ms=1000, key="H", expected_char="H", position=0, is_backspace=False)
    e1 = evaluator.evaluate(s1)
    assert e1.is_correct is True
    assert e1.latency_ms == 0

    # Incorrect stroke
    s2 = KeystrokeInput(timestamp_ms=1200, key="a", expected_char="e", position=1, is_backspace=False)
    e2 = evaluator.evaluate(s2)
    assert e2.is_correct is False
    assert e2.latency_ms == 200

    # Backspace
    s3 = KeystrokeInput(timestamp_ms=1300, key="Backspace", expected_char="e", position=1, is_backspace=True)
    e3 = evaluator.evaluate(s3)
    assert e3.is_backspace is True


def test_metrics_calculator_formulas():
    calc = MetricsCalculator()

    # Simulate 25 correct characters typed over 5 seconds (60 WPM)
    # 25 characters = 5 words. 5 words / (5 / 60) mins = 60 WPM
    t = 1000
    for i in range(25):
        s = KeystrokeInput(timestamp_ms=t, key="a", expected_char="a", position=i, is_backspace=False)
        e = KeystrokeEvaluator("a" * 50).evaluate(s)
        calc.add_evaluation(e)
        t += 200  # 200ms per character -> 25 * 0.2s = 5s

    metrics = calc.compute_metrics()
    assert metrics.correct_keystrokes == 25
    assert metrics.incorrect_keystrokes == 0
    assert metrics.accuracy_pct == 100.0
    assert metrics.error_rate_pct == 0.0
    assert metrics.gross_wpm > 50.0
    assert metrics.net_wpm > 50.0
    assert metrics.consistency_pct >= 90.0


def test_typing_session_manager_lifecycle():
    target = "TypeRead"
    manager = TypingSessionManager(
        session_id=SessionId("sess_1"),
        user_id=UserId("u_1"),
        document_id=DocumentId("d_1"),
        chapter_id=ChapterId("c_1"),
        section_id=SectionId("s_1"),
        target_text=target,
    )
    assert manager.state == TypingSessionState.READY

    # First keystroke transitions to ACTIVE
    stroke = KeystrokeInput(timestamp_ms=1000, key="T", expected_char="T", position=0, is_backspace=False)
    batch = manager.process_keystrokes([stroke])
    assert manager.state == TypingSessionState.ACTIVE
    assert batch.currentPosition == 1

    # Pause and resume
    manager.set_state(TypingSessionState.PAUSED)
    assert manager.state == TypingSessionState.PAUSED
    manager.set_state(TypingSessionState.ACTIVE)
    assert manager.state == TypingSessionState.ACTIVE

    # Complete
    entity = manager.complete()
    assert entity.completed is True
    assert entity.state == TypingSessionState.COMPLETED
    assert entity.end_time is not None


def test_stop_on_error_mode():
    target = "abc"
    manager = TypingSessionManager(
        session_id=SessionId("sess_2"),
        user_id=UserId("u_1"),
        document_id=DocumentId("d_1"),
        chapter_id=ChapterId("c_1"),
        section_id=SectionId("s_1"),
        target_text=target,
        error_handling_mode=ErrorHandlingMode.STOP_ON_ERROR,
    )
    # Incorrect stroke
    stroke_bad = KeystrokeInput(timestamp_ms=1000, key="x", expected_char="a", position=0, is_backspace=False)
    batch = manager.process_keystrokes([stroke_bad])
    # Position must NOT advance in STOP_ON_ERROR mode
    assert batch.currentPosition == 0
    assert len(manager.error_records) == 1
