"""
Unit tests for ZIP backup export, SHA-256 verification, corruption rejection, and restore.
"""

import tempfile
import zipfile
import pytest
from pathlib import Path

from src.contracts.types import (
    ExportBackupRequest,
    BackupFileRequest,
    ErrorCode,
)
from src.core.errors import AppErrorException
from src.app import create_app


def test_backup_export_validate_and_restore():
    with tempfile.TemporaryDirectory() as data_dir:
        app = create_app(data_dir=data_dir)

        # Export backup
        with tempfile.TemporaryDirectory() as export_dir:
            resp = app.backup_service.export_backup(ExportBackupRequest(destinationDirectory=export_dir))
            backup_path = resp.backupFilePath

            assert Path(backup_path).exists()
            assert resp.manifest.backup_version == 1
            assert resp.manifest.database_checksum_sha256 != ""

            # Validate backup
            val_res = app.backup_service.validate_backup(BackupFileRequest(backupFilePath=backup_path))
            assert val_res.is_valid is True
            assert len(val_res.validation_errors) == 0

            # Corrupt the archive by modifying a byte
            corrupted_backup_path = Path(export_dir) / "corrupted.typeread-backup"
            with open(backup_path, "rb") as fin, open(corrupted_backup_path, "wb") as fout:
                data = bytearray(fin.read())
                # Flip a byte near the middle
                data[len(data) // 2] ^= 0xFF
                fout.write(data)

            # Validation must fail on corrupted archive
            val_corrupt = app.backup_service.validate_backup(BackupFileRequest(backupFilePath=str(corrupted_backup_path)))
            assert val_corrupt.is_valid is False

            # Restore corrupted must raise error
            with pytest.raises(AppErrorException) as exc_info:
                app.backup_service.restore_backup(BackupFileRequest(backupFilePath=str(corrupted_backup_path)))
            assert exc_info.value.code == ErrorCode.BACKUP_CORRUPTED

            # Restore valid archive
            restore_res = app.backup_service.restore_backup(BackupFileRequest(backupFilePath=backup_path))
            assert restore_res["success"] is True
