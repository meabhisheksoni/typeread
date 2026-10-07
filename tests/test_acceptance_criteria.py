"""
PRD Acceptance Criteria and System Readiness Tests.
Audits the workspace to verify implementation deliverables required by PRD.md (AC-001 through AC-010).
"""

import os
import json
import unittest
import tempfile
import socket
from pathlib import Path

import fitz  # PyMuPDF

from src.app import create_app
from src.contracts.types import (
    DocumentFormat,
    IngestionStatus,
    StructuralLevel,
    TypingMode,
    ErrorHandlingMode,
    KeystrokeInput,
    ReadingPositionPointer,
    ReadingProgressEntity,
    UserId,
    DocumentId,
    ExportBackupRequest,
    BackupFileRequest,
    CreateNoteRequest,
    CreateBookmarkRequest,
)
from src.core.document.pipeline import IngestionPipeline


class TestPRDAcceptanceCriteria(unittest.TestCase):
    """
    Verifies that the implemented codebase fulfills the Product Requirements Document (PRD) AC-001 to AC-010.
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.app = create_app(data_dir=self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_ledger_gates_completion(self):
        """Verify that preceding engineering gates (Backend, Frontend) passed."""
        ledger_path = ".orchestrator/blackboard/ledger.json"
        self.assertTrue(os.path.exists(ledger_path), "ledger.json must exist")

        with open(ledger_path, "r", encoding="utf-8") as f:
            ledger = json.load(f)

        gates = ledger.get("gates", {})
        backend_gate = gates.get("GATE_2_BACKEND", {})
        frontend_gate = gates.get("GATE_3_FRONTEND", {})

        self.assertEqual(
            backend_gate.get("status"),
            "PASSED",
            f"GATE_2_BACKEND did not pass. Status: {backend_gate.get('status')}, Evidence: {backend_gate.get('evidence')}",
        )
        self.assertEqual(
            frontend_gate.get("status"),
            "PASSED",
            f"GATE_3_FRONTEND did not pass. Status: {frontend_gate.get('status')}, Evidence: {frontend_gate.get('evidence')}",
        )

    def test_core_backend_modules_exist(self):
        """Verify that clean architecture engine files specified in ARCH_DECISIONS.md and PRD.md exist."""
        expected_locations = [
            "src/typeread/engine/document",
            "src/typeread/engine/typing",
            "src/typeread/persistence/db",
            "src/typeread/services/document_service.py",
            "src/typeread/services/typing_service.py",
        ]
        missing = [loc for loc in expected_locations if not os.path.exists(loc)]
        self.assertEqual(len(missing), 0, f"Missing required backend modules: {missing}")

    def test_frontend_ui_modules_exist(self):
        """Verify that UI modules specified in PRD.md exist."""
        expected_locations = [
            "src/typeread/ui/main_window.py",
            "src/typeread/ui/widgets/typing_widget.py",
            "src/typeread/ui/widgets/reader_widget.py",
            "src/typeread/ui/widgets/nav_tree.py",
            "src/typeread/ui/widgets/analytics_view.py",
        ]
        missing = [loc for loc in expected_locations if not os.path.exists(loc)]
        self.assertEqual(len(missing), 0, f"Missing required UI modules: {missing}")

    # =========================================================================
    # PRD Acceptance Criteria AC-001 through AC-010
    # =========================================================================

    def test_ac_001_document_import(self):
        """
        AC-001: Document Import
        Given a supported PDF
        When the user imports it
        Then the application extracts the text and creates a document entry.
        """
        doc_pdf = fitz.open()
        page = doc_pdf.new_page()
        page.insert_text((50, 72), "Chapter 1: Deep Practice", fontsize=16)
        page.insert_text((50, 110), "Deliberate practice is the core of mastery.", fontsize=12)

        pdf_path = os.path.join(self.temp_dir.name, "ac001_test.pdf")
        doc_pdf.save(pdf_path)
        doc_pdf.close()

        # Import via dispatcher
        res_import = self.app.dispatcher.dispatch("POST", "/documents/import", body={"filePath": pdf_path})
        self.assertEqual(res_import.status_code, 201)
        doc_id = res_import.data["document_id"]
        self.assertTrue(len(doc_id) > 0)
        self.assertGreater(res_import.data["statistics"]["total_words"], 0)

        # Commit document
        res_commit = self.app.dispatcher.dispatch("POST", f"/documents/{doc_id}/commit", body={"title": "Deep Practice"})
        self.assertEqual(res_commit.status_code, 201)

        # Verify document entry in database
        res_get = self.app.dispatcher.dispatch("GET", f"/documents/{doc_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.data["id"], doc_id)
        self.assertEqual(res_get.data["status"], "committed")

    def test_ac_002_existing_toc(self):
        """
        AC-002: Existing TOC
        Given a PDF with a valid outline
        When it is processed
        Then the outline becomes the document navigation tree.
        """
        doc_pdf = fitz.open()
        p1 = doc_pdf.new_page()
        p1.insert_text((50, 72), "Chapter 1: The Origin", fontsize=14)
        p1.insert_text((50, 100), "First chapter text details.", fontsize=12)

        p2 = doc_pdf.new_page()
        p2.insert_text((50, 72), "Chapter 2: Evolution", fontsize=14)
        p2.insert_text((50, 100), "Second chapter text details.", fontsize=12)

        # PyMuPDF set_toc: [[lvl, title, page]]
        doc_pdf.set_toc([
            [1, "Chapter 1: The Origin", 1],
            [1, "Chapter 2: Evolution", 2],
        ])

        pdf_path = os.path.join(self.temp_dir.name, "ac002_toc.pdf")
        doc_pdf.save(pdf_path)
        doc_pdf.close()

        pipeline = IngestionPipeline()
        preview, doc, chapters, sections, paragraphs = pipeline.process(pdf_path)

        self.assertGreaterEqual(len(chapters), 2)
        chap_titles = [c.title for c in chapters]
        self.assertTrue(any("The Origin" in t for t in chap_titles), f"Missing Chapter 1 in {chap_titles}")
        self.assertTrue(any("Evolution" in t for t in chap_titles), f"Missing Chapter 2 in {chap_titles}")

    def test_ac_003_missing_toc(self):
        """
        AC-003: Missing TOC
        Given a PDF without a usable outline
        When it is processed
        Then the application attempts deterministic heading detection.
        """
        doc_pdf = fitz.open()
        p = doc_pdf.new_page()
        # Large font heading, no TOC outline embedded
        p.insert_text((50, 60), "Chapter 1: Clean Architecture", fontsize=22)
        p.insert_text((50, 100), "Principles of dependency inversion and separation of concerns.", fontsize=12)
        p.insert_text((50, 150), "Section 1.1: Boundaries", fontsize=16)
        p.insert_text((50, 190), "Keeping core business logic decoupled from UI and storage.", fontsize=12)

        pdf_path = os.path.join(self.temp_dir.name, "ac003_no_toc.pdf")
        doc_pdf.save(pdf_path)
        doc_pdf.close()

        pipeline = IngestionPipeline()
        preview, doc, chapters, sections, paragraphs = pipeline.process(pdf_path)

        self.assertGreaterEqual(len(chapters), 1)
        self.assertGreaterEqual(len(sections), 1)
        # Check that heading confidence was calculated deterministically
        self.assertGreaterEqual(chapters[0].confidence.score, 0.65)
        self.assertIn("Clean Architecture", chapters[0].title)

    def test_ac_004_manual_correction(self):
        """
        AC-004: Manual Correction
        Given incorrect structure detection
        When the user edits the structure
        Then the final navigation reflects those changes.
        """
        # Create doc and import
        txt_path = os.path.join(self.temp_dir.name, "ac004_test.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("Line 1 text body\nLine 2 text body\n")

        res_import = self.app.dispatcher.dispatch("POST", "/documents/import", body={"filePath": txt_path})
        doc_id = res_import.data["document_id"]

        # Commit with custom edited title
        res_commit = self.app.dispatcher.dispatch(
            "POST",
            f"/documents/{doc_id}/commit",
            body={"title": "Manually Corrected Title", "chapters": []},
        )
        self.assertEqual(res_commit.status_code, 201)
        self.assertEqual(res_commit.data["title"], "Manually Corrected Title")

        # Get structure
        res_struct = self.app.dispatcher.dispatch("GET", f"/documents/{doc_id}/structure")
        chap_id = res_struct.data["chapters"][0]["id"]

        # Update exclusion manually
        res_excl = self.app.dispatcher.dispatch(
            "PATCH",
            f"/documents/{doc_id}/exclusions",
            body={"targetType": "chapter", "targetId": chap_id, "includedInPractice": False},
        )
        self.assertEqual(res_excl.status_code, 200)

        # Verify exclusion took effect in navigation structure
        res_updated_struct = self.app.dispatcher.dispatch("GET", f"/documents/{doc_id}/structure")
        self.assertFalse(res_updated_struct.data["chapters"][0]["includedInPractice"])

    def test_ac_005_typing(self):
        """
        AC-005: Typing
        Given an imported document
        When the user starts a typing session
        Then every input character is evaluated and session metrics are updated.
        """
        txt_path = os.path.join(self.temp_dir.name, "ac005_typing.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("TypeRead Practice Session Text")

        res_imp = self.app.dispatcher.dispatch("POST", "/documents/import", body={"filePath": txt_path})
        doc_id = res_imp.data["document_id"]
        self.app.dispatcher.dispatch("POST", f"/documents/{doc_id}/commit", body={"title": "Typing Doc"})

        res_struct = self.app.dispatcher.dispatch("GET", f"/documents/{doc_id}/structure")
        chap_id = res_struct.data["chapters"][0]["id"]
        sec_id = res_struct.data["chapters"][0]["sections"][0]["id"]

        # Start typing session
        res_start = self.app.dispatcher.dispatch(
            "POST",
            "/sessions/start",
            body={
                "documentId": doc_id,
                "chapterId": chap_id,
                "sectionId": sec_id,
                "typingMode": "standard",
                "errorHandlingMode": "allow_with_backspace",
            },
        )
        self.assertEqual(res_start.status_code, 201)
        sess_id = res_start.data["id"]

        # Send keystrokes: 'T' (correct), 'y' (correct), 'x' (incorrect for 'p')
        strokes = [
            {"timestamp_ms": 1000, "key": "T", "expected_char": "T", "position": 0, "is_backspace": False},
            {"timestamp_ms": 1150, "key": "y", "expected_char": "y", "position": 1, "is_backspace": False},
            {"timestamp_ms": 1300, "key": "x", "expected_char": "p", "position": 2, "is_backspace": False},
        ]
        res_strokes = self.app.dispatcher.dispatch("POST", f"/sessions/{sess_id}/keystrokes", body={"keystrokes": strokes})
        self.assertEqual(res_strokes.status_code, 200)

        metrics = res_strokes.data["currentMetrics"]
        self.assertEqual(metrics["total_keystrokes"], 3)
        self.assertEqual(metrics["correct_keystrokes"], 2)
        self.assertEqual(metrics["incorrect_keystrokes"], 1)
        self.assertAlmostEqual(metrics["accuracy_pct"], 66.67, delta=1.0)

    def test_ac_006_progress(self):
        """
        AC-006: Progress
        Given a partially completed section
        When the application closes
        Then reopening the document resumes from the exact saved position.
        """
        txt_path = os.path.join(self.temp_dir.name, "ac006_progress.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("A long passage of text for bookmarking and position tracking.")

        res_imp = self.app.dispatcher.dispatch("POST", "/documents/import", body={"filePath": txt_path})
        doc_id = res_imp.data["document_id"]
        self.app.dispatcher.dispatch("POST", f"/documents/{doc_id}/commit", body={"title": "Progress Doc"})

        res_struct = self.app.dispatcher.dispatch("GET", f"/documents/{doc_id}/structure")
        chap_id = res_struct.data["chapters"][0]["id"]
        sec_id = res_struct.data["chapters"][0]["sections"][0]["id"]
        content = self.app.dispatcher.dispatch("GET", f"/documents/{doc_id}/sections/{sec_id}/content")
        p_id = content.data["paragraphs"][0]["id"]

        # Save progress at exact character offset 25
        saved_pointer = ReadingPositionPointer(
            document_id=doc_id,
            chapter_id=chap_id,
            section_id=sec_id,
            paragraph_id=p_id,
            character_offset=25,
        )
        prog_entity = ReadingProgressEntity(
            id="prog_ac006",
            user_id=UserId("default_user"),
            document_id=DocumentId(doc_id),
            position=saved_pointer,
            completion_percentage=40.0,
            is_completed=False,
            last_practiced_at="2026-10-07T00:00:00Z",
            updated_at="2026-10-07T00:00:00Z",
        )
        self.app.progress_repo.save_progress(prog_entity)

        # Simulate app closing and restarting with a new application container instance
        restarted_app = create_app(data_dir=self.temp_dir.name)
        recovered_progress = restarted_app.progress_repo.get_progress("default_user", doc_id)

        self.assertIsNotNone(recovered_progress)
        self.assertEqual(recovered_progress.position.character_offset, 25)
        self.assertEqual(recovered_progress.position.section_id, sec_id)
        self.assertEqual(recovered_progress.position.paragraph_id, p_id)

    def test_ac_007_offline(self):
        """
        AC-007: Offline
        Given no Internet connection
        When the user opens the application
        Then all Phase 1 core functionality remains available.
        """
        # Monkeypatch socket to ensure no network calls can succeed
        orig_socket = socket.socket

        def guarded_socket(*args, **kwargs):
            raise OSError("Network connection forbidden: strictly offline-first application")

        socket.socket = guarded_socket  # type: ignore
        try:
            # Execute full pipeline: import -> commit -> type -> search -> analytics completely offline
            txt_path = os.path.join(self.temp_dir.name, "ac007_offline.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("Offline first software architecture with zero network dependencies.")

            res_imp = self.app.dispatcher.dispatch("POST", "/documents/import", body={"filePath": txt_path})
            self.assertEqual(res_imp.status_code, 201)
            doc_id = res_imp.data["document_id"]

            res_commit = self.app.dispatcher.dispatch("POST", f"/documents/{doc_id}/commit", body={"title": "Offline Book"})
            self.assertEqual(res_commit.status_code, 201)

            res_search = self.app.dispatcher.dispatch("POST", "/search", body={"query": "architecture"})
            self.assertEqual(res_search.status_code, 200)
            self.assertGreaterEqual(res_search.data["total_matches"], 1)

            res_an = self.app.dispatcher.dispatch("GET", "/analytics/overview")
            self.assertEqual(res_an.status_code, 200)
        finally:
            socket.socket = orig_socket

    def test_ac_008_search(self):
        """
        AC-008: Search
        Given a document with known text
        When the user searches a phrase
        Then matching passages are displayed and selectable.
        """
        txt_path = os.path.join(self.temp_dir.name, "ac008_search.txt")
        unique_phrase = "QuantumComputingSupremacy2026"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"This text discusses {unique_phrase} in full cryptographic detail.")

        res_imp = self.app.dispatcher.dispatch("POST", "/documents/import", body={"filePath": txt_path})
        doc_id = res_imp.data["document_id"]
        self.app.dispatcher.dispatch("POST", f"/documents/{doc_id}/commit", body={"title": "Search Document"})

        # Search for unique phrase
        res_search = self.app.dispatcher.dispatch("POST", "/search", body={"query": unique_phrase})
        self.assertEqual(res_search.status_code, 200)
        self.assertEqual(res_search.data["total_matches"], 1)
        item = res_search.data["items"][0]
        self.assertEqual(item["document_id"], doc_id)
        self.assertIn(unique_phrase, item["matched_snippet"])
        self.assertTrue(len(item["paragraph_id"]) > 0)

    def test_ac_009_backup(self):
        """
        AC-009: Backup
        Given a populated library
        When the user exports a backup
        Then documents, metadata, progress, notes, and settings can be restored.
        """
        # 1. Populate library with document, bookmark, and note
        txt_path = os.path.join(self.temp_dir.name, "ac009_backup.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("Important backup test content.")

        res_imp = self.app.dispatcher.dispatch("POST", "/documents/import", body={"filePath": txt_path})
        doc_id = res_imp.data["document_id"]
        self.app.dispatcher.dispatch("POST", f"/documents/{doc_id}/commit", body={"title": "Backup Document"})

        res_struct = self.app.dispatcher.dispatch("GET", f"/documents/{doc_id}/structure")
        chap_id = res_struct.data["chapters"][0]["id"]
        sec_id = res_struct.data["chapters"][0]["sections"][0]["id"]
        content = self.app.dispatcher.dispatch("GET", f"/documents/{doc_id}/sections/{sec_id}/content")
        p_id = content.data["paragraphs"][0]["id"]

        # Add note
        res_note = self.app.dispatcher.dispatch(
            "POST",
            "/notes",
            body={
                "documentId": doc_id,
                "chapterId": chap_id,
                "sectionId": sec_id,
                "paragraphId": p_id,
                "content": "A precious study note",
            },
        )
        self.assertEqual(res_note.status_code, 201)

        # 2. Export backup
        export_dir = os.path.join(self.temp_dir.name, "backups")
        os.makedirs(export_dir, exist_ok=True)
        res_export = self.app.dispatcher.dispatch("POST", "/backup/export", body={"destinationDirectory": export_dir})
        self.assertEqual(res_export.status_code, 201)
        backup_file = res_export.data["backupFilePath"]
        self.assertTrue(os.path.exists(backup_file))

        # 3. Create fresh app container (new empty database)
        fresh_dir = os.path.join(self.temp_dir.name, "fresh_installation")
        fresh_app = create_app(data_dir=fresh_dir)

        # Restore into fresh installation
        res_restore = fresh_app.dispatcher.dispatch("POST", "/backup/restore", body={"backupFilePath": backup_file})
        self.assertEqual(res_restore.status_code, 200)
        self.assertTrue(res_restore.data["success"])

        # 4. Verify document and note restored in fresh installation
        restored_doc = fresh_app.dispatcher.dispatch("GET", f"/documents/{doc_id}")
        self.assertEqual(restored_doc.status_code, 200)
        self.assertEqual(restored_doc.data["title"], "Backup Document")

        restored_notes = fresh_app.dispatcher.dispatch("GET", "/notes", params={"documentId": doc_id})
        self.assertEqual(restored_notes.status_code, 200)
        self.assertEqual(len(restored_notes.data), 1)
        self.assertEqual(restored_notes.data[0]["content"], "A precious study note")

    def test_ac_010_no_ai_dependency(self):
        """
        AC-010: No AI Dependency
        Given a clean installation
        When no AI/API configuration exists
        Then the application starts and functions normally.
        """
        # Ensure AI environment variables are stripped
        for ai_key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "CLAUDE_API_KEY"]:
            if ai_key in os.environ:
                del os.environ[ai_key]

        clean_dir = os.path.join(self.temp_dir.name, "no_ai_test")
        clean_app = create_app(data_dir=clean_dir)

        # Verify application boots and settings retrieve cleanly
        res_settings = clean_app.dispatcher.dispatch("GET", "/settings")
        self.assertEqual(res_settings.status_code, 200)
        self.assertEqual(res_settings.data["general"]["autosave_interval_seconds"], 10)
        self.assertEqual(res_settings.data["general"]["startup_behavior"], "resume_last")

        # Verify drill generation functions deterministically without LLM calls
        res_drill = clean_app.dispatcher.dispatch(
            "POST",
            "/practice/drills/generate",
            body={"targetKeys": ["a", "s", "d", "f"], "wordCount": 15},
        )
        self.assertEqual(res_drill.status_code, 200)
        self.assertEqual(res_drill.data["word_count"], 15)
        self.assertTrue(len(res_drill.data["generated_passage"]) > 0)


if __name__ == "__main__":
    unittest.main()
