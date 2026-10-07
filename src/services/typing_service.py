"""
TypeRead Typing Session Service
Coordinates in-memory keystroke evaluation, session state transitions,
weak-key updates, and crash-resilient persistence.
"""

from __future__ import annotations
import uuid
from typing import Dict, Optional, List

from src.contracts.types import (
    TypingSessionEntity,
    StartSessionRequest,
    SubmitKeystrokesRequest,
    SetSessionStateRequest,
    KeystrokeBatchResult,
    TypingSessionState,
    TypingMode,
    ErrorHandlingMode,
    SessionId,
    UserId,
    DocumentId,
    ChapterId,
    SectionId,
    ParagraphId,
    ReadingPositionPointer,
    ErrorCode,
)
from src.core.errors import AppErrorException
from src.core.typing.session import TypingSessionManager
from src.core.practice.weak_keys import WeakKeyAggregator
from src.storage.repositories.document_repo import DocumentRepository
from src.storage.repositories.session_repo import SessionRepository
from src.storage.repositories.progress_repo import ProgressRepository
from src.storage.repositories.analytics_repo import AnalyticsRepository


class TypingSessionService:
    def __init__(
        self,
        doc_repo: DocumentRepository,
        session_repo: SessionRepository,
        progress_repo: ProgressRepository,
        analytics_repo: AnalyticsRepository,
    ):
        self.doc_repo = doc_repo
        self.session_repo = session_repo
        self.progress_repo = progress_repo
        self.analytics_repo = analytics_repo

        # Active session managers held in-memory for sub-50ms keystroke execution
        self._active_sessions: Dict[str, TypingSessionManager] = {}

    def start_session(self, request: StartSessionRequest, user_id: str = "default_user") -> TypingSessionEntity:
        # Check document and section exist
        content = self.doc_repo.get_section_content(request.documentId, request.sectionId)
        if not content:
            raise AppErrorException.not_found(
                code=ErrorCode.SECTION_NOT_FOUND,
                message=f"Section {request.sectionId} not found in document {request.documentId}",
                field="sectionId",
            )

        # Assemble typing target text from section paragraphs
        target_text = "\n\n".join(p.typingText for p in content.paragraphs)
        if not target_text:
            raise AppErrorException.bad_request(
                code=ErrorCode.EMPTY_DOCUMENT,
                message="Section contains no typing text",
            )

        session_id = SessionId(str(uuid.uuid4()))
        error_mode = request.errorHandlingMode or ErrorHandlingMode.ALLOW_WITH_BACKSPACE

        manager = TypingSessionManager(
            session_id=session_id,
            user_id=UserId(user_id),
            document_id=DocumentId(request.documentId),
            chapter_id=ChapterId(request.chapterId),
            section_id=SectionId(request.sectionId),
            target_text=target_text,
            typing_mode=request.typingMode,
            error_handling_mode=error_mode,
        )

        self._active_sessions[str(session_id)] = manager
        entity = manager.to_entity()
        self.session_repo.save_session(entity)
        return entity

    def submit_keystrokes(self, session_id: str, request: SubmitKeystrokesRequest) -> KeystrokeBatchResult:
        manager = self._get_manager(session_id)
        result = manager.process_keystrokes(request.keystrokes)

        # Update persisted session snapshot
        entity = manager.to_entity()
        self.session_repo.save_session(entity)

        # If completed, finalize analytics and progress
        if entity.completed:
            self._finalize_session(manager)

        return result

    def set_session_state(self, session_id: str, request: SetSessionStateRequest) -> TypingSessionEntity:
        manager = self._get_manager(session_id)
        target_state = TypingSessionState(request.state)
        manager.set_state(target_state)

        entity = manager.to_entity()
        self.session_repo.save_session(entity)
        return entity

    def complete_session(self, session_id: str) -> TypingSessionEntity:
        manager = self._get_manager(session_id)
        entity = manager.complete()
        self._finalize_session(manager)
        return entity

    def abort_session(self, session_id: str) -> TypingSessionEntity:
        manager = self._get_manager(session_id)
        entity = manager.abort()
        self._finalize_session(manager)
        return entity

    def get_active_session(self, user_id: str = "default_user") -> Optional[TypingSessionEntity]:
        # First check in-memory sessions
        for s_id, manager in self._active_sessions.items():
            if str(manager.user_id) == user_id and manager.state in (TypingSessionState.ACTIVE, TypingSessionState.READY, TypingSessionState.PAUSED):
                return manager.to_entity()

        # Check database for recovery
        return self.session_repo.get_active_session(user_id=user_id)

    def _get_manager(self, session_id: str) -> TypingSessionManager:
        if session_id in self._active_sessions:
            return self._active_sessions[session_id]

        # Try recovering from DB
        entity = self.session_repo.get_session_by_id(session_id)
        if not entity:
            raise AppErrorException.not_found(
                code=ErrorCode.SESSION_NOT_FOUND,
                message=f"Session {session_id} not found",
                field="sessionId",
            )

        content = self.doc_repo.get_section_content(str(entity.document_id), str(entity.section_id))
        target_text = "\n\n".join(p.typingText for p in content.paragraphs) if content else ""

        manager = TypingSessionManager(
            session_id=entity.id,
            user_id=entity.user_id,
            document_id=entity.document_id,
            chapter_id=entity.chapter_id,
            section_id=entity.section_id,
            target_text=target_text,
            typing_mode=entity.typing_mode,
            error_handling_mode=ErrorHandlingMode.ALLOW_WITH_BACKSPACE,
        )
        self._active_sessions[session_id] = manager
        return manager

    def _finalize_session(self, manager: TypingSessionManager) -> None:
        entity = manager.to_entity()
        self.session_repo.save_session(entity)

        # Save errors
        if manager.error_records:
            self.session_repo.save_errors(manager.error_records, user_id=str(entity.user_id))

            # Aggregate weak keys and bigrams
            char_totals = {c: manager.target_text.count(c) for c in set(manager.target_text)}
            bg_totals = {}
            for i in range(len(manager.target_text) - 1):
                bg = manager.target_text[i:i+2]
                bg_totals[bg] = bg_totals.get(bg, 0) + 1

            weak_keys, weak_bigrams = WeakKeyAggregator.aggregate_errors(
                errors=manager.error_records,
                character_totals=char_totals,
                bigram_totals=bg_totals,
            )
            self.analytics_repo.update_weak_keys_and_bigrams(
                user_id=str(entity.user_id),
                weak_keys=weak_keys,
                weak_bigrams=weak_bigrams,
            )

        # Update daily streak
        self.analytics_repo.record_daily_streak(
            user_id=str(entity.user_id),
            active_seconds=entity.metrics.active_seconds,
            chars_typed=entity.metrics.total_keystrokes,
        )

        # Update reading progress pointer
        content = self.doc_repo.get_section_content(str(entity.document_id), str(entity.section_id))
        para_id = content.paragraphs[0].id if content and content.paragraphs else "p_0"
        pointer = ReadingPositionPointer(
            document_id=entity.document_id,
            chapter_id=entity.chapter_id,
            section_id=entity.section_id,
            paragraph_id=ParagraphId(para_id),
            character_offset=manager.current_position,
        )
        self.progress_repo.update_position(user_id=str(entity.user_id), pointer=pointer)
