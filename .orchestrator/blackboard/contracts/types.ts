/**
 * TypeRead Core Domain Types & Interfaces
 * Specification Version: 1.0.0
 * Architecture Gate: GATE_1_ARCHITECT
 * 
 * Invariants & Strict Design:
 * - Zero 'any' types.
 * - Branded string types for entity IDs to prevent accidental ID mixing.
 * - Discriminated unions for state machines and processing results.
 * - Exact typing for all domain primitives, metrics, and configurations.
 */

// ============================================================================
// BRANDED IDENTIFIER TYPES
// ============================================================================

export type UserId = string & { readonly __brand: unique symbol };
export type DocumentId = string & { readonly __brand: unique symbol };
export type ChapterId = string & { readonly __brand: unique symbol };
export type SectionId = string & { readonly __brand: unique symbol };
export type ParagraphId = string & { readonly __brand: unique symbol };
export type SessionId = string & { readonly __brand: unique symbol };
export type BookmarkId = string & { readonly __brand: unique symbol };
export type NoteId = string & { readonly __brand: unique symbol };
export type VersionId = string & { readonly __brand: unique symbol };

// Helper constructor signatures for branded IDs
export const createUserId = (id: string): UserId => id as UserId;
export const createDocumentId = (id: string): DocumentId => id as DocumentId;
export const createChapterId = (id: string): ChapterId => id as ChapterId;
export const createSectionId = (id: string): SectionId => id as SectionId;
export const createParagraphId = (id: string): ParagraphId => id as ParagraphId;
export const createSessionId = (id: string): SessionId => id as SessionId;
export const createBookmarkId = (id: string): BookmarkId => id as BookmarkId;
export const createNoteId = (id: string): NoteId => id as NoteId;

// ============================================================================
// ENUMS & CONSTANT UNIONS
// ============================================================================

export type DocumentFormat =
  | 'pdf'
  | 'epub'
  | 'docx'
  | 'txt'
  | 'markdown'
  | 'html';

export type IngestionStatus =
  | 'pending'
  | 'validating'
  | 'extracting'
  | 'normalizing'
  | 'cleaning'
  | 'detecting_structure'
  | 'preview_ready'
  | 'committed'
  | 'failed';

export type StructuralLevel = 'part' | 'chapter' | 'section' | 'subsection';

export type HeadingTag = 'H1' | 'H2' | 'H3' | 'H4' | 'H5' | 'H6' | 'PARAGRAPH';

export type TypingMode =
  | 'standard'        // Original text preserved (case, punctuation, numbers)
  | 'lowercase'       // All letters converted to lowercase
  | 'no_punctuation'  // Punctuation stripped, words preserved
  | 'letters_only'    // Only A-Z, a-z, and single spaces
  | 'numbers'         // Numbers preserved
  | 'punctuation'     // Punctuation emphasis
  | 'quotes'          // Preserves quotations
  | 'custom';         // Configured via CustomTypingFilter

export type ErrorHandlingMode =
  | 'allow_with_backspace' // Standard: records errors, cursor moves, backspace allows correction
  | 'stop_on_error'        // Cursor locks on incorrect character until correct key is pressed
  | 'immediate_backspace'; // Must backspace immediately upon error

export type CaretStyle = 'line' | 'block' | 'underline' | 'bar_blinking';

export type ThemeId =
  | 'light'
  | 'dark'
  | 'sepia'
  | 'paper'
  | 'high_contrast'
  | 'midnight';

export type TypingSessionState =
  | 'ready'
  | 'active'
  | 'paused'
  | 'completed'
  | 'aborted';

