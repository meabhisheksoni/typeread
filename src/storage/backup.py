"""
TypeRead Backup & Restore Manager
ZIP archive (.typeread-backup) generation with SQLite Online Backup API,
SHA-256 manifest validation, and atomic restore.
"""

from __future__ import annotations
import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple, List, Optional

from src.contracts.types import (
    BackupManifest,
    BackupFileItem,
    BackupValidationResult,
    ErrorCode,
)
from src.core.errors import AppErrorException
from src.storage.db import Database
from src.storage.filesystem import FileSystemManager


class BackupManager:
    def __init__(self, db: Database, fs: FileSystemManager, app_version: str = "1.0.0"):
        self.db = db
        self.fs = fs
        self.app_version = app_version

    @staticmethod
    def sha256_file(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def export_backup(self, destination_dir: str) -> Tuple[str, BackupManifest]:
        dest_path = Path(destination_dir)
        dest_path.mkdir(parents=True, exist_ok=True)

        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_filename = f"typeread_backup_{timestamp_str}.typeread-backup"
        backup_file_path = dest_path / backup_filename

        with tempfile.TemporaryDirectory() as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)
            db_snap_path = tmp_dir / "library.db"

            # 1. Clean SQLite snapshot using sqlite3_backup API
            src_conn = self.db.get_connection()
            try:
                dst_conn = sqlite3.connect(str(db_snap_path))
                src_conn.backup(dst_conn)
                dst_conn.close()
            except Exception as e:
                raise AppErrorException.server_error(
                    code=ErrorCode.BACKUP_CREATION_FAILED,
                    message=f"Failed to create online SQLite backup: {str(e)}",
                )
            finally:
                src_conn.close()

            db_hash = self.sha256_file(db_snap_path)
            files_manifest: List[BackupFileItem] = [
                BackupFileItem(
                    relative_path="library.db",
                    checksum_sha256=db_hash,
                    byte_size=db_snap_path.stat().st_size,
                )
            ]

            # 2. Copy documents directory
            tmp_docs = tmp_dir / "documents"
            if self.fs.documents_dir.exists():
                shutil.copytree(self.fs.documents_dir, tmp_docs, dirs_exist_ok=True)
                for root, _, files in os.walk(tmp_docs):
                    for f in files:
                        p = Path(root) / f
                        rel = str(p.relative_to(tmp_dir)).replace("\\", "/")
                        files_manifest.append(
                            BackupFileItem(
                                relative_path=rel,
                                checksum_sha256=self.sha256_file(p),
                                byte_size=p.stat().st_size,
                            )
                        )

            # Query counts
            with self.db.cursor() as cur:
                cur.execute("SELECT COUNT(*) as cnt FROM documents;")
                docs_count = cur.fetchone()["cnt"]
                cur.execute("SELECT COUNT(*) as cnt FROM typing_sessions;")
                sess_count = cur.fetchone()["cnt"]

            now_iso = datetime.now(timezone.utc).isoformat()
            manifest = BackupManifest(
                backup_version=1,
                app_version=self.app_version,
                exported_at=now_iso,
                database_checksum_sha256=db_hash,
                documents_count=docs_count,
                sessions_count=sess_count,
                files=files_manifest,
            )

            # Write manifest.json
            manifest_path = tmp_dir / "manifest.json"
            manifest_dict = {
                "backupVersion": manifest.backup_version,
                "appVersion": manifest.app_version,
                "exportedAt": manifest.exported_at,
                "databaseChecksumSha256": manifest.database_checksum_sha256,
                "documentsCount": manifest.documents_count,
                "sessionsCount": manifest.sessions_count,
                "files": [
                    {
                        "relativePath": item.relative_path,
                        "checksumSha256": item.checksum_sha256,
                        "byteSize": item.byte_size,
                    }
                    for item in manifest.files
                ],
            }
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest_dict, f, indent=2)

            # 3. Create zip archive
            try:
                with zipfile.ZipFile(backup_file_path, "w", zipfile.ZIP_DEFLATED) as zip_out:
                    for root, _, files in os.walk(tmp_dir):
                        for f in files:
                            p = Path(root) / f
                            arcname = p.relative_to(tmp_dir)
                            zip_out.write(p, arcname)
            except Exception as e:
                raise AppErrorException.server_error(
                    code=ErrorCode.BACKUP_CREATION_FAILED,
                    message=f"Failed to assemble zip archive: {str(e)}",
                )

        return str(backup_file_path), manifest

    def validate_backup(self, backup_path: str) -> BackupValidationResult:
        p = Path(backup_path)
        if not p.exists() or not p.is_file():
            return BackupValidationResult(
                is_valid=False,
                validation_errors=[f"Backup file does not exist: {backup_path}"],
            )

        if not zipfile.is_zipfile(p):
            return BackupValidationResult(
                is_valid=False,
                validation_errors=["File is not a valid zip archive"],
            )

        errors: List[str] = []
        manifest: Optional[BackupManifest] = None

        with zipfile.ZipFile(p, "r") as zf:
            namelist = zf.namelist()
            if "manifest.json" not in namelist:
                return BackupValidationResult(
                    is_valid=False,
                    validation_errors=["Missing manifest.json in backup archive"],
                )

            try:
                manifest_bytes = zf.read("manifest.json")
                data = json.loads(manifest_bytes.decode("utf-8"))
                files_items = [
                    BackupFileItem(
                        relative_path=fi["relativePath"],
                        checksum_sha256=fi["checksumSha256"],
                        byte_size=fi["byteSize"],
                    )
                    for fi in data.get("files", [])
                ]
                manifest = BackupManifest(
                    backup_version=data.get("backupVersion", 1),
                    app_version=data.get("appVersion", "1.0.0"),
                    exported_at=data.get("exportedAt", ""),
                    database_checksum_sha256=data.get("databaseChecksumSha256", ""),
                    documents_count=data.get("documentsCount", 0),
                    sessions_count=data.get("sessionsCount", 0),
                    files=files_items,
                )
            except Exception as e:
                return BackupValidationResult(
                    is_valid=False,
                    validation_errors=[f"Failed to parse manifest.json: {str(e)}"],
                )

            # Check files and checksums
            for item in manifest.files:
                if item.relative_path not in namelist:
                    errors.append(f"Missing file in archive: {item.relative_path}")
                    continue

                try:
                    extracted_data = zf.read(item.relative_path)
                    h = hashlib.sha256(extracted_data).hexdigest()
                    if h != item.checksum_sha256:
                        errors.append(
                            f"Checksum mismatch for {item.relative_path}: expected {item.checksum_sha256}, got {h}"
                        )
                except Exception as ex:
                    errors.append(f"Corrupted file '{item.relative_path}' in archive: {str(ex)}")

        return BackupValidationResult(
            is_valid=(len(errors) == 0),
            validation_errors=errors,
            manifest=manifest,
        )

    def restore_backup(self, backup_path: str) -> Tuple[int, int]:
        validation = self.validate_backup(backup_path)
        if not validation.is_valid:
            raise AppErrorException.bad_request(
                code=ErrorCode.BACKUP_CORRUPTED,
                message=f"Backup validation failed: {', '.join(validation.validation_errors)}",
                suggested_action="Ensure the backup archive has not been modified or corrupted.",
            )

        manifest = validation.manifest
        assert manifest is not None

        # Extract to temporary directory first
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)
            with zipfile.ZipFile(backup_path, "r") as zf:
                zf.extractall(tmp_dir)

            # Verify SQLite DB
            tmp_db = tmp_dir / "library.db"
            if not tmp_db.exists():
                raise AppErrorException.bad_request(
                    code=ErrorCode.BACKUP_CORRUPTED,
                    message="library.db not found in backup",
                )

            # Restore database using SQLite Online Backup API
            src_conn = sqlite3.connect(str(tmp_db))
            dst_conn = self.db.get_connection()
            try:
                src_conn.backup(dst_conn)
            finally:
                src_conn.close()
                dst_conn.close()

            # Restore documents
            tmp_docs = tmp_dir / "documents"
            if tmp_docs.exists():
                shutil.copytree(tmp_docs, self.fs.documents_dir, dirs_exist_ok=True)

        return manifest.documents_count, manifest.sessions_count
