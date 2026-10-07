"""
Rigorously tests boundary conditions, null values, invalid inputs, and error states.
Verifies application security, fault tolerance, and strict contract adherence.
"""

import os
import tempfile
import sqlite3
import pytest
import fitz

from src.app import create_app
from src.contracts.types import (
    DocumentFormat,
    ErrorCode,
    KeystrokeInput,
    TypingMode,
    ErrorHandlingMode,
    ExportBackupRequest,
    BackupFileRequest,
)
from src.core.errors import AppErrorException
from src.core.document.parsers import DocumentParserRegistry
from src.core.typing.evaluator import KeystrokeEvaluator
from src.core.typing.metrics import MetricsCalculator
from src.core.typing.session import TypingSessionManager


@pytest.fixture
def app_instance():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        yield create_app(data_dir=temp_dir)


def test_empty_file_import_error():
    """Verify that importing a 0-byte file raises EMPTY_DOCUMENT."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        path = f.name

    with pytest.raises(AppErrorException) as exc_info:
        DocumentParserRegistry.parse(path)
    assert exc_info.value.code == ErrorCode.EMPTY_DOCUMENT
    assert exc_info.value.status_code == 400


def test_scanned_pdf_ocr_required():
    """Verify that a PDF containing 0 extractable text raises OCR_REQUIRED."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        pdf_path = os.path.join(td, "blank.pdf")
        doc = fitz.open()
        doc.new_page()  # Blank page without text
        doc.save(pdf_path)
        doc.close()

        with pytest.raises(AppErrorException) as exc_info:
            DocumentParserRegistry.parse(pdf_path)
        assert exc_info.value.code == ErrorCode.OCR_REQUIRED
        assert exc_info.value.status_code == 422


def test_nonexistent_file_import_error():
    """Verify that importing a non-existent file path raises FILE_NOT_FOUND."""
    fake_path = "/path/to/nonexistent/file_123456789.pdf"
    with pytest.raises(AppErrorException) as exc_info:
        DocumentParserRegistry.parse(fake_path)
    assert exc_info.value.code == ErrorCode.FILE_NOT_FOUND
    assert exc_info.value.status_code == 400


def test_unsupported_format_error():
    """Verify that unsupported extensions raise UNSUPPORTED_FORMAT."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        path = os.path.join(td, "bad.exe")
        with open(path, "w") as f:
            f.write("Binary executable dummy")

        with pytest.raises(AppErrorException) as exc_info:
            DocumentParserRegistry.parse(path)
        assert exc_info.value.code == ErrorCode.UNSUPPORTED_FORMAT
        assert exc_info.value.status_code == 400


def test_corrupted_pdf_file_error():
    """Verify that invalid/corrupted binary content in a .pdf file raises CORRUPTED_DOCUMENT or PARSING_FAILED."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        path = os.path.join(td, "corrupt.pdf")
        with open(path, "wb") as f:
            f.write(b"%PDF-1.4\nGARBAGE_CORRUPTED_BYTES_NOT_A_VALID_PDF_STRUCTURE\n%%EOF")

        with pytest.raises(AppErrorException) as exc_info:
            DocumentParserRegistry.parse(path)
        assert exc_info.value.code in (ErrorCode.CORRUPTED_DOCUMENT, ErrorCode.PARSING_FAILED)


def test_dispatcher_unknown_route_404(app_instance):
    """Verify dispatcher returns 404 for unknown endpoints."""
    res = app_instance.dispatcher.dispatch("GET", "/nonexistent/endpoint/route")
    assert res.status_code == 404
    assert res.data["code"] == "DOCUMENT_NOT_FOUND"


def test_dispatcher_unmatched_method_404(app_instance):
    """Verify dispatcher returns 404 when calling an unmatched HTTP method on a route."""
    res = app_instance.dispatcher.dispatch("PUT", "/documents")
    assert res.status_code == 404
    assert res.data["code"] == "DOCUMENT_NOT_FOUND"