export type ErrorCode =
  | 'FILE_NOT_FOUND'
  | 'FILE_UNREADABLE'
  | 'UNSUPPORTED_FORMAT'
  | 'CORRUPTED_DOCUMENT'
  | 'EMPTY_DOCUMENT'
  | 'OCR_REQUIRED'
  | 'OCR_FAILED'
  | 'PARSING_FAILED'
  | 'DOCUMENT_NOT_FOUND'
  | 'DOCUMENT_ALREADY_EXISTS'
  | 'CHAPTER_NOT_FOUND'
  | 'SECTION_NOT_FOUND'
  | 'PARAGRAPH_NOT_FOUND'
  | 'SESSION_NOT_FOUND'
  | 'SESSION_ALREADY_FINISHED'
  | 'INVALID_KEYSTROKE'
  | 'POSITION_OUT_OF_BOUNDS'
  | 'USER_NOT_FOUND'
  | 'DATABASE_ERROR'
  | 'BACKUP_CREATION_FAILED'
  | 'BACKUP_CORRUPTED'
  | 'SCHEMA_VERSION_MISMATCH';

// ============================================================================
// SYSTEM ERROR CONTRACT
// ============================================================================

export interface ErrorDetail {
  readonly field?: string;
  readonly message: string;
  readonly constraint?: string;
}

export interface AppError {
  readonly code: ErrorCode;
  readonly message: string;
  readonly details?: readonly ErrorDetail[];
  readonly timestamp: string; // ISO 8601
  readonly recoverable: boolean;
  readonly suggestedAction?: string;
}

// ============================================================================
// DOCUMENT PROCESSING CONFIGURATION & PROFILE
// ============================================================================

export interface CustomTypingFilter {
  readonly preserveCase: boolean;
  readonly preservePunctuation: boolean;
  readonly preserveNumbers: boolean;
  readonly preserveSymbols: boolean;
  readonly customAllowedCharacters?: string;
}

export interface ProcessingProfile {
  readonly removeHeaders: boolean;
  readonly removeFooters: boolean;
  readonly removePageNumbers: boolean;
  readonly repairHyphenation: boolean;
  readonly mergeWrappedLines: boolean;
  readonly normalizeUnicode: boolean;     // ftfy / NFC normalization
  readonly normalizeWhitespace: boolean;
  readonly excludeReferences: boolean;
  readonly excludeAcknowledgments: boolean;
  readonly excludePreface: boolean;
  readonly minHeadingConfidence: number;  // Range [0.0, 1.0]
  readonly enableLocalOcrFallback: boolean;
}

export interface ProcessingStatistics {
  readonly totalPages: number;
  readonly totalWords: number;
  readonly totalCharacters: number;
  readonly detectedChaptersCount: number;
  readonly detectedSectionsCount: number;
  readonly removedHeadersCount: number;
  readonly removedFootersCount: number;
  readonly removedPageNumbersCount: number;
  readonly repairedHyphenationsCount: number;
  readonly ocrAppliedPagesCount: number;
  readonly processingDurationMs: number;
}

// ============================================================================
// TEXT REPRESENTATIONS & OFFSET MAPPING
// ============================================================================

export interface CharacterOffsetMap {
  /**
   * For every character index in `typingText`, index of corresponding character in `displayText`.
   * Essential for highlighting the current source character on the UI.
   */
  readonly typingToDisplayIndices: readonly number[];
  /**
   * For every character index in `displayText`, index in `sourceText`.
   */
  readonly displayToSourceIndices: readonly number[];
}

export interface TextRepresentations {
  readonly sourceText: string;
  readonly normalizedText: string;
  readonly displayText: string;
  readonly typingText: string;
  readonly offsetMap: CharacterOffsetMap;
}

// ============================================================================
// DOCUMENT & STRUCTURAL TREE ENTITIES
// ============================================================================

export interface DocumentEntity {
  readonly id: DocumentId;
  readonly userId: UserId;
  readonly title: string;
  readonly author: string;
  readonly fileName: string;
  readonly filePath: string;
  readonly fileHash: string; // SHA-256
  readonly sourceFormat: DocumentFormat;
  readonly wordCount: number;
  readonly characterCount: number;
  readonly status: IngestionStatus;
  readonly processingProfile: ProcessingProfile;
  readonly errorMessage?: string;
  readonly createdAt: string; // ISO 8601
  readonly updatedAt: string; // ISO 8601
}

