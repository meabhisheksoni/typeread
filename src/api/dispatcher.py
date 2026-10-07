"""
TypeRead API Dispatcher
Strict implementation of all operations defined in api.json.
Provides in-process typed IPC dispatch for PySide6 and headless test harnesses.
"""

from __future__ import annotations
import dataclasses
import json
import re
from dataclasses import is_dataclass
from typing import Dict, Any, Optional, Tuple

from src.contracts.types import (
    ImportDocumentRequest,
    StructureUpdateRequest,
    ChapterUpdateRequest,
    SectionUpdateRequest,
    ExclusionUpdateRequest,
    StartSessionRequest,
    SubmitKeystrokesRequest,
    SetSessionStateRequest,
    KeystrokeInput,
    ReadingPositionPointer,
    SearchQuery,
    CreateBookmarkRequest,
    CreateNoteRequest,
    UpdateNoteRequest,
    GenerateWeakKeyDrillRequest,
    ExportBackupRequest,
    BackupFileRequest,
    UserSettings,
    GeneralSettings,
    AppearanceSettings,
    TypingSettings,
    DocumentSettings,
    PrivacySettings,
    ProcessingProfile,
    TypingMode,
    ErrorHandlingMode,
    ThemeId,
    CaretStyle,
    DocumentId,
    ChapterId,
    SectionId,
    ParagraphId,
    UserId,
    ErrorCode,
)
from src.core.errors import AppErrorException
from src.services.document_service import DocumentService
from src.services.typing_service import TypingSessionService
from src.services.analytics_service import AnalyticsService
from src.services.search_service import SearchService
from src.services.bookmark_service import BookmarkService
from src.services.note_service import NoteService
from src.services.settings_service import SettingsService
from src.services.backup_service import BackupService


