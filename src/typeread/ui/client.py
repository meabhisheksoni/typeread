"""
TypeRead UI Client Wrapper
Provides synchronous typed in-process IPC client connecting PySide6 UI views to ApiDispatcher.
Strictly adheres to api.json endpoints and domain models from types.py.
"""

from __future__ import annotations
import dataclasses
from typing import Optional, List, Dict, Any

from src.contracts.types import (
    DocumentEntity,
    DocumentStructureTree,
    IngestionPreview,
    StructureUpdateRequest,
    ReadingProgressEntity,
    ReadingPositionPointer,
    TypingSessionEntity,
    BookmarkEntity,
    NoteEntity,
    UserSettings,
    TypingMode,
    ErrorHandlingMode,
    ThemeId,
    CaretStyle,
    DocumentId,
    ChapterId,
    SectionId,
    ParagraphId,
    SessionId,
    BookmarkId,
    NoteId,
    UserId,
)
from src.app import create_app, ApplicationContainer
from src.api.dispatcher import ApiDispatcher


class UiApiClient:
    def __init__(self, dispatcher: Optional[ApiDispatcher] = None, app_container: Optional[ApplicationContainer] = None):
        if dispatcher:
            self.dispatcher = dispatcher
            self.container = app_container
        elif app_container:
            self.container = app_container
            self.dispatcher = app_container.dispatcher
        else:
            self.container = create_app()
            self.dispatcher = self.container.dispatcher

    def import_document(self, file_path: str, profile_override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        body: Dict[str, Any] = {"filePath": file_path}
        if profile_override:
            body["profileOverride"] = profile_override
        res = self.dispatcher.dispatch("POST", "/documents/import", body=body)
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Document import failed"))
        return res.data

    def commit_document(self, document_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
        res = self.dispatcher.dispatch("POST", f"/documents/{document_id}/commit", body=request)
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Document commit failed"))
        return res.data

    def list_documents(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        res = self.dispatcher.dispatch("GET", "/documents", params={"limit": limit, "offset": offset})
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to list documents"))
        return res.data

    def get_document(self, document_id: str) -> Dict[str, Any]:
        res = self.dispatcher.dispatch("GET", f"/documents/{document_id}")
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Document not found"))
        return res.data

    def delete_document(self, document_id: str) -> None:
        res = self.dispatcher.dispatch("DELETE", f"/documents/{document_id}")
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to delete document"))

    def get_document_structure(self, document_id: str) -> Dict[str, Any]:
        res = self.dispatcher.dispatch("GET", f"/documents/{document_id}/structure")
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to get structure"))
        return res.data

    def update_document_structure(self, document_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
        res = self.dispatcher.dispatch("PUT", f"/documents/{document_id}/structure", body=request)
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to update structure"))
        return res.data

    def update_exclusions(self, document_id: str, target_type: str, target_id: str, included: bool) -> None:
        body = {
            "targetType": target_type,
            "targetId": target_id,
            "includedInPractice": included,
        }
        res = self.dispatcher.dispatch("PATCH", f"/documents/{document_id}/exclusions", body=body)
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to update exclusions"))

    def get_section_content(self, document_id: str, section_id: str) -> Dict[str, Any]:
        res = self.dispatcher.dispatch("GET", f"/documents/{document_id}/sections/{section_id}/content")
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to get section content"))
        return res.data

    def get_document_progress(self, document_id: str) -> Dict[str, Any]:
        res = self.dispatcher.dispatch("GET", f"/documents/{document_id}/progress")
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to get progress"))
        return res.data

    def update_document_progress(self, document_id: str, pointer: Dict[str, Any]) -> Dict[str, Any]:
        res = self.dispatcher.dispatch("PUT", f"/documents/{document_id}/progress", body=pointer)
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to update progress"))
        return res.data

    def start_session(
        self,
        document_id: str,
        chapter_id: str,
        section_id: str,
        typing_mode: str = "standard",
        error_handling_mode: str = "allow_with_backspace",
    ) -> Dict[str, Any]:
        body = {
            "documentId": document_id,
            "chapterId": chapter_id,
            "sectionId": section_id,
            "typingMode": typing_mode,
            "errorHandlingMode": error_handling_mode,
        }
        res = self.dispatcher.dispatch("POST", "/sessions/start", body=body)
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to start session"))
        return res.data

    def submit_keystrokes(self, session_id: str, keystrokes: List[Dict[str, Any]]) -> Dict[str, Any]:
        body = {"keystrokes": keystrokes}
        res = self.dispatcher.dispatch("POST", f"/sessions/{session_id}/keystrokes", body=body)
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to submit keystrokes"))
        return res.data

    def set_session_state(self, session_id: str, state: str) -> Dict[str, Any]:
        res = self.dispatcher.dispatch("POST", f"/sessions/{session_id}/state", body={"state": state})
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to set session state"))
        return res.data

    def complete_session(self, session_id: str) -> Dict[str, Any]:
        res = self.dispatcher.dispatch("POST", f"/sessions/{session_id}/complete")
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to complete session"))
        return res.data

    def abort_session(self, session_id: str) -> Dict[str, Any]:
        res = self.dispatcher.dispatch("POST", f"/sessions/{session_id}/abort")
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to abort session"))
        return res.data

    def get_active_session(self) -> Optional[Dict[str, Any]]:
        res = self.dispatcher.dispatch("GET", "/sessions/active")
        if res.status_code == 200:
            return res.data
        return None

    def get_analytics_overview(self) -> Dict[str, Any]:
        res = self.dispatcher.dispatch("GET", "/analytics/overview")
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to get analytics overview"))
        return res.data

    def get_analytics_trends(self, days: int = 30) -> Dict[str, Any]:
        res = self.dispatcher.dispatch("GET", "/analytics/trends", params={"days": days})
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to get analytics trends"))
        return res.data

    def get_document_analytics(self, document_id: str) -> Dict[str, Any]:
        res = self.dispatcher.dispatch("GET", f"/analytics/documents/{document_id}")
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to get document analytics"))
        return res.data

    def get_weak_keys(self, limit: int = 10) -> List[Dict[str, Any]]:
        res = self.dispatcher.dispatch("GET", "/analytics/weak-keys", params={"limit": limit})
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to get weak keys"))
        return res.data

    def generate_weak_key_drill(self, word_count: int = 100, document_id: Optional[str] = None, target_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        body: Dict[str, Any] = {"wordCount": word_count}
        if document_id:
            body["documentId"] = document_id
        if target_keys:
            body["targetKeys"] = target_keys
        res = self.dispatcher.dispatch("POST", "/practice/drills/generate", body=body)
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to generate weak key drill"))
        return res.data

    def search_documents(self, query: str, document_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        body = {"query": query, "limit": limit, "offset": 0}
        if document_id:
            body["documentId"] = document_id
        res = self.dispatcher.dispatch("POST", "/search", body=body)
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to perform search"))
        return res.data

    def list_bookmarks(self, document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"documentId": document_id} if document_id else {}
        res = self.dispatcher.dispatch("GET", "/bookmarks", params=params)
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to list bookmarks"))
        return res.data

    def create_bookmark(
        self,
        document_id: str,
        chapter_id: str,
        section_id: str,
        paragraph_id: str,
        character_offset: int,
        title: str,
        note_snippet: Optional[str] = None,
    ) -> Dict[str, Any]:
        body = {
            "documentId": document_id,
            "chapterId": chapter_id,
            "sectionId": section_id,
            "paragraphId": paragraph_id,
            "characterOffset": character_offset,
            "title": title,
            "noteSnippet": note_snippet,
        }
        res = self.dispatcher.dispatch("POST", "/bookmarks", body=body)
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to create bookmark"))
        return res.data

    def delete_bookmark(self, bookmark_id: str) -> None:
        res = self.dispatcher.dispatch("DELETE", f"/bookmarks/{bookmark_id}")
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to delete bookmark"))

    def list_notes(self, document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"documentId": document_id} if document_id else {}
        res = self.dispatcher.dispatch("GET", "/notes", params=params)
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to list notes"))
        return res.data

    def create_note(
        self,
        document_id: str,
        chapter_id: str,
        section_id: str,
        paragraph_id: str,
        content: str,
    ) -> Dict[str, Any]:
        body = {
            "documentId": document_id,
            "chapterId": chapter_id,
            "sectionId": section_id,
            "paragraphId": paragraph_id,
            "content": content,
        }
        res = self.dispatcher.dispatch("POST", "/notes", body=body)
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to create note"))
        return res.data

    def update_note(self, note_id: str, content: str) -> Dict[str, Any]:
        res = self.dispatcher.dispatch("PUT", f"/notes/{note_id}", body={"content": content})
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to update note"))
        return res.data

    def delete_note(self, note_id: str) -> None:
        res = self.dispatcher.dispatch("DELETE", f"/notes/{note_id}")
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to delete note"))

    def get_settings(self) -> Dict[str, Any]:
        res = self.dispatcher.dispatch("GET", "/settings")
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to get settings"))
        return res.data

    def update_settings(self, settings_data: Dict[str, Any]) -> Dict[str, Any]:
        res = self.dispatcher.dispatch("PUT", "/settings", body=settings_data)
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to update settings"))
        return res.data

    def export_backup(self, dest_dir: str) -> Dict[str, Any]:
        res = self.dispatcher.dispatch("POST", "/backup/export", body={"destinationDirectory": dest_dir})
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to export backup"))
        return res.data

    def validate_backup(self, file_path: str) -> Dict[str, Any]:
        res = self.dispatcher.dispatch("POST", "/backup/validate", body={"backupFilePath": file_path})
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to validate backup"))
        return res.data

    def restore_backup(self, file_path: str) -> Dict[str, Any]:
        res = self.dispatcher.dispatch("POST", "/backup/restore", body={"backupFilePath": file_path})
        if res.status_code >= 400:
            raise RuntimeError(res.data.get("message", "Failed to restore backup"))
        return res.data