export interface DocumentVersion {
  readonly id: VersionId;
  readonly documentId: DocumentId;
  readonly versionNumber: number;
  readonly processingProfile: ProcessingProfile;
  readonly statistics: ProcessingStatistics;
  readonly createdAt: string;
}

export interface StructuralNodeConfidence {
  readonly score: number; // Range [0.0, 1.0]
  readonly signals: {
    readonly fontSizeScore: number;
    readonly boldWeightScore: number;
    readonly numberingScore: number;
    readonly positionScore: number;
    readonly whitespaceScore: number;
    readonly shortLineScore: number;
    readonly paragraphLengthPenalty: number;
  };
}

export interface ChapterEntity {
  readonly id: ChapterId;
  readonly documentId: DocumentId;
  readonly parentId: ChapterId | null; // For hierarchical nesting
  readonly title: string;
  readonly level: StructuralLevel;
  readonly orderIndex: number;
  readonly pageStart: number;
  readonly pageEnd: number;
  readonly textStartChar: number;
  readonly textEndChar: number;
  readonly confidence: StructuralNodeConfidence;
  readonly includedInPractice: boolean;
  readonly createdAt: string;
}

export interface SectionEntity {
  readonly id: SectionId;
  readonly documentId: DocumentId;
  readonly chapterId: ChapterId;
  readonly title: string;
  readonly orderIndex: number;
  readonly pageStart: number;
  readonly pageEnd: number;
  readonly textStartChar: number;
  readonly textEndChar: number;
  readonly wordCount: number;
  readonly characterCount: number;
  readonly includedInPractice: boolean;
  readonly createdAt: string;
}

export interface ParagraphEntity {
  readonly id: ParagraphId;
  readonly documentId: DocumentId;
  readonly chapterId: ChapterId;
  readonly sectionId: SectionId;
  readonly orderIndex: number;
  readonly representations: TextRepresentations;
  readonly sourcePage: number;
  readonly sourcePositionY: number;
  readonly createdAt: string;
}

export interface DocumentStructureTree {
  readonly document: DocumentEntity;
  readonly chapters: readonly (ChapterEntity & {
    readonly sections: readonly (SectionEntity & {
      readonly paragraphs: readonly ParagraphEntity[];
    })[];
  })[];
}

// Ingestion preview payload presented to user before saving
export interface IngestionPreview {
  readonly documentId: DocumentId;
  readonly detectedTitle: string;
  readonly detectedAuthor: string;
  readonly format: DocumentFormat;
  readonly statistics: ProcessingStatistics;
  readonly structureTree: readonly ChapterPreviewNode[];
  readonly sampleCleanups: readonly BeforeAfterSample[];
}

export interface ChapterPreviewNode {
  readonly id: string; // Temp ID
  readonly title: string;
  readonly level: StructuralLevel;
  readonly pageNumber: number;
  readonly confidenceScore: number;
  readonly included: boolean;
  readonly subSections: readonly SectionPreviewNode[];
}

export interface SectionPreviewNode {
  readonly id: string;
  readonly title: string;
  readonly wordCount: number;
  readonly included: boolean;
}

export interface BeforeAfterSample {
  readonly title: string;
  readonly beforeText: string;
  readonly afterText: string;
  readonly cleanupCategory: 'hyphenation' | 'header_footer' | 'page_number' | 'whitespace';
}

// Manual corrections request
export interface StructureUpdateRequest {
  readonly title?: string;
  readonly author?: string;
  readonly chapters: readonly {
    readonly id: ChapterId | string;
    readonly title: string;
    readonly orderIndex: number;
    readonly includedInPractice: boolean;
    readonly sections: readonly {
      readonly id: SectionId | string;
      readonly title: string;
      readonly orderIndex: number;
      readonly includedInPractice: boolean;
    }[];
  }[];
}

