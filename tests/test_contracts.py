"""
Integration and Boundary Tests for TypeRead Architectural Contracts & Data Models
Tests types.py, schema.sql, and api.json specifications.
"""

import sys
import os
import json
import sqlite3
import unittest
import importlib.util
from dataclasses import FrozenInstanceError

# Load contract module from path to avoid colliding with stdlib 'types'
contracts_path = os.path.abspath(".orchestrator/blackboard/contracts/types.py")
spec = importlib.util.spec_from_file_location("contract_types", contracts_path)
contract_types = importlib.util.module_from_spec(spec)
sys.modules["contract_types"] = contract_types
spec.loader.exec_module(contract_types)

ProcessingProfile = contract_types.ProcessingProfile
CharacterOffsetMap = contract_types.CharacterOffsetMap
TextRepresentations = contract_types.TextRepresentations
StructuralNodeSignals = contract_types.StructuralNodeSignals
StructuralNodeConfidence = contract_types.StructuralNodeConfidence
DocumentFormat = contract_types.DocumentFormat
IngestionStatus = contract_types.IngestionStatus
StructuralLevel = contract_types.StructuralLevel
TypingMode = contract_types.TypingMode
ErrorHandlingMode = contract_types.ErrorHandlingMode
ErrorCode = contract_types.ErrorCode
AppError = contract_types.AppError
ErrorDetail = contract_types.ErrorDetail
DocumentEntity = contract_types.DocumentEntity
ChapterEntity = contract_types.ChapterEntity
TypingMetrics = contract_types.TypingMetrics
TypingSessionEntity = contract_types.TypingSessionEntity
TypingSessionState = contract_types.TypingSessionState
ReadingPositionPointer = contract_types.ReadingPositionPointer
UserId = contract_types.UserId
DocumentId = contract_types.DocumentId
ChapterId = contract_types.ChapterId
SectionId = contract_types.SectionId
ParagraphId = contract_types.ParagraphId
SessionId = contract_types.SessionId


class TestContractTypes(unittest.TestCase):
    """Test domain models, strict invariants, boundary conditions, and immutability."""

    def test_processing_profile_defaults_and_valid_bounds(self):
        profile = ProcessingProfile()
        self.assertTrue(profile.remove_headers)
        self.assertTrue(profile.remove_footers)
        self.assertEqual(profile.min_heading_confidence, 0.65)

    def test_processing_profile_confidence_boundaries(self):
        # Valid boundary values: 0.0 and 1.0
        p_min = ProcessingProfile(min_heading_confidence=0.0)
        self.assertEqual(p_min.min_heading_confidence, 0.0)
        p_max = ProcessingProfile(min_heading_confidence=1.0)
        self.assertEqual(p_max.min_heading_confidence, 1.0)

        # Invalid boundaries: < 0.0 or > 1.0
        with self.assertRaises(ValueError):
            ProcessingProfile(min_heading_confidence=-0.01)

        with self.assertRaises(ValueError):
            ProcessingProfile(min_heading_confidence=1.01)

    def test_structural_node_confidence_boundaries(self):
        signals = StructuralNodeSignals(
            font_size_score=0.9,
            bold_weight_score=1.0,
            numbering_score=0.8,
            position_score=0.7,
            whitespace_score=0.5,
            short_line_score=0.6,
            paragraph_length_penalty=0.0,
        )

        # Valid score
        conf = StructuralNodeConfidence(score=0.85, signals=signals)
        self.assertEqual(conf.score, 0.85)

        # Invalid bounds
        with self.assertRaises(ValueError):
            StructuralNodeConfidence(score=-0.1, signals=signals)

        with self.assertRaises(ValueError):
            StructuralNodeConfidence(score=1.05, signals=signals)

    def test_text_representations_invariant_offset_match(self):
        text = "Hello World"
        offset_map = CharacterOffsetMap(
            typing_to_display_indices=tuple(range(len(text))),
            display_to_source_indices=tuple(range(len(text))),
        )
        rep = TextRepresentations(
            source_text=text,
            normalized_text=text,
            display_text=text,
            typing_text=text,
            offset_map=offset_map,
        )
        self.assertEqual(rep.typing_text, text)

    def test_text_representations_invariant_mismatch_raises_error(self):
        text = "Hello World"
        # Mismatched offset map length
        bad_offset_map = CharacterOffsetMap(
            typing_to_display_indices=(0, 1, 2),  # only 3 elements instead of 11
            display_to_source_indices=tuple(range(len(text))),
        )
        with self.assertRaises(ValueError):
            TextRepresentations(
                source_text=text,
                normalized_text=text,
                display_text=text,
                typing_text=text,
                offset_map=bad_offset_map,
            )

    def test_immutability_frozen_dataclasses(self):
        profile = ProcessingProfile()
        with self.assertRaises(FrozenInstanceError):
            profile.remove_headers = False  # type: ignore

    def test_null_value_handling_in_chapter_entity(self):
        signals = StructuralNodeSignals(
            font_size_score=0.8,
            bold_weight_score=0.9,
            numbering_score=1.0,
            position_score=0.5,
            whitespace_score=0.5,
            short_line_score=0.5,
            paragraph_length_penalty=0.0,
        )
        conf = StructuralNodeConfidence(score=0.9, signals=signals)

        # Root chapter with parent_id=None
        root_chapter = ChapterEntity(
            id=ChapterId("chap_001"),
            document_id=DocumentId("doc_001"),
            parent_id=None,
            title="Chapter 1: The Beginning",
            level=StructuralLevel.CHAPTER,
            order_index=1,
            page_start=1,
            page_end=20,
            text_start_char=0,
            text_end_char=5000,
            confidence=conf,
            included_in_practice=True,
            created_at="2026-10-07T00:00:00Z",
        )
        self.assertIsNone(root_chapter.parent_id)

    def test_app_error_structure(self):
        err = AppError(
            code=ErrorCode.CORRUPTED_DOCUMENT,
            message="Document stream truncated",
            timestamp="2026-10-07T00:00:00Z",
            recoverable=False,
            details=[ErrorDetail(message="Unexpected EOF at byte 1024", field="file_path")],
            suggested_action="Re-import the original file.",
        )
        self.assertEqual(err.code, ErrorCode.CORRUPTED_DOCUMENT)
        self.assertFalse(err.recoverable)
        self.assertEqual(len(err.details), 1)


