"""
TypeRead Text Representations & Bi-Directional Character Offset Mapping
Generates source_text, normalized_text, display_text, typing_text,
and computes exact character offset maps.
"""

from __future__ import annotations
import re
import string
from typing import Tuple, Optional

from src.contracts.types import (
    TypingMode,
    CharacterOffsetMap,
    TextRepresentations,
    CustomTypingFilter,
)


class TextRepresentationBuilder:
    @classmethod
    def build(
        cls,
        raw_source: str,
        normalized_str: str,
        mode: TypingMode = TypingMode.STANDARD,
        custom_filter: Optional[CustomTypingFilter] = None,
    ) -> TextRepresentations:
        source_text = raw_source
        display_text = normalized_str

        # Build display_to_source_indices mapping
        # In normalized vs source, if length differs due to simple whitespace/ftfy,
        # we compute monotonic alignment
        display_to_source_indices = cls._align_display_to_source(display_text, source_text)

        # Build typing_text and typing_to_display_indices
        typing_chars = []
        typing_to_display = []

        for idx, char in enumerate(display_text):
            should_include, transformed_char = cls._transform_character(char, mode, custom_filter)
            if should_include:
                typing_chars.append(transformed_char)
                typing_to_display.append(idx)

        typing_text = "".join(typing_chars)

        offset_map = CharacterOffsetMap(
            typing_to_display_indices=tuple(typing_to_display),
            display_to_source_indices=tuple(display_to_source_indices),
        )

        return TextRepresentations(
            source_text=source_text,
            normalized_text=normalized_str,
            display_text=display_text,
            typing_text=typing_text,
            offset_map=offset_map,
        )

    @classmethod
    def _transform_character(
        cls,
        char: str,
        mode: TypingMode,
        custom_filter: Optional[CustomTypingFilter] = None,
    ) -> Tuple[bool, str]:
        """
        Determines if a character from display_text should be included in typing_text,
        and its transformed form.
        """
        if mode == TypingMode.STANDARD:
            return True, char

        elif mode == TypingMode.LOWERCASE:
            return True, char.lower()

        elif mode == TypingMode.NO_PUNCTUATION:
            # Preserve letters, numbers, spaces, newlines; strip punctuation
            if char in string.punctuation or char in "“”‘’—–…«»":
                return False, ""
            return True, char

        elif mode == TypingMode.LETTERS_ONLY:
            if char.isalpha() or char.isspace():
                return True, char
            return False, ""

        elif mode == TypingMode.NUMBERS:
            if char.isdigit() or char.isspace() or char in ".,+-/*=%":
                return True, char
            return False, ""

        elif mode == TypingMode.PUNCTUATION:
            return True, char

        elif mode == TypingMode.QUOTES:
            return True, char

        elif mode == TypingMode.CUSTOM and custom_filter:
            if not custom_filter.preserve_case and char.isalpha():
                char = char.lower()
            if not custom_filter.preserve_punctuation and (char in string.punctuation or char in "“”‘’—–…"):
                return False, ""
            if not custom_filter.preserve_numbers and char.isdigit():
                return False, ""
            if custom_filter.custom_allowed_characters is not None:
                if char not in custom_filter.custom_allowed_characters and not char.isspace():
                    return False, ""
            return True, char

        return True, char

    @classmethod
    def _align_display_to_source(cls, display_text: str, source_text: str) -> Tuple[int, ...]:
        """
        Monotonic character alignment mapping display index -> source index.
        """
        disp_len = len(display_text)
        src_len = len(source_text)

        if disp_len == 0:
            return ()

        if disp_len == src_len:
            return tuple(range(disp_len))

        # Two-pointer sub-string alignment
        mapping = []
        src_idx = 0

        for d_char in display_text:
            matched = False
            # Lookahead up to 20 chars in source
            search_limit = min(src_len, src_idx + 25)
            for s_i in range(src_idx, search_limit):
                if source_text[s_i] == d_char:
                    src_idx = s_i
                    mapping.append(src_idx)
                    src_idx += 1
                    matched = True
                    break

            if not matched:
                # Clamp to nearest valid source index
                mapping.append(min(src_len - 1, max(0, src_idx)))

        return tuple(mapping)