// ============================================================================
// TYPING ENGINE & SESSION METRICS
// ============================================================================

export interface KeystrokeInput {
  readonly timestampMs: number;
  readonly key: string;             // Exact key pressed
  readonly expectedChar: string;    // Expected char in typingText
  readonly position: number;        // Char offset in current typingText
  readonly isBackspace: boolean;
}

export interface KeystrokeEvaluation {
  readonly position: number;
  readonly expectedChar: string;
  readonly actualKey: string;
  readonly isCorrect: boolean;
  readonly isBackspace: boolean;
  readonly timestampMs: number;
  readonly latencyMs: number;
}

export interface TypingErrorRecord {
  readonly id: string;
  readonly sessionId: SessionId;
  readonly documentId: DocumentId;
  readonly sectionId: SectionId;
  readonly expectedChar: string;
  readonly actualChar: string;
  readonly position: number;
  readonly timestampMs: number;
  readonly resolvedViaBackspace: boolean;
}

export interface TypingMetrics {
  readonly netWpm: number;          // Words Per Minute: ((correct_chars / 5) / (active_seconds / 60))
  readonly grossWpm: number;        // Raw WPM: ((total_chars / 5) / (active_seconds / 60))
  readonly accuracyPct: number;     // (correct_keystrokes / total_keystrokes) * 100
  readonly errorRatePct: number;    // (incorrect_keystrokes / total_keystrokes) * 100
  readonly totalKeystrokes: number;
  readonly correctKeystrokes: number;
  readonly incorrectKeystrokes: number;
  readonly backspaceCount: number;
  readonly activeSeconds: number;
  readonly consistencyPct: number;  // 100 - Coefficient of variation of 1-second burst WPMs
}

export interface TypingSessionEntity {
  readonly id: SessionId;
  readonly userId: UserId;
  readonly documentId: DocumentId;
  readonly chapterId: ChapterId;
  readonly sectionId: SectionId;
  readonly startTime: string;       // ISO 8601
  readonly endTime: string | null;  // ISO 8601
  readonly state: TypingSessionState;
  readonly typingMode: TypingMode;
  readonly metrics: TypingMetrics;
  readonly completed: boolean;
  readonly createdAt: string;
}

// ============================================================================
// READING PROGRESSION & RESUME POINTER
// ============================================================================

export interface ReadingPositionPointer {
  readonly documentId: DocumentId;
  readonly chapterId: ChapterId;
  readonly sectionId: SectionId;
  readonly paragraphId: ParagraphId;
  readonly characterOffset: number; // Offset into current paragraph typingText
}

export interface ReadingProgressEntity {
  readonly id: string;
  readonly userId: UserId;
  readonly documentId: DocumentId;
  readonly position: ReadingPositionPointer;
  readonly completionPercentage: number; // Range [0.0, 100.0]
  readonly isCompleted: boolean;
  readonly lastPracticedAt: string;      // ISO 8601
  readonly updatedAt: string;
}

// ============================================================================
// WEAK-KEY & ANALYTIC DRILLS
// ============================================================================

export interface WeakKeyAggregate {
  readonly character: string;
  readonly errorCount: number;
  readonly totalOccurrences: number;
  readonly errorRatePct: number;
  readonly commonSubstitutions: readonly {
    readonly substitutedFor: string;
    readonly count: number;
  }[];
}

export interface WeakBigramAggregate {
  readonly bigram: string; // 2-character sequence, e.g. "th", "re"
  readonly errorCount: number;
  readonly totalOccurrences: number;
  readonly errorRatePct: number;
}

export interface WeakKeyDrillPractice {
  readonly drillId: string;
  readonly targetKeys: readonly string[];
  readonly targetBigrams: readonly string[];
  readonly generatedPassage: string; // Generated deterministically from document vocabulary / local corpus
  readonly wordCount: number;
  readonly source: 'document_vocabulary' | 'built_in_frequency_corpus';
}