class TestDatabaseSchema(unittest.TestCase):
    """Test SQL schema contract execution in SQLite."""

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("PRAGMA foreign_keys = ON;")
        with open(".orchestrator/blackboard/contracts/schema.sql", "r", encoding="utf-8") as f:
            self.schema_sql = f.read()
        self.conn.executescript(self.schema_sql)

    def tearDown(self):
        self.conn.close()

    def test_tables_created(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        expected_tables = {
            "users",
            "documents",
            "document_versions",
            "chapters",
            "sections",
            "paragraphs",
            "typing_sessions",
            "typing_errors",
            "reading_progress",
            "bookmarks",
            "notes",
            "user_settings",
            "schema_migrations",
            "weak_key_aggregates",
            "weak_bigram_aggregates",
            "daily_streaks",
        }
        for table in expected_tables:
            self.assertIn(table, tables, f"Expected table '{table}' not found in schema")

    def test_foreign_key_enforcement(self):
        cursor = self.conn.cursor()
        # Insert a document without existing user should fail FK constraint
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute(
                """
                INSERT INTO documents (
                    id, user_id, title, author, file_name, file_path, file_hash,
                    source_format, word_count, character_count, status, processing_profile_json,
                    created_at, updated_at
                ) VALUES (
                    'doc_1', 'nonexistent_user', 'Title', 'Author', 'file.txt', '/path', 'hash123',
                    'txt', 100, 500, 'committed', '{}', datetime('now'), datetime('now')
                );
                """
            )


class TestApiContract(unittest.TestCase):
    """Test api.json architectural contract validity."""

    def test_api_json_structure(self):
        with open(".orchestrator/blackboard/contracts/api.json", "r", encoding="utf-8") as f:
            api_spec = json.load(f)

        self.assertIn("openapi", api_spec)
        self.assertIn("info", api_spec)
        self.assertIn("paths", api_spec)
        self.assertIn("components", api_spec)
        self.assertTrue(len(api_spec["paths"]) > 0, "api.json must define API paths")


if __name__ == "__main__":
    unittest.main()