class ApiResponse:
    def __init__(self, status_code: int, data: Any = None):
        self.status_code = status_code
        self.data = data

    def to_json(self) -> str:
        return json.dumps(self.data, default=self._json_serializer)

    @staticmethod
    def _json_serializer(obj: Any) -> Any:
        if is_dataclass(obj):
            return dataclasses.asdict(obj)
        if hasattr(obj, "value"):
            return obj.value
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class ApiDispatcher:
    def __init__(
        self,
        document_service: DocumentService,
        typing_service: TypingSessionService,
        analytics_service: AnalyticsService,
        search_service: SearchService,
        bookmark_service: BookmarkService,
        note_service: NoteService,
        settings_service: SettingsService,
        backup_service: BackupService,
        default_user_id: str = "default_user",
    ):
        self.doc_service = document_service
        self.typing_service = typing_service
        self.analytics_service = analytics_service
        self.search_service = search_service
        self.bookmark_service = bookmark_service
        self.note_service = note_service
        self.settings_service = settings_service
        self.backup_service = backup_service
        self.default_user_id = default_user_id

    def dispatch(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> ApiResponse:
        method = method.upper()
        params = params or {}
        body = body or {}

        try:
            # 1. Documents
            if method == "POST" and path == "/documents/import":
                profile_override = None
                if "profileOverride" in body and body["profileOverride"]:
                    profile_override = ProcessingProfile.from_dict(body["profileOverride"])
                req = ImportDocumentRequest(filePath=body.get("filePath", ""), profileOverride=profile_override)
                result = self.doc_service.import_document(req, user_id=self.default_user_id)
                return ApiResponse(201, self._serialize(result))

            m_commit = re.match(r"^/documents/([^/]+)/commit$", path)
            if method == "POST" and m_commit:
                doc_id = m_commit.group(1)
                chapters_upd = []
                for c in body.get("chapters", []):
                    sec_list = [SectionUpdateRequest(**s) for s in c.get("sections", [])]
                    chapters_upd.append(
                        ChapterUpdateRequest(
                            id=c["id"],
                            title=c["title"],
                            order_index=c["order_index"],
                            included_in_practice=c["included_in_practice"],
                            sections=sec_list,
                        )
                    )
                req = StructureUpdateRequest(
                    chapters=chapters_upd,
                    title=body.get("title"),
                    author=body.get("author"),
                )
                result = self.doc_service.commit_document(doc_id, req, user_id=self.default_user_id)
                return ApiResponse(201, self._serialize(result))

            if method == "GET" and path == "/documents":
                limit = int(params.get("limit", 50))
                offset = int(params.get("offset", 0))
                result = self.doc_service.list_documents(user_id=self.default_user_id, limit=limit, offset=offset)
                return ApiResponse(200, self._serialize(result))

            m_doc_id = re.match(r"^/documents/([^/]+)$", path)
            if m_doc_id:
                doc_id = m_doc_id.group(1)
                if method == "GET":
                    result = self.doc_service.get_document(doc_id)
                    return ApiResponse(200, self._serialize(result))
                elif method == "DELETE":
                    self.doc_service.delete_document(doc_id)
                    return ApiResponse(204, None)

            m_struct = re.match(r"^/documents/([^/]+)/structure$", path)
            if m_struct:
                doc_id = m_struct.group(1)
                if method == "GET":
                    result = self.doc_service.get_document_structure(doc_id)
                    return ApiResponse(200, self._serialize(result))
                elif method == "PUT":
                    chapters_upd = []
                    for c in body.get("chapters", []):
                        sec_list = [SectionUpdateRequest(**s) for s in c.get("sections", [])]
                        chapters_upd.append(
                            ChapterUpdateRequest(
                                id=c["id"],
                                title=c["title"],
                                order_index=c["order_index"],
                                included_in_practice=c["included_in_practice"],
                                sections=sec_list,
                            )
                        )
                    req = StructureUpdateRequest(
                        chapters=chapters_upd,
                        title=body.get("title"),
                        author=body.get("author"),
                    )
                    result = self.doc_service.update_document_structure(doc_id, req)
                    return ApiResponse(200, self._serialize(result))

            m_excl = re.match(r"^/documents/([^/]+)/exclusions$", path)
            if method == "PATCH" and m_excl:
                doc_id = m_excl.group(1)
                req = ExclusionUpdateRequest(
                    targetType=body.get("targetType"),
                    targetId=body.get("targetId"),
                    includedInPractice=body.get("includedInPractice", True),
                )
                self.doc_service.update_exclusions(doc_id, req)
                return ApiResponse(200, {"message": "Exclusions successfully updated"})

            m_sec = re.match(r"^/documents/([^/]+)/sections/([^/]+)/content$", path)
            if method == "GET" and m_sec:
                doc_id = m_sec.group(1)
                sec_id = m_sec.group(2)
                result = self.doc_service.get_section_content(doc_id, sec_id)
                return ApiResponse(200, self._serialize(result))

            m_prog = re.match(r"^/documents/([^/]+)/progress$", path)
            if m_prog:
                doc_id = m_prog.group(1)
                if method == "GET":
                    result = self.doc_service.get_document_progress(doc_id, user_id=self.default_user_id)
                    return ApiResponse(200, self._serialize(result))
                elif method == "PUT":
                    pointer = ReadingPositionPointer(
                        document_id=DocumentId(body.get("documentId", doc_id)),
                        chapter_id=ChapterId(body.get("chapterId", "")),
                        section_id=SectionId(body.get("sectionId", "")),
                        paragraph_id=ParagraphId(body.get("paragraphId", "")),
                        character_offset=body.get("characterOffset", 0),
                    )
                    result = self.doc_service.update_document_progress(doc_id, pointer, user_id=self.default_user_id)
                    return ApiResponse(200, self._serialize(result))

            # 2. Sessions
            if method == "POST" and path == "/sessions/start":
                req = StartSessionRequest(
                    documentId=body.get("documentId"),
                    chapterId=body.get("chapterId"),
                    sectionId=body.get("sectionId"),
                    typingMode=TypingMode(body.get("typingMode", "standard")),
                    errorHandlingMode=ErrorHandlingMode(body.get("errorHandlingMode", "allow_with_backspace")),
                )
                result = self.typing_service.start_session(req, user_id=self.default_user_id)
                return ApiResponse(201, self._serialize(result))

            m_strokes = re.match(r"^/sessions/([^/]+)/keystrokes$", path)
            if method == "POST" and m_strokes:
                sess_id = m_strokes.group(1)
                raw_strokes = body.get("keystrokes", [])
                strokes = [
                    KeystrokeInput(
                        timestamp_ms=s.get("timestamp_ms", s.get("timestampMs", 0)),
                        key=s.get("key", ""),
                        expected_char=s.get("expected_char", s.get("expectedChar", "")),
                        position=s.get("position", 0),
                        is_backspace=s.get("is_backspace", s.get("isBackspace", False)),
                    )
                    for s in raw_strokes
                ]
                req = SubmitKeystrokesRequest(keystrokes=strokes)
                result = self.typing_service.submit_keystrokes(sess_id, req)
                return ApiResponse(200, self._serialize(result))

            m_state = re.match(r"^/sessions/([^/]+)/state$", path)
            if method == "POST" and m_state:
                sess_id = m_state.group(1)
                req = SetSessionStateRequest(state=body.get("state"))
                result = self.typing_service.set_session_state(sess_id, req)
                return ApiResponse(200, self._serialize(result))

            m_comp = re.match(r"^/sessions/([^/]+)/complete$", path)
            if method == "POST" and m_comp:
                sess_id = m_comp.group(1)
                result = self.typing_service.complete_session(sess_id)
                return ApiResponse(200, self._serialize(result))

            m_abort = re.match(r"^/sessions/([^/]+)/abort$", path)
            if method == "POST" and m_abort:
                sess_id = m_abort.group(1)
                result = self.typing_service.abort_session(sess_id)
                return ApiResponse(200, self._serialize(result))

            if method == "GET" and path == "/sessions/active":
                result = self.typing_service.get_active_session(user_id=self.default_user_id)
                return ApiResponse(200, self._serialize(result))

            # 3. Analytics & Practice
            if method == "GET" and path == "/analytics/overview":
                result = self.analytics_service.get_analytics_overview(user_id=self.default_user_id)
                return ApiResponse(200, self._serialize(result))

            if method == "GET" and path == "/analytics/trends":
                days = int(params.get("days", 30))
                result = self.analytics_service.get_analytics_trends(user_id=self.default_user_id, days=days)
                return ApiResponse(200, self._serialize(result))

            m_doc_an = re.match(r"^/analytics/documents/([^/]+)$", path)
            if method == "GET" and m_doc_an:
                doc_id = m_doc_an.group(1)
                result = self.analytics_service.get_document_analytics(user_id=self.default_user_id, document_id=doc_id)
                return ApiResponse(200, self._serialize(result))

            if method == "GET" and path == "/analytics/weak-keys":
                limit = int(params.get("limit", 10))
                result = self.analytics_service.get_weak_keys(user_id=self.default_user_id, limit=limit)
                return ApiResponse(200, self._serialize(result))

            if method == "POST" and path == "/practice/drills/generate":
                req = GenerateWeakKeyDrillRequest(
                    wordCount=body.get("wordCount", 100),
                    documentId=body.get("documentId"),
                    targetKeys=body.get("targetKeys"),
                )
                result = self.analytics_service.generate_weak_key_drill(req, user_id=self.default_user_id)
                return ApiResponse(200, self._serialize(result))

            # 4. Search
            if method == "POST" and path == "/search":
                req = SearchQuery(
                    query=body.get("query", ""),
                    limit=body.get("limit", 50),
                    offset=body.get("offset", 0),
                    document_id=body.get("documentId"),
                )
                result = self.search_service.search_documents(req)
                return ApiResponse(200, self._serialize(result))

            # 5. Bookmarks
            if method == "GET" and path == "/bookmarks":
                doc_id = params.get("documentId")
                result = self.bookmark_service.list_bookmarks(user_id=self.default_user_id, document_id=doc_id)
                return ApiResponse(200, self._serialize(result))

            if method == "POST" and path == "/bookmarks":
                req = CreateBookmarkRequest(
                    documentId=body.get("documentId"),
                    chapterId=body.get("chapterId"),
                    sectionId=body.get("sectionId"),
                    paragraphId=body.get("paragraphId"),
                    characterOffset=body.get("characterOffset", 0),
                    title=body.get("title", ""),
                    noteSnippet=body.get("noteSnippet"),
                )
                result = self.bookmark_service.create_bookmark(req, user_id=self.default_user_id)
                return ApiResponse(201, self._serialize(result))

            m_bm = re.match(r"^/bookmarks/([^/]+)$", path)
            if method == "DELETE" and m_bm:
                bm_id = m_bm.group(1)
                self.bookmark_service.delete_bookmark(bm_id, user_id=self.default_user_id)
                return ApiResponse(204, None)

            # 6. Notes
            if method == "GET" and path == "/notes":
                doc_id = params.get("documentId")
                result = self.note_service.list_notes(user_id=self.default_user_id, document_id=doc_id)
                return ApiResponse(200, self._serialize(result))

            if method == "POST" and path == "/notes":
                req = CreateNoteRequest(
                    documentId=body.get("documentId"),
                    chapterId=body.get("chapterId"),
                    sectionId=body.get("sectionId"),
                    paragraphId=body.get("paragraphId"),
                    content=body.get("content", ""),
                )
                result = self.note_service.create_note(req, user_id=self.default_user_id)
                return ApiResponse(201, self._serialize(result))

            m_note = re.match(r"^/notes/([^/]+)$", path)
            if m_note:
                note_id = m_note.group(1)
                if method == "PUT":
                    req = UpdateNoteRequest(content=body.get("content", ""))
                    result = self.note_service.update_note(note_id, req, user_id=self.default_user_id)
                    return ApiResponse(200, self._serialize(result))
                elif method == "DELETE":
                    self.note_service.delete_note(note_id, user_id=self.default_user_id)
                    return ApiResponse(204, None)

            # 7. Settings
            if method == "GET" and path == "/settings":
                result = self.settings_service.get_settings(user_id=self.default_user_id)
                return ApiResponse(200, self._serialize(result))

            if method == "PUT" and path == "/settings":
                g = body.get("general", {})
                a = body.get("appearance", {})
                t = body.get("typing", {})
                d = body.get("documents", {})
                p = body.get("privacy", {})

                prof = ProcessingProfile.from_dict(d.get("default_processing_profile", d.get("defaultProcessingProfile", {})))
                settings = UserSettings(
                    user_id=UserId(self.default_user_id),
                    general=GeneralSettings(
                        startup_behavior=g.get("startup_behavior", g.get("startupBehavior", "resume_last")),
                        autosave_interval_seconds=g.get("autosave_interval_seconds", g.get("autosaveIntervalSeconds", 10)),
                        confirm_before_delete=g.get("confirm_before_delete", g.get("confirmBeforeDelete", True)),
                        backup_storage_directory=g.get("backup_storage_directory", g.get("backupStorageDirectory", "")),
                    ),
                    appearance=AppearanceSettings(
                        theme=ThemeId(a.get("theme", "dark")),
                        font_family=a.get("font_family", a.get("fontFamily", "JetBrains Mono")),
                        font_size_pt=a.get("font_size_pt", a.get("fontSizePt", 14)),
                        line_height_em=a.get("line_height_em", a.get("lineHeightEm", 1.6)),
                        content_width_px=a.get("content_width_px", a.get("contentWidthPx", 840)),
                        caret_style=CaretStyle(a.get("caret_style", a.get("caretStyle", "block"))),
                        smooth_caret_animation=a.get("smooth_caret_animation", a.get("smoothCaretAnimation", True)),
                    ),
                    typing=TypingSettings(
                        default_mode=TypingMode(t.get("default_mode", t.get("defaultMode", "standard"))),
                        error_handling=ErrorHandlingMode(t.get("error_handling", t.get("errorHandling", "allow_with_backspace"))),
                        sound_keypress=t.get("sound_keypress", t.get("soundKeypress", False)),
                        sound_error=t.get("sound_error", t.get("soundError", False)),
                        sound_complete=t.get("sound_complete", t.get("soundComplete", True)),
                        adaptive_difficulty_enabled=t.get("adaptive_difficulty_enabled", t.get("adaptiveDifficultyEnabled", False)),
                    ),
                    documents=DocumentSettings(
                        default_processing_profile=prof,
                        auto_run_ocr_if_low_confidence=d.get("auto_run_ocr_if_low_confidence", d.get("autoRunOcrIfLowConfidence", False)),
                    ),
                    privacy=PrivacySettings(
                        local_telemetry_enabled=p.get("local_telemetry_enabled", p.get("localTelemetryEnabled", False)),
                        detailed_error_logging=p.get("detailed_error_logging", p.get("detailedErrorLogging", True)),
                    ),
                    updated_at="",
                )
                result = self.settings_service.update_settings(settings)
                return ApiResponse(200, self._serialize(result))

            # 8. Backup
            if method == "POST" and path == "/backup/export":
                req = ExportBackupRequest(destinationDirectory=body.get("destinationDirectory", ""))
                result = self.backup_service.export_backup(req)
                return ApiResponse(201, self._serialize(result))

            if method == "POST" and path == "/backup/validate":
                req = BackupFileRequest(backupFilePath=body.get("backupFilePath", ""))
                result = self.backup_service.validate_backup(req)
                return ApiResponse(200, self._serialize(result))

            if method == "POST" and path == "/backup/restore":
                req = BackupFileRequest(backupFilePath=body.get("backupFilePath", ""))
                result = self.backup_service.restore_backup(req)
                return ApiResponse(200, self._serialize(result))

            # Unmatched route
            raise AppErrorException.not_found(
                code=ErrorCode.DOCUMENT_NOT_FOUND,
                message=f"No route found for {method} {path}",
            )

        except AppErrorException as app_err:
            return ApiResponse(app_err.status_code, app_err.to_dict())
        except Exception as ex:
            server_err = AppErrorException.server_error(
                code=ErrorCode.DATABASE_ERROR,
                message=f"Internal service error: {str(ex)}",
            )
            return ApiResponse(500, server_err.to_dict())

    def _serialize(self, obj: Any) -> Any:
        if obj is None:
            return None
        if isinstance(obj, list):
            return [self._serialize(x) for x in obj]
        if is_dataclass(obj):
            data = {}
            for k, v in dataclasses.asdict(obj).items():
                data[k] = self._serialize(v)
            return data
        if hasattr(obj, "value"):
            return obj.value
        return obj
