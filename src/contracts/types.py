"""
TypeRead Core Domain Types & Data Models (Python 3.11+)
Specification Version: 1.0.0
Architecture Gate: GATE_1_ARCHITECT

Invariants & Strict Design:
- Zero 'Any' types: everything is typed with strict primitives, Enums, or Dataclasses.
- Frozen dataclasses for domain entities and value objects to enforce immutability.
- Invariants checked upon initialization where appropriate.
- Matches `types.ts` 1:1 for cross-stack compatibility.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import NewType, Optional, List, Dict, Tuple, Literal
from datetime import datetime

# ============================================================================
# BRANDED IDENTIFIERS
# ============================================================================

UserId = NewType("UserId", str)
DocumentId = NewType("DocumentId", str)
ChapterId = NewType("ChapterId", str)
SectionId = NewType("SectionId", str)
ParagraphId = NewType("ParagraphId", str)
SessionId = NewType("SessionId", str)
BookmarkId = NewType("BookmarkId", str)
NoteId = NewType("NoteId", str)
VersionId = NewType("VersionId", str)


# ============================================================================
# ENUMS & DOMAIN CONSTANTS
# ============================================================================

class DocumentFormat(str, Enum):
    PDF = "pdf"
    EPUB = "epub"
    DOCX = "docx"
    TXT = "txt"
    MARKDOWN = "markdown"
    HTML = "html"


class IngestionStatus(str, Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    EXTRACTING = "extracting"
    NORMALIZING = "normalizing"
    CLEANING = "cleaning"
    DETECTING_STRUCTURE = "detecting_structure"
    PREVIEW_READY = "preview_ready"
    COMMITTED = "committed"
    FAILED = "failed"


class StructuralLevel(str, Enum):
    PART = "part"
    CHAPTER = "chapter"
    SECTION = "section"
    SUBSECTION = "subsection"


class HeadingTag(str, Enum):
    H1 = "H1"
    H2 = "H2"
    H3 = "H3"
    H4 = "H4"
    H5 = "H5"
    H6 = "H6"
    PARAGRAPH = "PARAGRAPH"


class TypingMode(str, Enum):
    STANDARD = "standard"
    LOWERCASE = "lowercase"
    NO_PUNCTUATION = "no_punctuation"
    LETTERS_ONLY = "letters_only"
    NUMBERS = "numbers"
    PUNCTUATION = "punctuation"
    QUOTES = "quotes"
    CUSTOM = "custom"


class ErrorHandlingMode(str, Enum):
    ALLOW_WITH_BACKSPACE = "allow_with_backspace"
    STOP_ON_ERROR = "stop_on_error"
    IMMEDIATE_BACKSPACE = "immediate_backspace"


class CaretStyle(str, Enum):
    LINE = "line"
    BLOCK = "block"
    UNDERLINE = "underline"
    BAR_BLINKING = "bar_blinking"


class ThemeId(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    SEPIA = "sepia"
    PAPER = "paper"
    HIGH_CONTRAST = "high_contrast"
    MIDNIGHT = "midnight"


class TypingSessionState(str, Enum):
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABORTED = "aborted"


class ErrorCode(str, Enum):
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_UNREADABLE = "FILE_UNREADABLE"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    CORRUPTED_DOCUMENT = "CORRUPTED_DOCUMENT"
    EMPTY_DOCUMENT = "EMPTY_DOCUMENT"
    OCR_REQUIRED = "OCR_REQUIRED"
    OCR_FAILED = "OCR_FAILED"
    PARSING_FAILED = "PARSING_FAILED"
    DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
    DOCUMENT_ALREADY_EXISTS = "DOCUMENT_ALREADY_EXISTS"
    CHAPTER_NOT_FOUND = "CHAPTER_NOT_FOUND"
    SECTION_NOT_FOUND = "SECTION_NOT_FOUND"
    PARAGRAPH_NOT_FOUND = "PARAGRAPH_NOT_FOUND"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_ALREADY_FINISHED = "SESSION_ALREADY_FINISHED"
    INVALID_KEYSTROKE = "INVALID_KEYSTROKE"
    POSITION_OUT_OF_BOUNDS = "POSITION_OUT_OF_BOUNDS"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    DATABASE_ERROR = "DATABASE_ERROR"
    BACKUP_CREATION_FAILED = "BACKUP_CREATION_FAILED"
    BACKUP_CORRUPTED = "BACKUP_CORRUPTED"
    SCHEMA_VERSION_MISMATCH = "SCHEMA_VERSION_MISMATCH"


# ============================================================================
# SYSTEM ERROR CONTRACT
# ============================================================================

@dataclass(frozen=True)
class ErrorDetail:
    message: str
    field: Optional[str] = None
    constraint: Optional[str] = None


@dataclass(frozen=True)
class AppError:
    code: ErrorCode
    message: str
    timestamp: str  # ISO 8601
    recoverable: bool
    details: List[ErrorDetail] = field(default_factory=list)
    suggested_action: Optional[str] = None


# ============================================================================
# PROCESSING CONFIGURATION & STATISTICS
# ============================================================================

@dataclass(frozen=True)
class CustomTypingFilter:
    preserve_case: bool
    preserve_punctuation: bool
    preserve_numbers: bool
    preserve_symbols: bool
    custom_allowed_characters: Optional[str] = None


@dataclass(frozen=True)
class ProcessingProfile:
    remove_headers: bool = True
    remove_footers: bool = True
    remove_page_numbers: bool = True
    repair_hyphenation: bool = True
    merge_wrapped_lines: bool = True
    normalize_unicode: bool = True      # ftfy + unicodedata NFC
    normalize_whitespace: bool = True
    exclude_references: bool = False
    exclude_acknowledgments: bool = False
    exclude_preface: bool = False
    min_heading_confidence: float = 0.65  # Range [0.0, 1.0]
    enable_local_ocr_fallback: bool = True

    def __post_init__(self) -> None:
        if not (0.0 <= self.min_heading_confidence <= 1.0):
            raise ValueError(f"min_heading_confidence must be between 0.0 and 1.0, got {self.min_heading_confidence}")

    @classmethod
    def from_dict(cls, data: dict) -> ProcessingProfile:
        if not data:
            return cls()
        return cls(
            remove_headers=data.get("remove_headers", data.get("removeHeaders", True)),
            remove_footers=data.get("remove_footers", data.get("removeFooters", True)),
            remove_page_numbers=data.get("remove_page_numbers", data.get("removePageNumbers", True)),
            repair_hyphenation=data.get("repair_hyphenation", data.get("repairHyphenation", True)),
            merge_wrapped_lines=data.get("merge_wrapped_lines", data.get("mergeWrappedLines", True)),
            normalize_unicode=data.get("normalize_unicode", data.get("normalizeUnicode", True)),
            normalize_whitespace=data.get("normalize_whitespace", data.get("normalizeWhitespace", True)),
            exclude_references=data.get("exclude_references", data.get("excludeReferences", False)),
            exclude_acknowledgments=data.get("exclude_acknowledgments", data.get("excludeAcknowledgments", False)),
            exclude_preface=data.get("exclude_preface", data.get("excludePreface", False)),
            min_heading_confidence=float(data.get("min_heading_confidence", data.get("minHeadingConfidence", 0.65))),
            enable_local_ocr_fallback=data.get("enable_local_ocr_fallback", data.get("enableLocalOcrFallback", True)),
        )


@dataclass(frozen=True)
class ProcessingStatistics:
    total_pages: int
    total_words: int
    total_characters: int
    detected_chapters_count: int
    detected_sections_count: int
    removed_headers_count: int
    removed_footers_count: int
    removed_page_numbers_count: int
    repaired_hyphenations_count: int
    ocr_applied_pages_count: int
    processing_duration_ms: int


# ============================================================================
# TEXT REPRESENTATIONS & BI-DIRECTIONAL OFFSET MAPPING
# ============================================================================

@dataclass(frozen=True)
class CharacterOffsetMap:
    """
    Bi-directional character mapping to correlate typing position with display and source texts.
    Invariant:
    len(typing_to_display_indices) == len(typing_text)
    len(display_to_source_indices) == len(display_text)
    """
    typing_to_display_indices: Tuple[int, ...]
    display_to_source_indices: Tuple[int, ...]


@dataclass(frozen=True)
class TextRepresentations:
    source_text: str
    normalized_text: str
    display_text: str
    typing_text: str
    offset_map: CharacterOffsetMap

    def __post_init__(self) -> None:
        if len(self.offset_map.typing_to_display_indices) != len(self.typing_text):
            raise ValueError(
                f"offset_map length mismatch: typing_to_display has {len(self.offset_map.typing_to_display_indices)} "
                f"elements, typing_text has {len(self.typing_text)} characters"
            )


# ============================================================================
# DOCUMENT ENTITIES & STRUCTURAL NODES
# ============================================================================

@dataclass(frozen=True)
class DocumentEntity:
    id: DocumentId
    user_id: UserId
    title: str
    author: str
    file_name: str
    file_path: str
    file_hash: str  # SHA-256
    source_format: DocumentFormat
    word_count: int
    character_count: int
    status: IngestionStatus
    processing_profile: ProcessingProfile
    created_at: str  # ISO 8601
    updated_at: str  # ISO 8601
    error_message: Optional[str] = None


@dataclass(frozen=True)
class DocumentVersion:
    id: VersionId
    document_id: DocumentId
    version_number: int
    processing_profile: ProcessingProfile
    statistics: ProcessingStatistics
    created_at: str


@dataclass(frozen=True)
class StructuralNodeSignals:
    font_size_score: float
    bold_weight_score: float
    numbering_score: float
    position_score: float
    whitespace_score: float
    short_line_score: float
    paragraph_length_penalty: float


@dataclass(frozen=True)
class StructuralNodeConfidence:
    score: float  # Range [0.0, 1.0]
    signals: StructuralNodeSignals

    def __post_init__(self) -> None:
        if not (0.0 <= self.score <= 1.0):
            raise ValueError(f"Confidence score must be between 0.0 and 1.0, got {self.score}")


@dataclass(frozen=True)
class ChapterEntity:
    id: ChapterId
    document_id: DocumentId
    parent_id: Optional[ChapterId]  # Nullable for root chapters
    title: str
    level: StructuralLevel
    order_index: int
    page_start: int
    page_end: int
    text_start_char: int
    text_end_char: int
    confidence: StructuralNodeConfidence
    included_in_practice: bool
    created_at: str


@dataclass(frozen=True)
class SectionEntity:
    id: SectionId
    document_id: DocumentId
    chapter_id: ChapterId
    title: str
    order_index: int
    page_start: int
    page_end: int
    text_start_char: int
    text_end_char: int
    word_count: int
    character_count: int
    included_in_practice: bool
    created_at: str


@dataclass(frozen=True)
class ParagraphEntity:
    id: ParagraphId
    document_id: DocumentId
    chapter_id: ChapterId
    section_id: SectionId
    order_index: int
    representations: TextRepresentations
    source_page: int
    source_position_y: float
    created_at: str


# ============================================================================
# INGESTION PREVIEWS & CORRECTIONS
# ============================================================================

@dataclass(frozen=True)
class BeforeAfterSample:
    title: str
    before_text: str
    after_text: str
    cleanup_category: Literal["hyphenation", "header_footer", "page_number", "whitespace"]


@dataclass(frozen=True)
class SectionPreviewNode:
    id: str
    title: str
    word_count: int
    included: bool


@dataclass(frozen=True)
class ChapterPreviewNode:
    id: str
    title: str
    level: StructuralLevel
    page_number: int
    confidence_score: float
    included: bool
    sub_sections: List[SectionPreviewNode] = field(default_factory=list)


@dataclass(frozen=True)
class IngestionPreview:
    document_id: DocumentId
    detected_title: str
    detected_author: str
    format: DocumentFormat
    statistics: ProcessingStatistics
    structure_tree: List[ChapterPreviewNode]
    sample_cleanups: List[BeforeAfterSample]


@dataclass(frozen=True)
class SectionUpdateRequest:
    id: str
    title: str
    order_index: int
    included_in_practice: bool


@dataclass(frozen=True)
class ChapterUpdateRequest:
    id: str
    title: str
    order_index: int
    included_in_practice: bool
    sections: List[SectionUpdateRequest]


@dataclass(frozen=True)
class StructureUpdateRequest:
    chapters: List[ChapterUpdateRequest]
    title: Optional[str] = None
    author: Optional[str] = None


# ============================================================================
# TYPING ENGINE & SESSION METRICS
# ============================================================================

@dataclass(frozen=True)
class KeystrokeInput:
    timestamp_ms: int
    key: str
    expected_char: str
    position: int
    is_backspace: bool


@dataclass(frozen=True)
class KeystrokeEvaluation:
    position: int
    expected_char: str
    actual_key: str
    is_correct: bool
    is_backspace: bool
    timestamp_ms: int
    latency_ms: int


@dataclass(frozen=True)
class TypingErrorRecord:
    id: str
    session_id: SessionId
    document_id: DocumentId
    section_id: SectionId
    expected_char: str
    actual_char: str
    position: int
    timestamp_ms: int
    resolved_via_backspace: bool


@dataclass(frozen=True)
class TypingMetrics:
    net_wpm: float          # ((correct_chars / 5) / (active_seconds / 60))
    gross_wpm: float        # ((total_chars / 5) / (active_seconds / 60))
    accuracy_pct: float     # (correct_keystrokes / total_keystrokes) * 100
    error_rate_pct: float   # (incorrect_keystrokes / total_keystrokes) * 100
    total_keystrokes: int
    correct_keystrokes: int
    incorrect_keystrokes: int
    backspace_count: int
    active_seconds: float
    consistency_pct: float  # 100 - Coefficient of variation of 1-second burst WPMs


@dataclass(frozen=True)
class TypingSessionEntity:
    id: SessionId
    user_id: UserId
    document_id: DocumentId
    chapter_id: ChapterId
    section_id: SectionId
    start_time: str
    state: TypingSessionState
    typing_mode: TypingMode
    metrics: TypingMetrics
    completed: bool
    created_at: str
    end_time: Optional[str] = None


# ============================================================================
# READING PROGRESSION & RESUME POINTER
# ============================================================================

@dataclass(frozen=True)
class ReadingPositionPointer:
    document_id: DocumentId
    chapter_id: ChapterId
    section_id: SectionId
    paragraph_id: ParagraphId
    character_offset: int


@dataclass(frozen=True)
class ReadingProgressEntity:
    id: str
    user_id: UserId
    document_id: DocumentId
    position: ReadingPositionPointer
    completion_percentage: float  # [0.0, 100.0]
    is_completed: bool
    last_practiced_at: str
    updated_at: str


# ============================================================================
# WEAK-KEY & ANALYTIC DRILLS
# ============================================================================

@dataclass(frozen=True)
class SubstitutionCount:
    substituted_for: str
    count: int


@dataclass(frozen=True)
class WeakKeyAggregate:
    character: str
    error_count: int
    total_occurrences: int
    error_rate_pct: float
    common_substitutions: List[SubstitutionCount]


@dataclass(frozen=True)
class WeakBigramAggregate:
    bigram: str
    error_count: int
    total_occurrences: int
    error_rate_pct: float


@dataclass(frozen=True)
class WeakKeyDrillPractice:
    drill_id: str
    target_keys: List[str]
    target_bigrams: List[str]
    generated_passage: str
    word_count: int
    source: Literal["document_vocabulary", "built_in_frequency_corpus"]


# ============================================================================
# BOOKMARKS, NOTES & SEARCH
# ============================================================================

@dataclass(frozen=True)
class BookmarkEntity:
    id: BookmarkId
    user_id: UserId
    document_id: DocumentId
    chapter_id: ChapterId
    section_id: SectionId
    paragraph_id: ParagraphId
    character_offset: int
    title: str
    created_at: str
    note_snippet: Optional[str] = None


@dataclass(frozen=True)
class NoteEntity:
    id: NoteId
    user_id: UserId
    document_id: DocumentId
    chapter_id: ChapterId
    section_id: SectionId
    paragraph_id: ParagraphId
    content: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class SearchQuery:
    query: str
    limit: int = 50
    offset: int = 0
    document_id: Optional[DocumentId] = None


@dataclass(frozen=True)
class SearchResultItem:
    document_id: DocumentId
    document_title: str
    chapter_id: ChapterId
    chapter_title: str
    section_id: SectionId
    section_title: str
    paragraph_id: ParagraphId
    page_number: int
    matched_snippet: str
    character_offset: int
    rank_score: float


@dataclass(frozen=True)
class SearchResults:
    query: str
    total_matches: int
    items: List[SearchResultItem]


# ============================================================================
# USER PROFILES & SETTINGS
# ============================================================================

@dataclass(frozen=True)
class UserProfileEntity:
    id: UserId
    display_name: str
    created_at: str
    last_active_at: str


@dataclass(frozen=True)
class GeneralSettings:
    startup_behavior: Literal["resume_last", "open_library"] = "resume_last"
    autosave_interval_seconds: int = 10
    confirm_before_delete: bool = True
    backup_storage_directory: str = ""


@dataclass(frozen=True)
class AppearanceSettings:
    theme: ThemeId = ThemeId.DARK
    font_family: str = "JetBrains Mono"
    font_size_pt: int = 14
    line_height_em: float = 1.6
    content_width_px: int = 840
    caret_style: CaretStyle = CaretStyle.BLOCK
    smooth_caret_animation: bool = True


@dataclass(frozen=True)
class TypingSettings:
    default_mode: TypingMode = TypingMode.STANDARD
    error_handling: ErrorHandlingMode = ErrorHandlingMode.ALLOW_WITH_BACKSPACE
    sound_keypress: bool = False
    sound_error: bool = False
    sound_complete: bool = True
    adaptive_difficulty_enabled: bool = False


@dataclass(frozen=True)
class DocumentSettings:
    default_processing_profile: ProcessingProfile = field(default_factory=ProcessingProfile)
    auto_run_ocr_if_low_confidence: bool = False


@dataclass(frozen=True)
class PrivacySettings:
    local_telemetry_enabled: bool = False
    detailed_error_logging: bool = True


@dataclass(frozen=True)
class UserSettings:
    user_id: UserId
    general: GeneralSettings
    appearance: AppearanceSettings
    typing: TypingSettings
    documents: DocumentSettings
    privacy: PrivacySettings
    updated_at: str


# ============================================================================
# BACKUP & EXPORT
# ============================================================================

@dataclass(frozen=True)
class BackupFileItem:
    relative_path: str
    checksum_sha256: str
    byte_size: int


@dataclass(frozen=True)
class BackupManifest:
    backup_version: int  # 1
    app_version: str
    exported_at: str
    database_checksum_sha256: str
    documents_count: int
    sessions_count: int
    files: List[BackupFileItem]


@dataclass(frozen=True)
class BackupValidationResult:
    is_valid: bool
    validation_errors: List[str]
    manifest: Optional[BackupManifest] = None


# ============================================================================
# API CONTRACT REQUEST & RESPONSE MODELS (api.json)
# ============================================================================

@dataclass(frozen=True)
class ImportDocumentRequest:
    filePath: str
    profileOverride: Optional[ProcessingProfile] = None


@dataclass(frozen=True)
class ExclusionUpdateRequest:
    targetType: Literal["chapter", "section"]
    targetId: str
    includedInPractice: bool


@dataclass(frozen=True)
class DocumentLibraryCard:
    id: str
    title: str
    author: str
    sourceFormat: DocumentFormat
    completionPercentage: float
    currentChapterTitle: str
    averageWpm: float
    averageAccuracy: float
    totalWords: int
    lastPracticedAt: Optional[str] = None


@dataclass(frozen=True)
class TreeSectionNode:
    id: str
    title: str
    orderIndex: int
    pageStart: int
    pageEnd: int
    wordCount: int
    characterCount: int
    includedInPractice: bool


@dataclass(frozen=True)
class TreeChapterNode:
    id: str
    title: str
    level: StructuralLevel
    orderIndex: int
    pageStart: int
    pageEnd: int
    includedInPractice: bool
    sections: List[TreeSectionNode] = field(default_factory=list)


@dataclass(frozen=True)
class DocumentStructureTree:
    document: DocumentEntity
    chapters: List[TreeChapterNode] = field(default_factory=list)


@dataclass(frozen=True)
class SectionParagraphItem:
    id: str
    orderIndex: int
    sourceText: str
    displayText: str
    typingText: str
    typingToDisplayIndices: List[int]


@dataclass(frozen=True)
class SectionContentResponse:
    sectionId: str
    title: str
    paragraphs: List[SectionParagraphItem]


@dataclass(frozen=True)
class StartSessionRequest:
    documentId: str
    chapterId: str
    sectionId: str
    typingMode: TypingMode
    errorHandlingMode: Optional[ErrorHandlingMode] = ErrorHandlingMode.ALLOW_WITH_BACKSPACE


@dataclass(frozen=True)
class SubmitKeystrokesRequest:
    keystrokes: List[KeystrokeInput]


@dataclass(frozen=True)
class SetSessionStateRequest:
    state: Literal["active", "paused"]


@dataclass(frozen=True)
class KeystrokeBatchResult:
    evaluations: List[KeystrokeEvaluation]
    currentMetrics: TypingMetrics
    currentPosition: int


@dataclass(frozen=True)
class AnalyticsOverview:
    averageWpm: float
    bestWpm: float
    averageAccuracy: float
    totalActiveTimeSeconds: float
    totalWordsTyped: int
    totalCharactersTyped: int
    currentDailyStreakDays: int
    longestDailyStreakDays: int
    completedChaptersCount: int
    completedBooksCount: int


@dataclass(frozen=True)
class TrendDayItem:
    date: str
    activeSeconds: float
    averageWpm: float
    accuracyPct: float
    wordsTyped: int


@dataclass(frozen=True)
class AnalyticsTrends:
    days: List[TrendDayItem]


@dataclass(frozen=True)
class ChapterBreakdownItem:
    chapterId: str
    title: str
    completionPercentage: float
    averageWpm: float
    accuracyPct: float
    timeTypedSeconds: float


@dataclass(frozen=True)
class DocumentAnalytics:
    documentId: str
    completionPercentage: float
    timeTypedSeconds: float
    wordsTyped: int
    averageWpm: float
    accuracyPct: float
    sessionsCount: int
    chapterBreakdown: List[ChapterBreakdownItem]


@dataclass(frozen=True)
class CreateBookmarkRequest:
    documentId: str
    chapterId: str
    sectionId: str
    paragraphId: str
    characterOffset: int
    title: str
    noteSnippet: Optional[str] = None


@dataclass(frozen=True)
class CreateNoteRequest:
    documentId: str
    chapterId: str
    sectionId: str
    paragraphId: str
    content: str


@dataclass(frozen=True)
class UpdateNoteRequest:
    content: str


@dataclass(frozen=True)
class GenerateWeakKeyDrillRequest:
    wordCount: int = 100
    documentId: Optional[str] = None
    targetKeys: Optional[List[str]] = None


@dataclass(frozen=True)
class ExportBackupRequest:
    destinationDirectory: str


@dataclass(frozen=True)
class ExportBackupResponse:
    backupFilePath: str
    manifest: BackupManifest


@dataclass(frozen=True)
class BackupFileRequest:
    backupFilePath: str