// ============================================================================
// BOOKMARKS, NOTES & SEARCH
// ============================================================================

export interface BookmarkEntity {
  readonly id: BookmarkId;
  readonly userId: UserId;
  readonly documentId: DocumentId;
  readonly chapterId: ChapterId;
  readonly sectionId: SectionId;
  readonly paragraphId: ParagraphId;
  readonly characterOffset: number;
  readonly title: string;
  readonly noteSnippet?: string;
  readonly createdAt: string;
}

export interface NoteEntity {
  readonly id: NoteId;
  readonly userId: UserId;
  readonly documentId: DocumentId;
  readonly chapterId: ChapterId;
  readonly sectionId: SectionId;
  readonly paragraphId: ParagraphId;
  readonly content: string;
  readonly createdAt: string;
  readonly updatedAt: string;
}

export interface SearchQuery {
  readonly query: string;
  readonly documentId?: DocumentId;
  readonly limit: number;
  readonly offset: number;
}

export interface SearchResultItem {
  readonly documentId: DocumentId;
  readonly documentTitle: string;
  readonly chapterId: ChapterId;
  readonly chapterTitle: string;
  readonly sectionId: SectionId;
  readonly sectionTitle: string;
  readonly paragraphId: ParagraphId;
  readonly pageNumber: number;
  readonly matchedSnippet: string; // Formatted with highlights, e.g. <mark>habit</mark>
  readonly characterOffset: number;
  readonly rankScore: number;
}

export interface SearchResults {
  readonly query: string;
  readonly totalMatches: number;
  readonly items: readonly SearchResultItem[];
}

// ============================================================================
// USER PROFILES & SETTINGS
// ============================================================================

export interface UserProfileEntity {
  readonly id: UserId;
  readonly displayName: string;
  readonly createdAt: string;
  readonly lastActiveAt: string;
}

export interface UserSettings {
  readonly userId: UserId;
  readonly general: {
    readonly startupBehavior: 'resume_last' | 'open_library';
    readonly autosaveIntervalSeconds: number; // e.g. 10
    readonly confirmBeforeDelete: boolean;
    readonly backupStorageDirectory: string;
  };
  readonly appearance: {
    readonly theme: ThemeId;
    readonly fontFamily: string;
    readonly fontSizePt: number;
    readonly lineHeightEm: number;
    readonly contentWidthPx: number;
    readonly caretStyle: CaretStyle;
    readonly smoothCaretAnimation: boolean;
  };
  readonly typing: {
    readonly defaultMode: TypingMode;
    readonly errorHandling: ErrorHandlingMode;
    readonly soundKeypress: boolean;
    readonly soundError: boolean;
    readonly soundComplete: boolean;
    readonly adaptiveDifficultyEnabled: boolean;
  };
  readonly documents: {
    readonly defaultProcessingProfile: ProcessingProfile;
    readonly autoRunOcrIfLowConfidence: boolean;
  };
  readonly privacy: {
    readonly localTelemetryEnabled: boolean;
    readonly detailedErrorLogging: boolean;
  };
  readonly updatedAt: string;
}

// ============================================================================
// BACKUP & EXPORT
// ============================================================================

export interface BackupManifest {
  readonly backupVersion: number; // 1
  readonly appVersion: string;
  readonly exportedAt: string;    // ISO 8601
  readonly databaseChecksumSha256: string;
  readonly documentsCount: number;
  readonly sessionsCount: number;
  readonly files: readonly {
    readonly relativePath: string;
    readonly checksumSha256: string;
    readonly byteSize: number;
  }[];
}

export interface BackupValidationResult {
  readonly isValid: boolean;
  readonly manifest: BackupManifest | null;
  readonly validationErrors: readonly string[];
}
