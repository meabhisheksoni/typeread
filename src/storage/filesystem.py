"""
TypeRead Local Filesystem Layout Manager
Standardized local directory structures for database, documents, assets, and backups.
"""

from __future__ import annotations
import os
import shutil
from pathlib import Path
from typing import Optional


class FileSystemManager:
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir:
            self.root = Path(base_dir)
        else:
            # Fallback to local app data / home directory
            env_dir = os.environ.get("TYPEREAD_DATA_DIR")
            if env_dir:
                self.root = Path(env_dir)
            else:
                self.root = Path.home() / ".local" / "share" / "TypeRead"

        self.database_dir = self.root / "database"
        self.documents_dir = self.root / "documents"
        self.backups_dir = self.root / "backups"
        self.logs_dir = self.root / "logs"

        self.ensure_directories()

    def ensure_directories(self) -> None:
        self.database_dir.mkdir(parents=True, exist_ok=True)
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    @property
    def db_path(self) -> Path:
        return self.database_dir / "library.db"

    def get_document_dir(self, doc_id: str) -> Path:
        d = self.documents_dir / doc_id
        (d / "source").mkdir(parents=True, exist_ok=True)
        (d / "processed").mkdir(parents=True, exist_ok=True)
        (d / "assets").mkdir(parents=True, exist_ok=True)
        return d

    def store_document_source(self, doc_id: str, source_path: str) -> str:
        doc_dir = self.get_document_dir(doc_id)
        suffix = Path(source_path).suffix
        target_path = doc_dir / "source" / f"original{suffix}"
        if Path(source_path).resolve() != target_path.resolve():
            shutil.copy2(source_path, target_path)
        return str(target_path)
