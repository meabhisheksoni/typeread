"""
TypeRead Notes Repository
CRUD operations for user study notes.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from src.contracts.types import (
    NoteEntity,
    CreateNoteRequest,
    NoteId,
    UserId,
    DocumentId,
    ChapterId,
    SectionId,
    ParagraphId,
    ErrorCode,
)
from src.core.errors import AppErrorException
from src.storage.db import Database


class NoteRepository:
    def __init__(self, db: Database):
        self.db = db

    def list_notes(self, user_id: str = "default_user", document_id: Optional[str] = None) -> List[NoteEntity]:
        notes: List[NoteEntity] = []
        with self.db.cursor() as cur:
            if document_id:
                cur.execute(
                    "SELECT * FROM notes WHERE user_id = ? AND document_id = ? ORDER BY created_at DESC;",
                    (user_id, document_id),
                )
            else:
                cur.execute("SELECT * FROM notes WHERE user_id = ? ORDER BY created_at DESC;", (user_id,))

            for r in cur.fetchall():
                notes.append(
                    NoteEntity(
                        id=NoteId(r["id"]),
                        user_id=UserId(r["user_id"]),
                        document_id=DocumentId(r["document_id"]),
                        chapter_id=ChapterId(r["chapter_id"]),
                        section_id=SectionId(r["section_id"]),
                        paragraph_id=ParagraphId(r["paragraph_id"]),
                        content=r["content"],
                        created_at=r["created_at"],
                        updated_at=r["updated_at"],
                    )
                )
        return notes

    def create_note(self, user_id: str, req: CreateNoteRequest) -> NoteEntity:
        # Validate existence of document
        with self.db.cursor() as cur:
            cur.execute("SELECT id FROM documents WHERE id = ?;", (req.documentId,))
            if not cur.fetchone():
                raise AppErrorException.not_found(
                    code=ErrorCode.DOCUMENT_NOT_FOUND,
                    message=f"Document {req.documentId} not found",
                    field="documentId",
                )

        n_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        with self.db.transaction() as cur:
            cur.execute(
                """
                INSERT INTO notes (
                    id, user_id, document_id, chapter_id, section_id, paragraph_id,
                    content, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    n_id,
                    user_id,
                    req.documentId,
                    req.chapterId,
                    req.sectionId,
                    req.paragraphId,
                    req.content,
                    now_iso,
                    now_iso,
                ),
            )

        return NoteEntity(
            id=NoteId(n_id),
            user_id=UserId(user_id),
            document_id=DocumentId(req.documentId),
            chapter_id=ChapterId(req.chapterId),
            section_id=SectionId(req.sectionId),
            paragraph_id=ParagraphId(req.paragraphId),
            content=req.content,
            created_at=now_iso,
            updated_at=now_iso,
        )

    def update_note(self, user_id: str, note_id: str, content: str) -> NoteEntity:
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.db.transaction() as cur:
            cur.execute(
                """
                UPDATE notes 
                SET content = ?, updated_at = ?
                WHERE id = ? AND user_id = ?;
                """,
                (content, now_iso, note_id, user_id),
            )
            if cur.rowcount == 0:
                raise AppErrorException.not_found(
                    code=ErrorCode.DOCUMENT_NOT_FOUND,
                    message=f"Note {note_id} not found",
                    field="noteId",
                )

        # Retrieve updated
        with self.db.cursor() as cur:
            cur.execute("SELECT * FROM notes WHERE id = ?;", (note_id,))
            r = cur.fetchone()
            return NoteEntity(
                id=NoteId(r["id"]),
                user_id=UserId(r["user_id"]),
                document_id=DocumentId(r["document_id"]),
                chapter_id=ChapterId(r["chapter_id"]),
                section_id=SectionId(r["section_id"]),
                paragraph_id=ParagraphId(r["paragraph_id"]),
                content=r["content"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )

    def delete_note(self, user_id: str, note_id: str) -> bool:
        with self.db.transaction() as cur:
            cur.execute("DELETE FROM notes WHERE id = ? AND user_id = ?;", (note_id, user_id))
            if cur.rowcount == 0:
                raise AppErrorException.not_found(
                    code=ErrorCode.DOCUMENT_NOT_FOUND,
                    message=f"Note {note_id} not found",
                    field="noteId",
                )
            return True
