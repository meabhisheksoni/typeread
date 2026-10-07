"""
Unit tests for Weak-Key Aggregator, Drill Generator, and Crash Recovery / Session Resume.
"""

import tempfile
import pytest
from src.contracts.types import (
    TypingErrorRecord,
    SessionId,
    UserId,
    DocumentId,
    SectionId,
    TypingSessionState,
    TypingSessionEntity,
    TypingMetrics,
    TypingMode,
    ReadingPositionPointer,
    ParagraphId,
    ChapterId,
    DocumentEntity,
    ChapterEntity,
    SectionEntity,
    ParagraphEntity,
    DocumentFormat,
    IngestionStatus,
    ProcessingProfile,
    TextRepresentations,
    CharacterOffsetMap,
    StructuralLevel,
    StructuralNodeConfidence,
    StructuralNodeSignals,
)
from src.core.practice.weak_keys import WeakKeyAggregator
from src.core.practice.drills import DrillGenerator
from src.app import create_app


def test_weak_key_aggregator():
    errors = [
        TypingErrorRecord(
            id="1", session_id=SessionId("s1"), document_id=DocumentId("d1"), section_id=SectionId("sec1"),
            expected_char="t", actual_char="r", position=0, timestamp_ms=1000, resolved_via_backspace=False,
        ),
        TypingErrorRecord(
            id="2", session_id=SessionId("s1"), document_id=DocumentId("d1"), section_id=SectionId("sec1"),
            expected_char="h", actual_char="g", position=1, timestamp_ms=1200, resolved_via_backspace=False,
        ),
        TypingErrorRecord(
            id="3", session_id=SessionId("s1"), document_id=DocumentId("d1"), section_id=SectionId("sec1"),
            expected_char="t", actual_char="y", position=5, timestamp_ms=2000, resolved_via_backspace=False,
        ),
    ]

    char_totals = {"t": 10, "h": 5}
    bg_totals = {"th": 5}

    weak_keys, weak_bigrams = WeakKeyAggregator.aggregate_errors(errors, char_totals, bg_totals)

    assert len(weak_keys) >= 2
    top_key = weak_keys[0]
    assert top_key.character == "t"
    assert top_key.error_count == 2
    assert len(top_key.common_substitutions) == 2

    assert len(weak_bigrams) == 1
    assert weak_bigrams[0].bigram == "th"
    assert weak_bigrams[0].error_count == 1


def test_drill_generator():
    drill = DrillGenerator.generate(
        target_keys=["t", "h"],
        target_bigrams=["th"],
        word_count=30,
    )
    assert drill.word_count == 30
    assert len(drill.generated_passage.split()) == 30
    assert "t" in drill.target_keys


def test_crash_recovery_and_resume():
    with tempfile.TemporaryDirectory() as data_dir:
        app = create_app(data_dir=data_dir)

        # Insert prerequisite document, chapter, and section
        doc = DocumentEntity(
            id=DocumentId("doc_crashed"),
            user_id=UserId("default_user"),
            title="Crashed Doc",
            author="Author",
            file_name="doc.txt",
            file_path="/doc.txt",
            file_hash="hash_crashed",
            source_format=DocumentFormat.TXT,
            word_count=20,
            character_count=100,
            status=IngestionStatus.COMMITTED,
            processing_profile=ProcessingProfile(),
            created_at="2026-10-07T00:00:00Z",
            updated_at="2026-10-07T00:00:00Z",
        )
        chap = ChapterEntity(
            id=ChapterId("chap_crashed"),
            document_id=DocumentId("doc_crashed"),
            parent_id=None,
            title="Chapter 1",
            level=StructuralLevel.CHAPTER,
            order_index=0,
            page_start=1,
            page_end=1,
            text_start_char=0,
            text_end_char=100,
            confidence=StructuralNodeConfidence(score=1.0, signals=StructuralNodeSignals(1, 1, 1, 1, 1, 1, 0)),
            included_in_practice=True,
            created_at="2026-10-07T00:00:00Z",
        )
        sec = SectionEntity(
            id=SectionId("sec_crashed"),
            document_id=DocumentId("doc_crashed"),
            chapter_id=ChapterId("chap_crashed"),
            title="Section 1",
            order_index=0,
            page_start=1,
            page_end=1,
            text_start_char=0,
            text_end_char=100,
            word_count=20,
            character_count=100,
            included_in_practice=True,
            created_at="2026-10-07T00:00:00Z",
        )
        para = ParagraphEntity(
            id=ParagraphId("para_crashed"),
            document_id=DocumentId("doc_crashed"),
            chapter_id=ChapterId("chap_crashed"),
            section_id=SectionId("sec_crashed"),
            order_index=0,
            representations=TextRepresentations(
                source_text="Test",
                normalized_text="Test",
                display_text="Test",
                typing_text="Test",
                offset_map=CharacterOffsetMap((0, 1, 2, 3), (0, 1, 2, 3)),
            ),
            source_page=1,
            source_position_y=0,
            created_at="2026-10-07T00:00:00Z",
        )
        app.doc_repo.save_document(doc, [chap], [sec], [para])

        # Simulate a session left in 'active' state due to sudden crash
        active_session = TypingSessionEntity(
            id=SessionId("crashed_sess_1"),
            user_id=UserId("default_user"),
            document_id=DocumentId("doc_crashed"),
            chapter_id=ChapterId("chap_crashed"),
            section_id=SectionId("sec_crashed"),
            start_time="2026-10-07T00:00:00Z",
            state=TypingSessionState.ACTIVE,
            typing_mode=TypingMode.STANDARD,
            metrics=TypingMetrics(
                net_wpm=45.0, gross_wpm=50.0, accuracy_pct=95.0, error_rate_pct=5.0,
                total_keystrokes=100, correct_keystrokes=95, incorrect_keystrokes=5,
                backspace_count=3, active_seconds=25.0, consistency_pct=90.0,
            ),
            completed=False,
            created_at="2026-10-07T00:00:00Z",
            end_time=None,
        )
        app.session_repo.save_session(active_session)

        # On next startup (simulated by querying get_active_session)
        recovered = app.typing_service.get_active_session("default_user")
        assert recovered is not None
        assert recovered.id == "crashed_sess_1"
        assert recovered.state == TypingSessionState.ACTIVE
        assert recovered.completed is False
