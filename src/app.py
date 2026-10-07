"""
TypeRead Application Container & Service Registry
Instantiates and wires together all storage, domain services, and the API dispatcher.
"""

from __future__ import annotations
from typing import Optional

from src.storage.db import Database
from src.storage.filesystem import FileSystemManager
from src.storage.backup import BackupManager
from src.storage.repositories.document_repo import DocumentRepository
from src.storage.repositories.session_repo import SessionRepository
from src.storage.repositories.progress_repo import ProgressRepository
from src.storage.repositories.analytics_repo import AnalyticsRepository
from src.storage.repositories.search_repo import SearchRepository
from src.storage.repositories.bookmarks_repo import BookmarkRepository
from src.storage.repositories.notes_repo import NoteRepository
from src.storage.repositories.settings_repo import SettingsRepository

from src.services.document_service import DocumentService
from src.services.typing_service import TypingSessionService
from src.services.analytics_service import AnalyticsService
from src.services.search_service import SearchService
from src.services.bookmark_service import BookmarkService
from src.services.note_service import NoteService
from src.services.settings_service import SettingsService
from src.services.backup_service import BackupService
from src.api.dispatcher import ApiDispatcher


class ApplicationContainer:
    def __init__(self, data_dir: Optional[str] = None, db_path: Optional[str] = None):
        self.fs = FileSystemManager(base_dir=data_dir)
        actual_db_path = db_path if db_path else str(self.fs.db_path)
        self.db = Database(db_path=actual_db_path)
        self.backup_mgr = BackupManager(db=self.db, fs=self.fs)

        # Repositories
        self.doc_repo = DocumentRepository(db=self.db)
        self.session_repo = SessionRepository(db=self.db)
        self.progress_repo = ProgressRepository(db=self.db)
        self.analytics_repo = AnalyticsRepository(db=self.db)
        self.search_repo = SearchRepository(db=self.db)
        self.bookmark_repo = BookmarkRepository(db=self.db)
        self.note_repo = NoteRepository(db=self.db)
        self.settings_repo = SettingsRepository(db=self.db)

        # Services
        self.doc_service = DocumentService(doc_repo=self.doc_repo, progress_repo=self.progress_repo, fs=self.fs)
        self.typing_service = TypingSessionService(
            doc_repo=self.doc_repo,
            session_repo=self.session_repo,
            progress_repo=self.progress_repo,
            analytics_repo=self.analytics_repo,
        )
        self.analytics_service = AnalyticsService(analytics_repo=self.analytics_repo, doc_repo=self.doc_repo)
        self.search_service = SearchService(search_repo=self.search_repo)
        self.bookmark_service = BookmarkService(bookmark_repo=self.bookmark_repo)
        self.note_service = NoteService(note_repo=self.note_repo)
        self.settings_service = SettingsService(settings_repo=self.settings_repo)
        self.backup_service = BackupService(backup_mgr=self.backup_mgr)

        # In-process API dispatcher
        self.dispatcher = ApiDispatcher(
            document_service=self.doc_service,
            typing_service=self.typing_service,
            analytics_service=self.analytics_service,
            search_service=self.search_service,
            bookmark_service=self.bookmark_service,
            note_service=self.note_service,
            settings_service=self.settings_service,
            backup_service=self.backup_service,
        )


def create_app(data_dir: Optional[str] = None, db_path: Optional[str] = None) -> ApplicationContainer:
    return ApplicationContainer(data_dir=data_dir, db_path=db_path)
