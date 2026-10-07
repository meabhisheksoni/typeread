"""
Unit tests for the document parsing, text normalization, heading heuristics, and offset maps.
"""

import tempfile
import pytest
from pathlib import Path

from src.contracts.types import (
    DocumentFormat,
    ProcessingProfile,
    TypingMode,
    StructuralLevel,
)
from src.core.document.parsers import DocumentParserRegistry, RawDocumentContent, RawPage, RawLine
from src.core.document.normalizer import TextNormalizer
from src.core.document.heuristics import HeadingClassifier
from src.core.document.representations import TextRepresentationBuilder
from src.core.document.pipeline import IngestionPipeline


def test_markdown_and_txt_parsers():
    # Markdown test
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write("# Chapter 1: Foundations\nThis is paragraph one.\n\n## Section 1.1\nAnother paragraph.")
        md_path = f.name

    doc = DocumentParserRegistry.parse(md_path)
    assert doc.format == DocumentFormat.MARKDOWN
    assert len(doc.pages) >= 1
    headings = [l for p in doc.pages for l in p.lines if l.is_heading_hint]
    assert len(headings) == 2
    assert headings[0].text == "Chapter 1: Foundations"
    assert headings[1].text == "Section 1.1"

    # TXT test
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("Line 1\nLine 2\nLine 3")
        txt_path = f.name

    txt_doc = DocumentParserRegistry.parse(txt_path)
    assert txt_doc.format == DocumentFormat.TXT
    assert len(txt_doc.pages[0].lines) == 3


def test_text_normalizer_cleaning():
    # Simulate multi-page document with repeated headers, footers, page numbers, and hyphenation
    page1 = RawPage(
        page_number=1,
        lines=[
            RawLine(text="TypeRead User Guide", page_number=1),  # Header
            RawLine(text="1", page_number=1),                    # Page number
            RawLine(text="This is an impor-", page_number=1),     # Hyphenation start
            RawLine(text="tant concept in reading.", page_number=1),
            RawLine(text="Copyright 2026", page_number=1),        # Footer
        ],
    )
    page2 = RawPage(
        page_number=2,
        lines=[
            RawLine(text="TypeRead User Guide", page_number=2),  # Header
            RawLine(text="2", page_number=2),                    # Page number
            RawLine(text="Second page body line.", page_number=2),
            RawLine(text="Copyright 2026", page_number=2),        # Footer
        ],
    )

    raw_doc = RawDocumentContent(
        title="Test",
        author="Author",
        format=DocumentFormat.TXT,
        pages=[page1, page2],
    )

    normalizer = TextNormalizer(profile=ProcessingProfile())
    cleaned_pages, stats, samples = normalizer.process(raw_doc)

    assert stats.removed_headers_count >= 2
    assert stats.removed_footers_count >= 2
    assert stats.removed_page_numbers_count >= 2
    assert stats.repaired_hyphenations_count >= 1

    # Verify repaired hyphenation
    p1_texts = [l.text for l in cleaned_pages[0].lines]
    assert any("important" in t for t in p1_texts)


def test_heading_classifier():
    classifier = HeadingClassifier(min_confidence=0.65)

    chap_line = RawLine(text="Chapter 1. Introduction", page_number=1, font_size=18.0, is_bold=True)
    conf, is_heading, level = classifier.score_line(chap_line, line_idx=0, total_lines_on_page=10, median_font_size=12.0)
    assert is_heading is True
    assert conf.score >= 0.70
    assert level == StructuralLevel.CHAPTER

    body_line = RawLine(
        text="This is an ordinary sentence inside the paragraph discussing behavior change and daily routines.",
        page_number=1,
        font_size=12.0,
        is_bold=False,
    )
    conf_body, is_body_heading, _ = classifier.score_line(body_line, line_idx=5, total_lines_on_page=10, median_font_size=12.0)
    assert is_body_heading is False
    assert conf_body.score < 0.65


def test_text_representations_and_typing_modes():
    source = "The 'Habit Loop' (123)."
    norm = "The 'Habit Loop' (123)."

    # Standard mode
    rep_std = TextRepresentationBuilder.build(source, norm, mode=TypingMode.STANDARD)
    assert rep_std.typing_text == "The 'Habit Loop' (123)."
    assert len(rep_std.offset_map.typing_to_display_indices) == len(rep_std.typing_text)

    # Lowercase mode
    rep_lower = TextRepresentationBuilder.build(source, norm, mode=TypingMode.LOWERCASE)
    assert rep_lower.typing_text == "the 'habit loop' (123)."
    assert len(rep_lower.offset_map.typing_to_display_indices) == len(rep_lower.typing_text)

    # No punctuation mode
    rep_nopunct = TextRepresentationBuilder.build(source, norm, mode=TypingMode.NO_PUNCTUATION)
    assert rep_nopunct.typing_text == "The Habit Loop 123"
    assert len(rep_nopunct.offset_map.typing_to_display_indices) == len(rep_nopunct.typing_text)

    # Letters only mode
    rep_letters = TextRepresentationBuilder.build(source, norm, mode=TypingMode.LETTERS_ONLY)
    assert rep_letters.typing_text == "The Habit Loop "
    assert len(rep_letters.offset_map.typing_to_display_indices) == len(rep_letters.typing_text)


def test_ingestion_pipeline_end_to_end():
    content = """# Chapter 1: Foundations
The first principle of behavior change is to make cues obvious.
Environment design is an essential tool.

## Section 1.1: Small Cues
Even tiny adjustments in your environment create measurable compound differences.
"""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(content)
        path = f.name

    pipeline = IngestionPipeline()
    preview, doc, chapters, sections, paragraphs = pipeline.process(path, user_id="user_123")

    assert preview.detected_title != ""
    assert preview.statistics.total_words > 0
    assert len(chapters) >= 1
    assert len(sections) >= 1
    assert len(paragraphs) >= 1
    assert doc.status.value == "preview_ready"