def test_nonexistent_document_lookup_404(app_instance):
    """Verify dispatcher returns 404 for non-existent document ID."""
    res = app_instance.dispatcher.dispatch("GET", "/documents/nonexistent_doc_id_999")
    assert res.status_code == 404
    assert res.data["code"] == "DOCUMENT_NOT_FOUND"


def test_nonexistent_session_keystrokes_404(app_instance):
    """Verify sending keystrokes to non-existent session returns 404."""
    res = app_instance.dispatcher.dispatch(
        "POST",
        "/sessions/nonexistent_session_id/keystrokes",
        body={"keystrokes": []},
    )
    assert res.status_code == 404
    assert res.data["code"] == "SESSION_NOT_FOUND"


def test_nonexistent_note_update_404(app_instance):
    """Verify updating a non-existent note returns 404."""
    res = app_instance.dispatcher.dispatch(
        "PUT",
        "/notes/nonexistent_note_id",
        body={"content": "New content"},
    )
    assert res.status_code == 404
    assert res.data["code"] == "DOCUMENT_NOT_FOUND"


def test_typing_evaluator_backspace_at_zero():
    """Verify that backspace at position 0 does not underflow or crash."""
    evaluator = KeystrokeEvaluator(target_text="Sample")
    stroke = KeystrokeInput(timestamp_ms=1000, key="Backspace", expected_char="", position=0, is_backspace=True)
    res = evaluator.evaluate(stroke)
    assert res.is_backspace is True
    assert res.position == 0


def test_typing_evaluator_keystroke_boundary():
    """Verify keystroke evaluation rejects position beyond string bounds with POSITION_OUT_OF_BOUNDS."""
    evaluator = KeystrokeEvaluator(target_text="A")
    stroke_overflow = KeystrokeInput(timestamp_ms=1000, key="z", expected_char="", position=10, is_backspace=False)
    with pytest.raises(AppErrorException) as exc_info:
        evaluator.evaluate(stroke_overflow)
    assert exc_info.value.code == ErrorCode.POSITION_OUT_OF_BOUNDS
    assert exc_info.value.status_code == 400


def test_typing_metrics_zero_keystrokes():
    """Verify metrics calculator returns sensible zero/default values when no keystrokes are recorded."""
    calc = MetricsCalculator()
    metrics = calc.compute_metrics()
    assert metrics.total_keystrokes == 0
    assert metrics.correct_keystrokes == 0
    assert metrics.incorrect_keystrokes == 0
    assert metrics.accuracy_pct == 100.0
    assert metrics.error_rate_pct == 0.0
    assert metrics.gross_wpm == 0.0
    assert metrics.net_wpm == 0.0


def test_corrupted_backup_restore_rejection(app_instance):
    """Verify that tampering with a backup file fails validation and blocks restore."""
    with tempfile.TemporaryDirectory() as export_dir:
        resp = app_instance.backup_service.export_backup(ExportBackupRequest(destinationDirectory=export_dir))
        backup_path = resp.backupFilePath

        # Tamper with archive
        with open(backup_path, "r+b") as f:
            f.seek(50)
            f.write(b"TAMPERED_CORRUPTION")

        # Validate should report invalid
        val_res = app_instance.backup_service.validate_backup(BackupFileRequest(backupFilePath=backup_path))
        assert val_res.is_valid is False

        # Attempt to restore should raise AppErrorException
        with pytest.raises(AppErrorException) as exc_info:
            app_instance.backup_service.restore_backup(BackupFileRequest(backupFilePath=backup_path))
        assert exc_info.value.code == ErrorCode.BACKUP_CORRUPTED


def test_sqlite_foreign_key_enforcement():
    """Verify that foreign keys are strictly enforced in SQLite."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    with open(".orchestrator/blackboard/contracts/schema.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    # Try inserting chapter for non-existent document
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """
            INSERT INTO chapters (
                id, document_id, title, level, order_index, page_start, page_end,
                text_start_char, text_end_char, confidence_score, confidence_signals_json,
                included_in_practice, created_at
            ) VALUES (
                'c_1', 'nonexistent_doc_id', 'Title', 'chapter', 0, 1, 1, 0, 10, 1.0, '{}', 1, datetime('now')
            );
            """
        )
    conn.close()
