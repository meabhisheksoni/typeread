"""
TypeRead Backup Service
Provides library archive export, integrity validation, and full system restore.
"""

from __future__ import annotations
from typing import Dict, Any

from src.contracts.types import (
    ExportBackupRequest,
    ExportBackupResponse,
    BackupFileRequest,
    BackupValidationResult,
)
from src.storage.backup import BackupManager


class BackupService:
    def __init__(self, backup_mgr: BackupManager):
        self.backup_mgr = backup_mgr

    def export_backup(self, request: ExportBackupRequest) -> ExportBackupResponse:
        path, manifest = self.backup_mgr.export_backup(request.destinationDirectory)
        return ExportBackupResponse(
            backupFilePath=path,
            manifest=manifest,
        )

    def validate_backup(self, request: BackupFileRequest) -> BackupValidationResult:
        return self.backup_mgr.validate_backup(request.backupFilePath)

    def restore_backup(self, request: BackupFileRequest) -> Dict[str, Any]:
        docs_count, sess_count = self.backup_mgr.restore_backup(request.backupFilePath)
        return {
            "success": True,
            "restoredDocumentsCount": docs_count,
            "restoredSessionsCount": sess_count,
        }
