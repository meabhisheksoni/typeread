"""
TypeRead Document Ingestion Pipeline Coordinator
Executes the end-to-end ingestion pipeline:
Validation -> Extraction -> Normalization -> Cleaning -> Structure Detection -> IngestionPreview
"""

from __future__ import annotations
import hashlib
import time
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional

from src.contracts.types import (
    DocumentId,
    ChapterId,
    SectionId,
    ParagraphId,
    UserId,
    DocumentFormat,
    IngestionStatus,
    StructuralLevel,
    ProcessingProfile,
    ProcessingStatistics,
    BeforeAfterSample,
    ChapterPreviewNode,
    SectionPreviewNode,
    IngestionPreview,
    DocumentEntity,
    ChapterEntity,
    SectionEntity,
    ParagraphEntity,
    StructuralNodeConfidence,
    StructuralNodeSignals,
    TypingMode,
)
from src.core.document.parsers import DocumentParserRegistry, RawDocumentContent, RawPage, RawLine
from src.core.document.normalizer import TextNormalizer
from src.core.document.heuristics import HeadingClassifier
from src.core.document.representations import TextRepresentationBuilder


class IngestionPipeline:
    def __init__(self, profile: Optional[ProcessingProfile] = None):
        self.profile = profile or ProcessingProfile()

    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def process(
        self,
        file_path: str,
        user_id: str = "default_user",
        profile_override: Optional[ProcessingProfile] = None,
    ) -> Tuple[IngestionPreview, DocumentEntity, List[ChapterEntity], List[SectionEntity], List[ParagraphEntity]]:
        start_time = time.time()
        active_profile = profile_override or self.profile

        # 1. Validation & Extraction
        raw_doc = DocumentParserRegistry.parse(file_path)
        file_hash = self.calculate_file_hash(file_path)

        # 2. Normalization & Cleaning
        normalizer = TextNormalizer(profile=active_profile)
        cleaned_pages, stats, samples = normalizer.process(raw_doc)

        # 3. Structure Heuristics & Heading Classification
        classifier = HeadingClassifier(min_confidence=active_profile.min_heading_confidence)
        median_font_size = classifier.calculate_median_font_size(cleaned_pages)

        doc_id = DocumentId(str(uuid.uuid4()))
        now_iso = datetime.now(timezone.utc).isoformat()

        chapters: List[ChapterEntity] = []
        sections: List[SectionEntity] = []
        paragraphs: List[ParagraphEntity] = []

        # Build preview tree nodes
        chapter_preview_nodes: List[ChapterPreviewNode] = []

        current_chapter: Optional[ChapterEntity] = None
        current_section: Optional[SectionEntity] = None
        current_chapter_preview: Optional[ChapterPreviewNode] = None
        current_section_preview: Optional[SectionPreviewNode] = None

        chapter_idx = 0
        section_idx = 0
        paragraph_idx = 0

        char_counter = 0

        # Helper to ensure at least one chapter and section exists
        def ensure_active_chapter_and_section(page_num: int):
            nonlocal current_chapter, current_section, current_chapter_preview, current_section_preview
            nonlocal chapter_idx, section_idx

            if current_chapter is None:
                chap_id = ChapterId(str(uuid.uuid4()))
                conf = StructuralNodeConfidence(
                    score=1.0,
                    signals=StructuralNodeSignals(
                        font_size_score=1.0,
                        bold_weight_score=1.0,
                        numbering_score=1.0,
                        position_score=1.0,
                        whitespace_score=1.0,
                        short_line_score=1.0,
                        paragraph_length_penalty=0.0,
                    ),
                )
                current_chapter = ChapterEntity(
                    id=chap_id,
                    document_id=doc_id,
                    parent_id=None,
                    title="Chapter 1",
                    level=StructuralLevel.CHAPTER,
                    order_index=chapter_idx,
                    page_start=page_num,
                    page_end=page_num,
                    text_start_char=char_counter,
                    text_end_char=char_counter,
                    confidence=conf,
                    included_in_practice=True,
                    created_at=now_iso,
                )
                chapters.append(current_chapter)
                chapter_idx += 1

                current_chapter_preview = ChapterPreviewNode(
                    id=str(chap_id),
                    title=current_chapter.title,
                    level=current_chapter.level,
                    page_number=page_num,
                    confidence_score=1.0,
                    included=True,
                    sub_sections=[],
                )
                chapter_preview_nodes.append(current_chapter_preview)

            if current_section is None:
                sec_id = SectionId(str(uuid.uuid4()))
                current_section = SectionEntity(
                    id=sec_id,
                    document_id=doc_id,
                    chapter_id=current_chapter.id,
                    title="Section 1",
                    order_index=section_idx,
                    page_start=page_num,
                    page_end=page_num,
                    text_start_char=char_counter,
                    text_end_char=char_counter,
                    word_count=0,
                    character_count=0,
                    included_in_practice=True,
                    created_at=now_iso,
                )
                sections.append(current_section)
                section_idx += 1

                current_section_preview = SectionPreviewNode(
                    id=str(sec_id),
                    title=current_section.title,
                    word_count=0,
                    included=True,
                )
                if current_chapter_preview:
                    current_chapter_preview.sub_sections.append(current_section_preview)

        # Iterate over pages and lines
        for page in cleaned_pages:
            total_lines_on_page = len(page.lines)
            accumulated_para_lines: List[str] = []
            para_source_lines: List[str] = []
            para_pos_y = 0.0

            def flush_paragraph():
                nonlocal accumulated_para_lines, para_source_lines, para_pos_y
                nonlocal paragraph_idx, char_counter
                if not accumulated_para_lines:
                    return

                display_str = " ".join(accumulated_para_lines).strip()
                source_str = "\n".join(para_source_lines).strip()

                if not display_str:
                    accumulated_para_lines = []
                    para_source_lines = []
                    return

                ensure_active_chapter_and_section(page.page_number)

                reps = TextRepresentationBuilder.build(
                    raw_source=source_str,
                    normalized_str=display_str,
                    mode=TypingMode.STANDARD,
                )

                p_id = ParagraphId(str(uuid.uuid4()))
                p_entity = ParagraphEntity(
                    id=p_id,
                    document_id=doc_id,
                    chapter_id=current_chapter.id,
                    section_id=current_section.id,
                    order_index=paragraph_idx,
                    representations=reps,
                    source_page=page.page_number,
                    source_position_y=para_pos_y,
                    created_at=now_iso,
                )
                paragraphs.append(p_entity)
                paragraph_idx += 1

                p_words = len(display_str.split())
                p_chars = len(display_str)
                char_counter += p_chars

                # Update section stats
                if current_section:
                    sec_idx = sections.index(current_section)
                    updated_sec = SectionEntity(
                        id=current_section.id,
                        document_id=current_section.document_id,
                        chapter_id=current_section.chapter_id,
                        title=current_section.title,
                        order_index=current_section.order_index,
                        page_start=current_section.page_start,
                        page_end=page.page_number,
                        text_start_char=current_section.text_start_char,
                        text_end_char=char_counter,
                        word_count=current_section.word_count + p_words,
                        character_count=current_section.character_count + p_chars,
                        included_in_practice=current_section.included_in_practice,
                        created_at=current_section.created_at,
                    )
                    sections[sec_idx] = updated_sec

                    # Update preview node
                    if current_section_preview:
                        idx_prev = current_chapter_preview.sub_sections.index(current_section_preview)
                        current_chapter_preview.sub_sections[idx_prev] = SectionPreviewNode(
                            id=current_section_preview.id,
                            title=current_section_preview.title,
                            word_count=updated_sec.word_count,
                            included=current_section_preview.included,
                        )

                accumulated_para_lines = []
                para_source_lines = []

            for line_idx, line in enumerate(page.lines):
                conf, is_heading, level = classifier.score_line(
                    line=line,
                    line_idx=line_idx,
                    total_lines_on_page=total_lines_on_page,
                    median_font_size=median_font_size,
                )

                if is_heading:
                    flush_paragraph()

                    if level == StructuralLevel.CHAPTER:
                        chap_id = ChapterId(str(uuid.uuid4()))
                        current_chapter = ChapterEntity(
                            id=chap_id,
                            document_id=doc_id,
                            parent_id=None,
                            title=line.text.strip(),
                            level=StructuralLevel.CHAPTER,
                            order_index=chapter_idx,
                            page_start=page.page_number,
                            page_end=page.page_number,
                            text_start_char=char_counter,
                            text_end_char=char_counter,
                            confidence=conf,
                            included_in_practice=True,
                            created_at=now_iso,
                        )
                        chapters.append(current_chapter)
                        chapter_idx += 1

                        current_chapter_preview = ChapterPreviewNode(
                            id=str(chap_id),
                            title=current_chapter.title,
                            level=current_chapter.level,
                            page_number=page.page_number,
                            confidence_score=conf.score,
                            included=True,
                            sub_sections=[],
                        )
                        chapter_preview_nodes.append(current_chapter_preview)

                        # New default section for this chapter
                        sec_id = SectionId(str(uuid.uuid4()))
                        current_section = SectionEntity(
                            id=sec_id,
                            document_id=doc_id,
                            chapter_id=current_chapter.id,
                            title="Introduction",
                            order_index=0,
                            page_start=page.page_number,
                            page_end=page.page_number,
                            text_start_char=char_counter,
                            text_end_char=char_counter,
                            word_count=0,
                            character_count=0,
                            included_in_practice=True,
                            created_at=now_iso,
                        )
                        sections.append(current_section)
                        section_idx = 1

                        current_section_preview = SectionPreviewNode(
                            id=str(sec_id),
                            title=current_section.title,
                            word_count=0,
                            included=True,
                        )
                        current_chapter_preview.sub_sections.append(current_section_preview)

                    else:
                        # Subsection
                        ensure_active_chapter_and_section(page.page_number)
                        sec_id = SectionId(str(uuid.uuid4()))
                        current_section = SectionEntity(
                            id=sec_id,
                            document_id=doc_id,
                            chapter_id=current_chapter.id,
                            title=line.text.strip(),
                            order_index=section_idx,
                            page_start=page.page_number,
                            page_end=page.page_number,
                            text_start_char=char_counter,
                            text_end_char=char_counter,
                            word_count=0,
                            character_count=0,
                            included_in_practice=True,
                            created_at=now_iso,
                        )
                        sections.append(current_section)
                        section_idx += 1

                        current_section_preview = SectionPreviewNode(
                            id=str(sec_id),
                            title=current_section.title,
                            word_count=0,
                            included=True,
                        )
                        if current_chapter_preview:
                            current_chapter_preview.sub_sections.append(current_section_preview)

                else:
                    # Regular body text
                    if not accumulated_para_lines:
                        para_pos_y = line.position_y
                    accumulated_para_lines.append(line.text)
                    para_source_lines.append(line.text)

            flush_paragraph()

        # Update end char pointers on chapters
        for idx, chap in enumerate(chapters):
            chap_secs = [s for s in sections if s.chapter_id == chap.id]
            if chap_secs:
                max_page = max(s.page_end for s in chap_secs)
                max_char = max(s.text_end_char for s in chap_secs)
                chapters[idx] = ChapterEntity(
                    id=chap.id,
                    document_id=chap.document_id,
                    parent_id=chap.parent_id,
                    title=chap.title,
                    level=chap.level,
                    order_index=chap.order_index,
                    page_start=chap.page_start,
                    page_end=max_page,
                    text_start_char=chap.text_start_char,
                    text_end_char=max_char,
                    confidence=chap.confidence,
                    included_in_practice=chap.included_in_practice,
                    created_at=chap.created_at,
                )

        duration_ms = int((time.time() - start_time) * 1000)

        total_words = sum(s.word_count for s in sections)
        total_chars = sum(s.character_count for s in sections)

        final_stats = ProcessingStatistics(
            total_pages=stats.total_pages,
            total_words=total_words,
            total_characters=total_chars,
            detected_chapters_count=len(chapters),
            detected_sections_count=len(sections),
            removed_headers_count=stats.removed_headers_count,
            removed_footers_count=stats.removed_footers_count,
            removed_page_numbers_count=stats.removed_page_numbers_count,
            repaired_hyphenations_count=stats.repaired_hyphenations_count,
            ocr_applied_pages_count=0,
            processing_duration_ms=duration_ms,
        )

        doc_entity = DocumentEntity(
            id=doc_id,
            user_id=UserId(user_id),
            title=raw_doc.title,
            author=raw_doc.author,
            file_name=file_path.split("/")[-1],
            file_path=file_path,
            file_hash=file_hash,
            source_format=raw_doc.format,
            word_count=total_words,
            character_count=total_chars,
            status=IngestionStatus.PREVIEW_READY,
            processing_profile=active_profile,
            created_at=now_iso,
            updated_at=now_iso,
            error_message=None,
        )

        preview = IngestionPreview(
            document_id=doc_id,
            detected_title=raw_doc.title,
            detected_author=raw_doc.author,
            format=raw_doc.format,
            statistics=final_stats,
            structure_tree=chapter_preview_nodes,
            sample_cleanups=samples,
        )

        return preview, doc_entity, chapters, sections, paragraphs
