"""
TypeRead Typing Session State Machine & Manager
Enforces session transitions: READY -> ACTIVE <-> PAUSED -> COMPLETED / ABORTED
Coordinates KeystrokeEvaluator, MetricsCalculator, and error logging.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from src.contracts.types import (
    SessionId,
    UserId,
    DocumentId,
    ChapterId,
    SectionId,
    TypingSessionState,
    TypingMode,
    ErrorHandlingMode,
    TypingSessionEntity,
    TypingMetrics,
    KeystrokeInput,
    KeystrokeEvaluation,
    KeystrokeBatchResult,
    TypingErrorRecord,
    ErrorCode,
)
from src.core.errors import AppErrorException
from src.core.typing.evaluator import KeystrokeEvaluator
from src.core.typing.metrics import MetricsCalculator


class TypingSessionManager:
    def __init__(
        self,
        session_id: SessionId,
        user_id: UserId,
        document_id: DocumentId,
        chapter_id: ChapterId,
        section_id: SectionId,
        target_text: str,
        typing_mode: TypingMode = TypingMode.STANDARD,
        error_handling_mode: ErrorHandlingMode = ErrorHandlingMode.ALLOW_WITH_BACKSPACE,
        start_position: int = 0,
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.document_id = document_id
        self.chapter_id = chapter_id
        self.section_id = section_id
        self.target_text = target_text
        self.typing_mode = typing_mode
        self.error_handling_mode = error_handling_mode

        self.state = TypingSessionState.READY
        self.start_time = datetime.now(timezone.utc).isoformat()
        self.end_time: Optional[str] = None
        self.completed = False

        self.current_position = start_position
        self.evaluator = KeystrokeEvaluator(target_text=target_text, error_handling_mode=error_handling_mode)
        self.metrics_calculator = MetricsCalculator()
        self.error_records: List[TypingErrorRecord] = []
        self._unresolved_errors: List[TypingErrorRecord] = []

    def set_state(self, new_state: TypingSessionState) -> None:
        if self.state in (TypingSessionState.COMPLETED, TypingSessionState.ABORTED):
            raise AppErrorException.conflict(
                code=ErrorCode.SESSION_ALREADY_FINISHED,
                message=f"Session is already finalized in state '{self.state.value}'",
            )

        if new_state == TypingSessionState.ACTIVE:
            self.state = TypingSessionState.ACTIVE
        elif new_state == TypingSessionState.PAUSED:
            if self.state == TypingSessionState.ACTIVE:
                self.state = TypingSessionState.PAUSED
        elif new_state == TypingSessionState.COMPLETED:
            self.complete()
        elif new_state == TypingSessionState.ABORTED:
            self.abort()

    def process_keystrokes(self, keystrokes: List[KeystrokeInput]) -> KeystrokeBatchResult:
        if self.state in (TypingSessionState.COMPLETED, TypingSessionState.ABORTED):
            raise AppErrorException.conflict(
                code=ErrorCode.SESSION_ALREADY_FINISHED,
                message=f"Cannot submit keystrokes to a {self.state.value} session",
            )

        if self.state == TypingSessionState.READY and keystrokes:
            self.state = TypingSessionState.ACTIVE

        evaluations: List[KeystrokeEvaluation] = []

        for stroke in keystrokes:
            eval_res = self.evaluator.evaluate(stroke)
            evaluations.append(eval_res)
            self.metrics_calculator.add_evaluation(eval_res)

            if eval_res.is_backspace:
                if self.current_position > 0:
                    self.current_position -= 1
                    # Check if resolving an earlier error
                    if self._unresolved_errors:
                        last_err = self._unresolved_errors.pop()
                        resolved_err = TypingErrorRecord(
                            id=last_err.id,
                            session_id=last_err.session_id,
                            document_id=last_err.document_id,
                            section_id=last_err.section_id,
                            expected_char=last_err.expected_char,
                            actual_char=last_err.actual_char,
                            position=last_err.position,
                            timestamp_ms=last_err.timestamp_ms,
                            resolved_via_backspace=True,
                        )
                        # Update in error records
                        for idx, e in enumerate(self.error_records):
                            if e.id == last_err.id:
                                self.error_records[idx] = resolved_err
                                break
            else:
                if eval_res.is_correct:
                    self.current_position += 1
                else:
                    # Record error
                    err_record = TypingErrorRecord(
                        id=str(uuid.uuid4()),
                        session_id=self.session_id,
                        document_id=self.document_id,
                        section_id=self.section_id,
                        expected_char=eval_res.expected_char,
                        actual_char=eval_res.actual_key,
                        position=eval_res.position,
                        timestamp_ms=eval_res.timestamp_ms,
                        resolved_via_backspace=False,
                    )
                    self.error_records.append(err_record)
                    self._unresolved_errors.append(err_record)

                    # In STOP_ON_ERROR mode, cursor does not advance on incorrect key
                    if self.error_handling_mode != ErrorHandlingMode.STOP_ON_ERROR:
                        self.current_position += 1

            # Check for completion
            if self.current_position >= len(self.target_text):
                self.complete()

        current_metrics = self.metrics_calculator.compute_metrics()
        return KeystrokeBatchResult(
            evaluations=evaluations,
            currentMetrics=current_metrics,
            currentPosition=self.current_position,
        )

    def complete(self) -> TypingSessionEntity:
        self.state = TypingSessionState.COMPLETED
        self.completed = True
        self.end_time = datetime.now(timezone.utc).isoformat()
        return self.to_entity()

    def abort(self) -> TypingSessionEntity:
        self.state = TypingSessionState.ABORTED
        self.completed = False
        self.end_time = datetime.now(timezone.utc).isoformat()
        return self.to_entity()

    def to_entity(self) -> TypingSessionEntity:
        metrics = self.metrics_calculator.compute_metrics()
        return TypingSessionEntity(
            id=self.session_id,
            user_id=self.user_id,
            document_id=self.document_id,
            chapter_id=self.chapter_id,
            section_id=self.section_id,
            start_time=self.start_time,
            state=self.state,
            typing_mode=self.typing_mode,
            metrics=metrics,
            completed=self.completed,
            created_at=self.start_time,
            end_time=self.end_time,
        )
