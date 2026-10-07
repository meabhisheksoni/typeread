"""
TypeRead Deterministic Heading Detection Heuristics
Pure mathematical scoring algorithm without external AI / cloud dependencies.
Calculates StructuralNodeConfidence based on font size, bold weight, numbering,
positioning, whitespace, and length penalties.
"""

from __future__ import annotations
import re
import statistics
from typing import List, Tuple, Optional

from src.contracts.types import (
    StructuralLevel,
    HeadingTag,
    StructuralNodeConfidence,
    StructuralNodeSignals,
)
from src.core.document.parsers import RawLine, RawPage


class HeadingClassifier:
    CHAPTER_REGEX = re.compile(
        r"^(?:chapter\s+\d+|chapter\s+[ivxlcdm]+|part\s+[ivxlcdm]+|part\s+\d+|book\s+\d+|\d+\.\s+[a-z]|[ivxlcdm]+\.\s+[a-z])",
        re.IGNORECASE,
    )
    SECTION_REGEX = re.compile(
        r"^(?:\d+\.\d+|\d+\.\d+\.\d+|section\s+\d+)",
        re.IGNORECASE,
    )
    NUMBERING_REGEX = re.compile(
        r"^(?:chapter\b|part\b|section\b|book\b|\d+\.|\d+\.\d+|[ivxlcdm]+\.)",
        re.IGNORECASE,
    )

    def __init__(self, min_confidence: float = 0.65):
        self.min_confidence = min_confidence

    def score_line(
        self,
        line: RawLine,
        line_idx: int,
        total_lines_on_page: int,
        median_font_size: float = 12.0,
    ) -> Tuple[StructuralNodeConfidence, bool, StructuralLevel]:
        """
        Calculates heading confidence score in range [0.0, 1.0].
        Returns (confidence, is_heading, level).
        """
        text = line.text.strip()
        length = len(text)

        # Signal 1: Font Size Score
        if line.font_size > median_font_size:
            ratio = (line.font_size - median_font_size) / max(1.0, median_font_size)
            font_size_score = min(1.0, max(0.0, ratio * 2.0))
        else:
            font_size_score = 0.0

        # Signal 2: Bold Weight Score
        bold_weight_score = 1.0 if line.is_bold else 0.0

        # Signal 3: Numbering Score
        is_chapter_match = bool(self.CHAPTER_REGEX.search(text))
        is_section_match = bool(self.SECTION_REGEX.search(text))
        is_num_match = bool(self.NUMBERING_REGEX.search(text))
        if is_chapter_match:
            numbering_score = 1.0
        elif is_section_match or is_num_match:
            numbering_score = 0.8
        else:
            numbering_score = 0.0

        # Signal 4: Position Score (near top of page or first line)
        if line_idx == 0:
            position_score = 1.0
        elif line_idx <= 2:
            position_score = 0.7
        else:
            position_score = 0.2

        # Signal 5: Whitespace / Isolation Score
        whitespace_score = 0.8 if line_idx == 0 or line_idx == total_lines_on_page - 1 else 0.3

        # Signal 6: Short Line Score
        if length <= 45:
            short_line_score = 1.0
        elif length <= 80:
            short_line_score = 0.6
        else:
            short_line_score = 0.0

        # Penalty: Length and multiple sentence endings
        has_multiple_periods = text.count(".") >= 2 and not is_num_match
        if length > 120 or has_multiple_periods:
            length_penalty = 1.0
        elif length > 90:
            length_penalty = 0.5
        else:
            length_penalty = 0.0

        # If parser provided explicit hint (e.g. Markdown '#' or HTML '<hX>')
        if line.is_heading_hint:
            font_size_score = max(font_size_score, 0.9)
            bold_weight_score = 1.0
            short_line_score = max(short_line_score, 0.8)
            length_penalty = 0.0

        # Weighted calculation
        # Formula: w1*font + w2*bold + w3*numbering + w4*pos + w5*ws + w6*short - w7*penalty
        w1, w2, w3, w4, w5, w6, w7 = 0.25, 0.20, 0.25, 0.10, 0.10, 0.10, 0.30
        raw_score = (
            w1 * font_size_score
            + w2 * bold_weight_score
            + w3 * numbering_score
            + w4 * position_score
            + w5 * whitespace_score
            + w6 * short_line_score
            - w7 * length_penalty
        )

        final_score = round(max(0.0, min(1.0, raw_score)), 4)

        signals = StructuralNodeSignals(
            font_size_score=round(font_size_score, 2),
            bold_weight_score=round(bold_weight_score, 2),
            numbering_score=round(numbering_score, 2),
            position_score=round(position_score, 2),
            whitespace_score=round(whitespace_score, 2),
            short_line_score=round(short_line_score, 2),
            paragraph_length_penalty=round(length_penalty, 2),
        )

        confidence = StructuralNodeConfidence(score=final_score, signals=signals)
        is_heading = final_score >= self.min_confidence

        # Determine level
        if is_chapter_match or (line.heading_level_hint and line.heading_level_hint <= 1) or final_score >= 0.80:
            level = StructuralLevel.CHAPTER
        elif is_section_match or (line.heading_level_hint and line.heading_level_hint == 2):
            level = StructuralLevel.SECTION
        else:
            level = StructuralLevel.SECTION

        return confidence, is_heading, level

    @staticmethod
    def calculate_median_font_size(pages: List[RawPage]) -> float:
        sizes: List[float] = []
        for p in pages:
            for l in p.lines:
                if l.font_size > 0:
                    sizes.append(l.font_size)
        if not sizes:
            return 12.0
        return float(statistics.median(sizes))
