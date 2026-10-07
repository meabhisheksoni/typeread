"""
TypeRead Typing Session & Errors Repository
Persists typing sessions, live status, and character-level error telemetry.
"""

from __future__ import annotations
from typing import List, Optional, Any

from src.contracts.types import (
    TypingSessionEntity,
    TypingSessionState,
    TypingMode,
    TypingMetrics,
    TypingErrorRecord,
    SessionId,
    UserId,
    DocumentId,
    ChapterId,
    SectionId,
)
from src.storage.db import Database


class SessionRepository:
    def __init__(self, db: Database):
        self.db = db

    def save_session(self, session: TypingSessionEntity) -> None:
        m = session.metrics
        with self.db.transaction() as cur:
            cur.execute(
                """
                INSERT OR REPLACE INTO typing_sessions (
                    id, user_id, document_id, chapter_id, section_id, start_time, end_time,
                    state, session_mode, active_seconds, total_characters, correct_characters,
                    incorrect_characters, backspaces, net_wpm, gross_wpm, accuracy_pct,
                    consistency_pct, completed, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    session.id,
                    session.user_id,
                    session.document_id,
                    session.chapter_id,
                    session.section_id,
                    session.start_time,
                    session.end_time,
                    session.state.value,
                    session.typing_mode.value,
                    m.active_seconds,
                    m.total_keystrokes,
                    m.correct_keystrokes,
                    m.incorrect_keystrokes,
                    m.backspace_count,
                    m.net_wpm,
                    m.gross_wpm,
                    m.accuracy_pct,
                    m.consistency_pct,
                    1 if session.completed else 0,
                    session.created_at,
                ),
            )

    def get_session_by_id(self, session_id: str) -> Optional[TypingSessionEntity]:
        with self.db.cursor() as cur:
            cur.execute("SELECT * FROM typing_sessions WHERE id = ?;", (session_id,))
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_session_entity(row)

    def get_active_session(self, user_id: str = "default_user") -> Optional[TypingSessionEntity]:
        with self.db.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM typing_sessions 
                WHERE user_id = ? AND state IN ('active', 'paused') AND completed = 0
                ORDER BY start_time DESC LIMIT 1;
                """,
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_session_entity(row)

    def save_errors(self, errors: List[TypingErrorRecord], user_id: str = "default_user") -> None:
        if not errors:
            return
        with self.db.transaction() as cur:
            for err in errors:
                cur.execute(
                    """
                    INSERT OR REPLACE INTO typing_errors (
                        id, session_id, user_id, document_id, section_id,
                        expected_character, actual_character, character_position,
                        timestamp_ms, resolved_via_backspace
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        err.id,
                        err.session_id,
                        user_id,
                        err.document_id,
                        err.section_id,
                        err.expected_char,
                        err.actual_char,
                        err.position,
                        err.timestamp_ms,
                        1 if err.resolved_via_backspace else 0,
                    ),
                )

    def get_errors_by_session(self, session_id: str) -> List[TypingErrorRecord]:
        errors: List[TypingErrorRecord] = []
        with self.db.cursor() as cur:
            cur.execute("SELECT * FROM typing_errors WHERE session_id = ?;", (session_id,))
            for r in cur.fetchall():
                errors.append(
                    TypingErrorRecord(
                        id=r["id"],
                        session_id=r["session_id"],
                        document_id=r["document_id"],
                        section_id=r["section_id"],
                        expected_char=r["expected_character"],
                        actual_char=r["actual_character"],
                        position=r["character_position"],
                        timestamp_ms=r["timestamp_ms"],
                        resolved_via_backspace=bool(r["resolved_via_backspace"]),
                    )
                )
        return errors

    def get_errors_by_user(self, user_id: str = "default_user") -> List[TypingErrorRecord]:
        errors: List[TypingErrorRecord] = []
        with self.db.cursor() as cur:
            cur.execute("SELECT * FROM typing_errors WHERE user_id = ?;", (user_id,))
            for r in cur.fetchall():
                errors.append(
                    TypingErrorRecord(
                        id=r["id"],
                        session_id=r["session_id"],
                        document_id=r["document_id"],
                        section_id=r["section_id"],
                        expected_char=r["expected_character"],
                        actual_char=r["actual_character"],
                        position=r["character_position"],
                        timestamp_ms=r["timestamp_ms"],
                        resolved_via_backspace=bool(r["resolved_via_backspace"]),
                    )
                )
        return errors

    @staticmethod
    def _row_to_session_entity(r: Any) -> TypingSessionEntity:
        metrics = TypingMetrics(
            net_wpm=r["net_wpm"],
            gross_wpm=r["gross_wpm"],
            accuracy_pct=r["accuracy_pct"],
            error_rate_pct=round(100.0 - r["accuracy_pct"], 2),
            total_keystrokes=r["total_characters"],
            correct_keystrokes=r["correct_characters"],
            incorrect_keystrokes=r["incorrect_characters"],
            backspace_count=r["backspaces"],
            active_seconds=r["active_seconds"],
            consistency_pct=r["consistency_pct"],
        )
        return TypingSessionEntity(
            id=r["id"],
            user_id=r["user_id"],
            document_id=r["document_id"],
            chapter_id=r["chapter_id"],
            section_id=r["section_id"],
            start_time=r["start_time"],
            state=TypingSessionState(r["state"]),
            typing_mode=TypingMode(r["session_mode"]),
            metrics=metrics,
            completed=bool(r["completed"]),
            created_at=r["created_at"],
            end_time=r["end_time"],
        )
