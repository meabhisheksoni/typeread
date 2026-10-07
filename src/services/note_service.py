"""
TypeRead Note Service
Manages study notes and annotations.
"""

from __future__ import annotations
from typing import List, Optional

from src.contracts.types import NoteEntity, CreateNoteRequest, UpdateNoteRequest
from src.storage.repositories.notes_repo import NoteRepository


class NoteService:
    def __init__(self, note_repo: NoteRepository):
        self.note_repo = note_repo

    def list_notes(self, user_id: str = "default_user", document_id: Optional[str] = None) -> List[NoteEntity]:
        return self.note_repo.list_notes(user_id=user_id, document_id=document_id)

    def create_note(self, request: CreateNoteRequest, user_id: str = "default_user") -> NoteEntity:
        return self.note_repo.create_note(user_id=user_id, req=request)

    def update_note(self, note_id: str, request: UpdateNoteRequest, user_id: str = "default_user") -> NoteEntity:
        return self.note_repo.update_note(user_id=user_id, note_id=note_id, content=request.content)

    def delete_note(self, note_id: str, user_id: str = "default_user") -> None:
        self.note_repo.delete_note(user_id=user_id, note_id=note_id)
