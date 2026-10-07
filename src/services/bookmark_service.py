"""
TypeRead Bookmark Service
Manages bookmarks and progress points.
"""

from __future__ import annotations
from typing import List, Optional

from src.contracts.types import BookmarkEntity, CreateBookmarkRequest
from src.storage.repositories.bookmarks_repo import BookmarkRepository


class BookmarkService:
    def __init__(self, bookmark_repo: BookmarkRepository):
        self.bookmark_repo = bookmark_repo

    def list_bookmarks(self, user_id: str = "default_user", document_id: Optional[str] = None) -> List[BookmarkEntity]:
        return self.bookmark_repo.list_bookmarks(user_id=user_id, document_id=document_id)

    def create_bookmark(self, request: CreateBookmarkRequest, user_id: str = "default_user") -> BookmarkEntity:
        return self.bookmark_repo.create_bookmark(user_id=user_id, req=request)

    def delete_bookmark(self, bookmark_id: str, user_id: str = "default_user") -> None:
        self.bookmark_repo.delete_bookmark(user_id=user_id, bookmark_id=bookmark_id)
