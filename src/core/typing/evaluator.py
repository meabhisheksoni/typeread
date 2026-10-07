"""
TypeRead Keystroke Evaluator
Immediate in-memory evaluation of keyboard input (<50ms latency invariant).
"""

from __future__ import annotations
from typing import Optional

from src.contracts.types import (
    KeystrokeInput,
    KeystrokeEvaluation,
    ErrorHandlingMode,
    ErrorCode,
)
from src.core.errors import AppErrorException


class KeystrokeEvaluator:
    def __init__(
        self,
        target_text: str,
        error_handling_mode: ErrorHandlingMode = ErrorHandlingMode.ALLOW_WITH_BACKSPACE,
    ):
        self.target_text = target_text
        self.error_handling_mode = error_handling_mode
        self._last_keystroke_timestamp_ms: Optional[int] = None

    def evaluate(self, stroke: KeystrokeInput) -> KeystrokeEvaluation:
        # Validate position
        pos = stroke.position

        # Compute latency
        latency_ms = 0
        if self._last_keystroke_timestamp_ms is not None and stroke.timestamp_ms >= self._last_keystroke_timestamp_ms:
            latency_ms = stroke.timestamp_ms - self._last_keystroke_timestamp_ms
        self._last_keystroke_timestamp_ms = stroke.timestamp_ms

        if stroke.is_backspace:
            return KeystrokeEvaluation(
                position=pos,
                expected_char=self.target_text[pos] if 0 <= pos < len(self.target_text) else "",
                actual_key="Backspace",
                is_correct=True,
                is_backspace=True,
                timestamp_ms=stroke.timestamp_ms,
                latency_ms=latency_ms,
            )

        if pos < 0 or pos >= len(self.target_text):
            raise AppErrorException.bad_request(
                code=ErrorCode.POSITION_OUT_OF_BOUNDS,
                message=f"Keystroke position {pos} out of text bounds [0, {len(self.target_text)})",
                field="position",
            )

        expected = self.target_text[pos]
        actual = stroke.key

        is_correct = (actual == expected)

        return KeystrokeEvaluation(
            position=pos,
            expected_char=expected,
            actual_key=actual,
            is_correct=is_correct,
            is_backspace=False,
            timestamp_ms=stroke.timestamp_ms,
            latency_ms=latency_ms,
        )
