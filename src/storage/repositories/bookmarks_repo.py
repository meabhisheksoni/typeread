"""
TypeRead Bookmarks Repository
CRUD operations for reading and practice bookmarks.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from src.contracts.types import (
    BookmarkEntity,
    CreateBookmarkRequest,
    BookmarkId,
    UserId,
    DocumentId,
    ChapterId,
    SectionId,
    ParagraphId,
    ErrorCode,
)
from src.core.errors import AppErrorException
from src.storage.db import Database


class BookmarkRepository:
    def __init__(self, db: Database):
        self.db = db

    def list_bookmarks(self, user_id: str = "default_user", document_id: Optional[str] = None) -> List[BookmarkEntity]:
        bookmarks: List[BookmarkEntity] = []
        with self.db.cursor() as cur:
            if document_id:
                cur.execute(
                    "SELECT * FROM bookmarks WHERE user_id = ? AND document_id = ? ORDER BY created_at DESC;",
                    (user_id, document_id),
                )
            else:
                cur.execute(
                    "SELECT * FROM bookmarks WHERE user_id = ? ORDER BY created_at DESC;",
                    (user_id,),
                )

            for r in cur.fetchall():
                bookmarks.append(
                    BookmarkEntity(
                        id=BookmarkId(r["id"]),
                        user_id=UserId(r["user_id"]),
                        document_id=DocumentId(r["document_id"]),
                        chapter_id=ChapterId(r["chapter_id"]),
                        section_id=SectionId(r["section_id"]),
                        paragraph_id=ParagraphId(r["paragraph_id"]),
                        character_offset=r["character_offset"],
                        title=r["title"],
                        created_at=r["created_at"],
                        note_snippet=r["note_snippet"],
                    )
                )
        return bookmarks

    def create_bookmark(self, user_id: str, req: CreateBookmarkRequest) -> BookmarkEntity:
        # Validate existence of document, chapter, section, paragraph
        with self.db.cursor() as cur:
            cur.execute("SELECT id FROM documents WHERE id = ?;", (req.documentId,))
            if not cur.fetchone():
                raise AppErrorException.not_found(
                    code=ErrorCode.DOCUMENT_NOT_FOUND,
                    message=f"Document {req.documentId} not found",
                    field="documentId",
                )

        b_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        with self.db.transaction() as cur:
            cur.execute(
                """
                INSERT INTO bookmarks (
                    id, user_id, document_id, chapter_id, section_id, paragraph_id,
                    character_offset, title, note_snippet, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    b_id,
                    user_id,
                    req.documentId,
                    req.chapterId,
                    req.sectionId,
                    req.paragraphId,
                    req.characterOffset,
                    req.title,
                    req.noteSnippet,
                    now_iso,
                ),
            )

        return BookmarkEntity(
            id=BookmarkId(b_id),
            user_id=UserId(user_id),
            document_id=DocumentId(req.documentId),
            chapter_id=ChapterId(req.chapterId),
            section_id=SectionId(req.sectionId),
            paragraph_id=ParagraphId(req.paragraphId),
            character_offset=req.characterOffset,
            title=req.title,
            created_at=now_iso,
            note_snippet=req.noteSnippet,
        )

    def delete_bookmark(self, user_id: str, bookmark_id: str) -> bool:
        with self.db.transaction() as cur:
            cur.execute("DELETE FROM bookmarks WHERE id = ? AND user_id = ?;", (bookmark_id, user_id))
            if cur.rowcount == 0:
                raise AppErrorException.not_found(
                    code=ErrorCode.DOCUMENT_NOT_FOUND,
                    message=f"Bookmark {bookmark_id} not found",
                    field="bookmarkId",
                )
            return True
