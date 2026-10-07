"""
TypeRead Text Cleaning & Normalization Pipeline
Deterministic Unicode normalization, header/footer stripping, page number removal,
hyphenation repair, and paragraph reconstruction.
"""

from __future__ import annotations
import re
import unicodedata
from collections import Counter
from typing import List, Tuple, Dict, Optional

import ftfy

from src.contracts.types import ProcessingProfile, ProcessingStatistics, BeforeAfterSample
from src.core.document.parsers import RawDocumentContent, RawPage, RawLine


class TextNormalizer:
    def __init__(self, profile: Optional[ProcessingProfile] = None):
        self.profile = profile or ProcessingProfile()

    def process(self, raw_doc: RawDocumentContent) -> Tuple[List[RawPage], ProcessingStatistics, List[BeforeAfterSample]]:
        samples: List[BeforeAfterSample] = []
        removed_headers_count = 0
        removed_footers_count = 0
        removed_page_numbers_count = 0
        repaired_hyphenations_count = 0

        # Step 1: Detect candidate headers and footers across multiple pages
        header_candidates: Counter[str] = Counter()
        footer_candidates: Counter[str] = Counter()
        total_pages = max(1, len(raw_doc.pages))

        if total_pages > 1 and (self.profile.remove_headers or self.profile.remove_footers):
            for page in raw_doc.pages:
                if not page.lines:
                    continue
                # Top 2 lines are header candidates
                for line in page.lines[:2]:
                    t = line.text.strip()
                    if t and len(t) < 80:
                        header_candidates[t] += 1
                # Bottom 2 lines are footer candidates
                for line in page.lines[-2:]:
                    t = line.text.strip()
                    if t and len(t) < 80:
                        footer_candidates[t] += 1

        # Keep candidates that appear on at least 2 pages (or >= 30% of pages if many pages)
        min_occurrences = 2 if total_pages >= 3 else 2
        detected_headers = {
            txt for txt, count in header_candidates.items()
            if count >= min_occurrences and not self._is_page_number(txt)
        }
        detected_footers = {
            txt for txt, count in footer_candidates.items()
            if count >= min_occurrences and not self._is_page_number(txt)
        }

        cleaned_pages: List[RawPage] = []
        page_num_regex = re.compile(r"^(?:page\s+)?(?:[-–—]\s*)?\d+(?:\s*[-–—])?$", re.IGNORECASE)

        for page in raw_doc.pages:
            cleaned_page = RawPage(page_number=page.page_number)
            lines_count = len(page.lines)

            for idx, line in enumerate(page.lines):
                orig_text = line.text
                text = orig_text.strip()

                # Check Header removal
                if self.profile.remove_headers and idx < 2 and text in detected_headers:
                    removed_headers_count += 1
                    if len(samples) < 5:
                        samples.append(
                            BeforeAfterSample(
                                title=f"Header Removed (Page {page.page_number})",
                                before_text=orig_text,
                                after_text="",
                                cleanup_category="header_footer",
                            )
                        )
                    continue

                # Check Footer removal
                if self.profile.remove_footers and idx >= max(0, lines_count - 2) and text in detected_footers:
                    removed_footers_count += 1
                    if len(samples) < 5:
                        samples.append(
                            BeforeAfterSample(
                                title=f"Footer Removed (Page {page.page_number})",
                                before_text=orig_text,
                                after_text="",
                                cleanup_category="header_footer",
                            )
                        )
                    continue

                # Check Page Number removal
                if self.profile.remove_page_numbers and (idx < 2 or idx >= max(0, lines_count - 2)):
                    if page_num_regex.match(text):
                        removed_page_numbers_count += 1
                        if len(samples) < 5:
                            samples.append(
                                BeforeAfterSample(
                                    title=f"Page Number Removed (Page {page.page_number})",
                                    before_text=orig_text,
                                    after_text="",
                                    cleanup_category="page_number",
                                )
                            )
                        continue

                # Unicode & Whitespace Normalization
                cleaned_text = orig_text
                if self.profile.normalize_unicode:
                    cleaned_text = ftfy.fix_text(cleaned_text)
                    cleaned_text = unicodedata.normalize("NFC", cleaned_text)

                if self.profile.normalize_whitespace:
                    cleaned_text = re.sub(r"[\t\r\f\v]", " ", cleaned_text)
                    cleaned_text = re.sub(r" {2,}", " ", cleaned_text)

                cleaned_page.lines.append(
                    RawLine(
                        text=cleaned_text.strip(),
                        page_number=line.page_number,
                        font_size=line.font_size,
                        is_bold=line.is_bold,
                        position_y=line.position_y,
                        position_x=line.position_x,
                        line_width=line.line_width,
                        is_heading_hint=line.is_heading_hint,
                        heading_level_hint=line.heading_level_hint,
                    )
                )

            cleaned_pages.append(cleaned_page)

        # Step 2: Hyphenation Repair across consecutive lines
        if self.profile.repair_hyphenation:
            for page in cleaned_pages:
                new_lines: List[RawLine] = []
                i = 0
                while i < len(page.lines):
                    current_line = page.lines[i]
                    if i + 1 < len(page.lines):
                        next_line = page.lines[i + 1]
                        # Look for trailing hyphen on a word
                        hyphen_match = re.search(r"(\b[a-zA-Z]{2,})[-–]\s*$", current_line.text)
                        next_word_match = re.match(r"^\s*([a-zA-Z]{2,}\b)", next_line.text)
                        if hyphen_match and next_word_match:
                            prefix = current_line.text[:hyphen_match.start(0)]
                            word_part1 = hyphen_match.group(1)
                            word_part2 = next_word_match.group(1)
                            combined_word = word_part1 + word_part2
                            next_suffix = next_line.text[next_word_match.end(0):]

                            merged_current = f"{prefix}{combined_word}".strip()
                            if len(samples) < 5:
                                samples.append(
                                    BeforeAfterSample(
                                        title="Hyphenation Repaired",
                                        before_text=f"{current_line.text}\n{next_line.text}",
                                        after_text=f"{merged_current}\n{next_suffix.strip()}",
                                        cleanup_category="hyphenation",
                                    )
                                )
                            repaired_hyphenations_count += 1
                            current_line = RawLine(
                                text=merged_current,
                                page_number=current_line.page_number,
                                font_size=current_line.font_size,
                                is_bold=current_line.is_bold,
                                position_y=current_line.position_y,
                                position_x=current_line.position_x,
                                line_width=current_line.line_width,
                                is_heading_hint=current_line.is_heading_hint,
                                heading_level_hint=current_line.heading_level_hint,
                            )
                            new_lines.append(current_line)
                            if next_suffix.strip():
                                page.lines[i + 1] = RawLine(
                                    text=next_suffix.strip(),
                                    page_number=next_line.page_number,
                                    font_size=next_line.font_size,
                                    is_bold=next_line.is_bold,
                                    position_y=next_line.position_y,
                                    position_x=next_line.position_x,
                                    line_width=next_line.line_width,
                                    is_heading_hint=next_line.is_heading_hint,
                                    heading_level_hint=next_line.heading_level_hint,
                                )
                                i += 1
                            else:
                                i += 2
                            continue

                    new_lines.append(current_line)
                    i += 1
                page.lines = new_lines

        # Calculate statistics
        total_words = 0
        total_chars = 0
        for p in cleaned_pages:
            for l in p.lines:
                total_chars += len(l.text)
                total_words += len(l.text.split())

        stats = ProcessingStatistics(
            total_pages=total_pages,
            total_words=total_words,
            total_characters=total_chars,
            detected_chapters_count=0,
            detected_sections_count=0,
            removed_headers_count=removed_headers_count,
            removed_footers_count=removed_footers_count,
            removed_page_numbers_count=removed_page_numbers_count,
            repaired_hyphenations_count=repaired_hyphenations_count,
            ocr_applied_pages_count=0,
            processing_duration_ms=0,
        )

        return cleaned_pages, stats, samples

    @staticmethod
    def _is_page_number(text: str) -> bool:
        t = text.strip()
        return bool(re.match(r"^(?:page\s+)?(?:[-–—]\s*)?\d+(?:\s*[-–—])?$", t, re.IGNORECASE))
