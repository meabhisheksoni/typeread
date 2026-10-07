"""
Unit tests for SQLite schema, persistence, WAL mode, FTS5 triggers, and repositories.
"""

import tempfile
import pytest
from pathlib import Path

from src.contracts.types import (
    DocumentEntity,
    ChapterEntity,
    SectionEntity,
    ParagraphEntity,
    StructuralLevel,
    DocumentFormat,
    IngestionStatus,
    ProcessingProfile,
    CharacterOffsetMap,
    TextRepresentations,
    StructuralNodeConfidence,
    StructuralNodeSignals,
    SearchQuery,
    CreateBookmarkRequest,
    CreateNoteRequest,
)
from src.storage.db import Database
from src.storage.repositories.document_repo import DocumentRepository
from src.storage.repositories.search_repo import SearchRepository
from src.storage.repositories.bookmarks_repo import BookmarkRepository
from src.storage.repositories.notes_repo import NoteRepository


@pytest.fixture
def test_db():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        db_path = str(Path(td) / "test.db")
        db = Database(db_path=db_path)
        yield db


def test_schema_and_fts_integration(test_db):
    doc_repo = DocumentRepository(db=test_db)
    search_repo = SearchRepository(db=test_db)

    # Create dummy entities
    doc = DocumentEntity(
        id="doc_1",
        user_id="default_user",
        title="Atomic Habits",
        author="James Clear",
        file_name="habits.md",
        file_path="/habits.md",
        file_hash="hash_123",
        source_format=DocumentFormat.MARKDOWN,
        word_count=50,
        character_count=300,
        status=IngestionStatus.COMMITTED,
        processing_profile=ProcessingProfile(),
        created_at="2026-10-07T00:00:00Z",
        updated_at="2026-10-07T00:00:00Z",
    )
    chap = ChapterEntity(
        id="chap_1",
        document_id="doc_1",
        parent_id=None,
        title="The Fundamentals",
        level=StructuralLevel.CHAPTER,
        order_index=0,
        page_start=1,
        page_end=1,
        text_start_char=0,
        text_end_char=300,
        confidence=StructuralNodeConfidence(
            score=1.0,
            signals=StructuralNodeSignals(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0),
        ),
        included_in_practice=True,
        created_at="2026-10-07T00:00:00Z",
    )
    sec = SectionEntity(
        id="sec_1",
        document_id="doc_1",
        chapter_id="chap_1",
        title="Tiny Changes",
        order_index=0,
        page_start=1,
        page_end=1,
        text_start_char=0,
        text_end_char=300,
        word_count=50,
        character_count=300,
        included_in_practice=True,
        created_at="2026-10-07T00:00:00Z",
    )
    para = ParagraphEntity(
        id="p_1",
        document_id="doc_1",
        chapter_id="chap_1",
        section_id="sec_1",
        order_index=0,
        representations=TextRepresentations(
            source_text="Small habits make a massive compounding difference over time.",
            normalized_text="Small habits make a massive compounding difference over time.",
            display_text="Small habits make a massive compounding difference over time.",
            typing_text="Small habits make a massive compounding difference over time.",
            offset_map=CharacterOffsetMap(
                typing_to_display_indices=tuple(range(61)),
                display_to_source_indices=tuple(range(61)),
            ),
        ),
        source_page=1,
        source_position_y=10.0,
        created_at="2026-10-07T00:00:00Z",
    )

    doc_repo.save_document(doc, [chap], [sec], [para])

    # Verify retrieval
    retrieved = doc_repo.get_document_by_id("doc_1")
    assert retrieved is not None
    assert retrieved.title == "Atomic Habits"

    # Verify FTS5 trigger automatic indexing
    search_res = search_repo.search(SearchQuery(query="compounding"))
    assert search_res.total_matches == 1
    assert search_res.items[0].document_id == "doc_1"
    assert "compounding" in search_res.items[0].matched_snippet.lower()


def test_bookmarks_and_notes(test_db):
    bm_repo = BookmarkRepository(db=test_db)
    note_repo = NoteRepository(db=test_db)
    doc_repo = DocumentRepository(db=test_db)

    # First add a document so foreign keys pass
    doc = DocumentEntity(
        id="doc_2",
        user_id="default_user",
        title="Doc 2",
        author="Author",
        file_name="doc.txt",
        file_path="/doc.txt",
        file_hash="hash_456",
        source_format=DocumentFormat.TXT,
        word_count=10,
        character_count=50,
        status=IngestionStatus.COMMITTED,
        processing_profile=ProcessingProfile(),
        created_at="2026-10-07T00:00:00Z",
        updated_at="2026-10-07T00:00:00Z",
    )
    chap = ChapterEntity(
        id="c_2",
        document_id="doc_2",
        parent_id=None,
        title="Chapter",
        level=StructuralLevel.CHAPTER,
        order_index=0,
        page_start=1,
        page_end=1,
        text_start_char=0,
        text_end_char=50,
        confidence=StructuralNodeConfidence(score=1.0, signals=StructuralNodeSignals(1, 1, 1, 1, 1, 1, 0)),
        included_in_practice=True,
        created_at="2026-10-07T00:00:00Z",
    )
    sec = SectionEntity(
        id="s_2",
        document_id="doc_2",
        chapter_id="c_2",
        title="Sec",
        order_index=0,
        page_start=1,
        page_end=1,
        text_start_char=0,
        text_end_char=50,
        word_count=10,
        character_count=50,
        included_in_practice=True,
        created_at="2026-10-07T00:00:00Z",
    )
    para = ParagraphEntity(
        id="p_2",
        document_id="doc_2",
        chapter_id="c_2",
        section_id="s_2",
        order_index=0,
        representations=TextRepresentations(
            source_text="Test",
            normalized_text="Test",
            display_text="Test",
            typing_text="Test",
            offset_map=CharacterOffsetMap(typing_to_display_indices=(0, 1, 2, 3), display_to_source_indices=(0, 1, 2, 3)),
        ),
        source_page=1,
        source_position_y=0,
        created_at="2026-10-07T00:00:00Z",
    )
    doc_repo.save_document(doc, [chap], [sec], [para])

    # Bookmark
    bm = bm_repo.create_bookmark(
        user_id="default_user",
        req=CreateBookmarkRequest(
            documentId="doc_2",
            chapterId="c_2",
            sectionId="s_2",
            paragraphId="p_2",
            characterOffset=10,
            title="My Bookmark",
        ),
    )
    assert bm.title == "My Bookmark"
    assert len(bm_repo.list_bookmarks("default_user")) == 1

    # Note
    note = note_repo.create_note(
        user_id="default_user",
        req=CreateNoteRequest(
            documentId="doc_2",
            chapterId="c_2",
            sectionId="s_2",
            paragraphId="p_2",
            content="Important insight",
        ),
    )
    assert note.content == "Important insight"
    updated_note = note_repo.update_note(user_id="default_user", note_id=str(note.id), content="Updated insight")
    assert updated_note.content == "Updated insight"
