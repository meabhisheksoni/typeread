"""
Unit tests for domain types, validation invariants, and error contracts.
"""

import pytest
from datetime import datetime

from src.contracts.types import (
    ProcessingProfile,
    StructuralNodeConfidence,
    StructuralNodeSignals,
    CharacterOffsetMap,
    TextRepresentations,
    ErrorCode,
    ErrorDetail,
    AppError,
)
from src.core.errors import AppErrorException


def test_processing_profile_confidence_bounds():
    # Valid bounds
    prof = ProcessingProfile(min_heading_confidence=0.7)
    assert prof.min_heading_confidence == 0.7

    # Invalid bounds must raise ValueError
    with pytest.raises(ValueError):
        ProcessingProfile(min_heading_confidence=1.5)

    with pytest.raises(ValueError):
        ProcessingProfile(min_heading_confidence=-0.1)


def test_structural_node_confidence_bounds():
    signals = StructuralNodeSignals(
        font_size_score=0.5,
        bold_weight_score=1.0,
        numbering_score=0.8,
        position_score=0.7,
        whitespace_score=0.5,
        short_line_score=1.0,
        paragraph_length_penalty=0.0,
    )
    conf = StructuralNodeConfidence(score=0.85, signals=signals)
    assert conf.score == 0.85

    with pytest.raises(ValueError):
        StructuralNodeConfidence(score=1.2, signals=signals)


def test_text_representations_offset_map_invariant():
    # Valid invariant: len(typing_to_display_indices) == len(typing_text)
    typing_text = "Hello"
    display_text = "Hello World"
    offset_map = CharacterOffsetMap(
        typing_to_display_indices=(0, 1, 2, 3, 4),
        display_to_source_indices=tuple(range(len(display_text))),
    )
    reps = TextRepresentations(
        source_text="Hello World",
        normalized_text="Hello World",
        display_text=display_text,
        typing_text=typing_text,
        offset_map=offset_map,
    )
    assert reps.typing_text == "Hello"

    # Mismatch must raise ValueError
    mismatched_map = CharacterOffsetMap(
        typing_to_display_indices=(0, 1),
        display_to_source_indices=tuple(range(len(display_text))),
    )
    with pytest.raises(ValueError):
        TextRepresentations(
            source_text="Hello World",
            normalized_text="Hello World",
            display_text=display_text,
            typing_text=typing_text,
            offset_map=mismatched_map,
        )


def test_app_error_exception_status_mapping():
    err_404 = AppErrorException.not_found(
        code=ErrorCode.DOCUMENT_NOT_FOUND,
        message="Document not found",
        field="documentId",
    )
    assert err_404.status_code == 404
    assert err_404.code == ErrorCode.DOCUMENT_NOT_FOUND
    data_404 = err_404.to_dict()
    assert data_404["code"] == "DOCUMENT_NOT_FOUND"
    assert data_404["details"][0]["field"] == "documentId"

    err_409 = AppErrorException.conflict(
        code=ErrorCode.DOCUMENT_ALREADY_EXISTS,
        message="Duplicate document",
    )
    assert err_409.status_code == 409

    err_400 = AppErrorException.bad_request(
        code=ErrorCode.INVALID_KEYSTROKE,
        message="Invalid stroke",
    )
    assert err_400.status_code == 400

    err_422 = AppErrorException.unprocessable(
        code=ErrorCode.OCR_REQUIRED,
        message="Scanned PDF",
    )
    assert err_422.status_code == 422
