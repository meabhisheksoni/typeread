"""
TypeRead Reading Progress & Resume Pointer Repository
Tracks exact document coordinates and completion percentage.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, Any

from src.contracts.types import (
    ReadingProgressEntity,
    ReadingPositionPointer,
    UserId,
    DocumentId,
    ChapterId,
    SectionId,
    ParagraphId,
    ErrorCode,
)
from src.core.errors import AppErrorException
from src.storage.db import Database


class ProgressRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_progress(self, user_id: str, document_id: str) -> Optional[ReadingProgressEntity]:
        with self.db.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM reading_progress 
                WHERE user_id = ? AND document_id = ?;
                """,
                (user_id, document_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_progress_entity(row)

    def save_progress(self, progress: ReadingProgressEntity) -> None:
        p = progress.position
        with self.db.transaction() as cur:
            cur.execute(
                """
                INSERT OR REPLACE INTO reading_progress (
                    id, user_id, document_id, chapter_id, section_id, paragraph_id,
                    character_offset, completion_percentage, is_completed, last_practiced_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    progress.id,
                    progress.user_id,
                    progress.document_id,
                    p.chapter_id,
                    p.section_id,
                    p.paragraph_id,
                    p.character_offset,
                    progress.completion_percentage,
                    1 if progress.is_completed else 0,
                    progress.last_practiced_at,
                    progress.updated_at,
                ),
            )

    def update_position(self, user_id: str, pointer: ReadingPositionPointer) -> ReadingProgressEntity:
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.db.transaction() as cur:
            # Check document exists
            cur.execute("SELECT character_count FROM documents WHERE id = ?;", (pointer.document_id,))
            doc_row = cur.fetchone()
            if not doc_row:
                raise AppErrorException.not_found(
                    code=ErrorCode.DOCUMENT_NOT_FOUND,
                    message=f"Document {pointer.document_id} not found",
                    field="documentId",
                )

            total_chars = max(1, doc_row["character_count"])

            # Calculate character progress up to current paragraph + offset
            cur.execute(
                """
                SELECT COALESCE(SUM(LENGTH(display_text)), 0) as prior_chars
                FROM paragraphs
                WHERE document_id = ? AND (
                    order_index < (SELECT order_index FROM paragraphs WHERE id = ?)
                );
                """,
                (pointer.document_id, pointer.paragraph_id),
            )
            prior_row = cur.fetchone()
            prior_chars = prior_row["prior_chars"] if prior_row else 0
            current_total_chars = prior_chars + pointer.character_offset

            completion_pct = min(100.0, max(0.0, round((current_total_chars / float(total_chars)) * 100.0, 2)))
            is_completed = completion_pct >= 99.5

            prog_id = f"prog_{pointer.document_id}"
            cur.execute(
                """
                INSERT OR REPLACE INTO reading_progress (
                    id, user_id, document_id, chapter_id, section_id, paragraph_id,
                    character_offset, completion_percentage, is_completed, last_practiced_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    prog_id,
                    user_id,
                    pointer.document_id,
                    pointer.chapter_id,
                    pointer.section_id,
                    pointer.paragraph_id,
                    pointer.character_offset,
                    completion_pct,
                    1 if is_completed else 0,
                    now_iso,
                    now_iso,
                ),
            )

            return ReadingProgressEntity(
                id=prog_id,
                user_id=UserId(user_id),
                document_id=pointer.document_id,
                position=pointer,
                completion_percentage=completion_pct,
                is_completed=is_completed,
                last_practiced_at=now_iso,
                updated_at=now_iso,
            )

    @staticmethod
    def _row_to_progress_entity(r: Any) -> ReadingProgressEntity:
        pointer = ReadingPositionPointer(
            document_id=r["document_id"],
            chapter_id=r["chapter_id"],
            section_id=r["section_id"],
            paragraph_id=r["paragraph_id"],
            character_offset=r["character_offset"],
        )
        return ReadingProgressEntity(
            id=r["id"],
            user_id=r["user_id"],
            document_id=r["document_id"],
            position=pointer,
            completion_percentage=r["completion_percentage"],
            is_completed=bool(r["is_completed"]),
            last_practiced_at=r["last_practiced_at"],
            updated_at=r["updated_at"],
        )
