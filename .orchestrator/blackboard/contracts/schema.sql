-- ============================================================================
-- TypeRead Production SQLite Database Schema
-- Specification Version: 1.0.0
-- Architecture Gate: GATE_1_ARCHITECT
-- Target SQLite Version: 3.38+ (supports FTS5, strict JSON, CHECK constraints)
-- ============================================================================

-- Strict Foreign Keys & WAL Pragma configuration
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA temp_store = MEMORY;

-- ============================================================================
-- SCHEMA VERSIONING & MIGRATIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    description TEXT NOT NULL
);

INSERT OR IGNORE INTO schema_migrations (version, description)
VALUES (1, 'Initial TypeRead v1.0 schema with FTS5, sessions, progress, and weak keys');

-- ============================================================================
-- USER PROFILES & SETTINGS
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY, -- UUID v4
    display_name TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    last_active_at TIMESTAMP NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS user_settings (
    user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    -- General Settings
    startup_behavior TEXT NOT NULL CHECK (startup_behavior IN ('resume_last', 'open_library')) DEFAULT 'resume_last',
    autosave_interval_seconds INTEGER NOT NULL CHECK (autosave_interval_seconds >= 2 AND autosave_interval_seconds <= 300) DEFAULT 10,
    confirm_before_delete INTEGER NOT NULL CHECK (confirm_before_delete IN (0, 1)) DEFAULT 1,
    backup_storage_directory TEXT NOT NULL DEFAULT '',
    -- Appearance Settings
    theme TEXT NOT NULL CHECK (theme IN ('light', 'dark', 'sepia', 'paper', 'high_contrast', 'midnight')) DEFAULT 'dark',
    font_family TEXT NOT NULL DEFAULT 'JetBrains Mono',
    font_size_pt INTEGER NOT NULL CHECK (font_size_pt >= 8 AND font_size_pt <= 48) DEFAULT 14,
    line_height_em REAL NOT NULL CHECK (line_height_em >= 1.0 AND line_height_em <= 3.0) DEFAULT 1.6,
    content_width_px INTEGER NOT NULL CHECK (content_width_px >= 400 AND content_width_px <= 1920) DEFAULT 840,
    caret_style TEXT NOT NULL CHECK (caret_style IN ('line', 'block', 'underline', 'bar_blinking')) DEFAULT 'block',
    smooth_caret_animation INTEGER NOT NULL CHECK (smooth_caret_animation IN (0, 1)) DEFAULT 1,
    -- Typing Settings
    default_typing_mode TEXT NOT NULL CHECK (default_typing_mode IN ('standard', 'lowercase', 'no_punctuation', 'letters_only', 'numbers', 'punctuation', 'quotes', 'custom')) DEFAULT 'standard',
    error_handling_mode TEXT NOT NULL CHECK (error_handling_mode IN ('allow_with_backspace', 'stop_on_error', 'immediate_backspace')) DEFAULT 'allow_with_backspace',
    sound_keypress INTEGER NOT NULL CHECK (sound_keypress IN (0, 1)) DEFAULT 0,
    sound_error INTEGER NOT NULL CHECK (sound_error IN (0, 1)) DEFAULT 0,
    sound_complete INTEGER NOT NULL CHECK (sound_complete IN (0, 1)) DEFAULT 1,
    adaptive_difficulty_enabled INTEGER NOT NULL CHECK (adaptive_difficulty_enabled IN (0, 1)) DEFAULT 0,
    -- Document Processing Defaults (JSON serialized ProcessingProfile)
    default_processing_profile_json TEXT NOT NULL DEFAULT '{"removeHeaders":true,"removeFooters":true,"removePageNumbers":true,"repairHyphenation":true,"mergeWrappedLines":true,"normalizeUnicode":true,"normalizeWhitespace":true,"excludeReferences":false,"excludeAcknowledgments":false,"excludePreface":false,"minHeadingConfidence":0.65,"enableLocalOcrFallback":true}',
    auto_run_ocr_if_low_confidence INTEGER NOT NULL CHECK (auto_run_ocr_if_low_confidence IN (0, 1)) DEFAULT 0,
    -- Privacy Settings
    local_telemetry_enabled INTEGER NOT NULL CHECK (local_telemetry_enabled IN (0, 1)) DEFAULT 0,
    detailed_error_logging INTEGER NOT NULL CHECK (detailed_error_logging IN (0, 1)) DEFAULT 1,
    updated_at TIMESTAMP NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- ============================================================================
-- DOCUMENTS & STRUCTURAL TREE
-- ============================================================================

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY, -- UUID v4
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    author TEXT NOT NULL DEFAULT 'Unknown',
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL, -- SHA-256 for duplicate detection
    source_format TEXT NOT NULL CHECK (source_format IN ('pdf', 'epub', 'docx', 'txt', 'markdown', 'html')),
    word_count INTEGER NOT NULL DEFAULT 0 CHECK (word_count >= 0),
    character_count INTEGER NOT NULL DEFAULT 0 CHECK (character_count >= 0),
    status TEXT NOT NULL CHECK (status IN (
        'pending', 'validating', 'extracting', 'normalizing',
        'cleaning', 'detecting_structure', 'preview_ready',
        'committed', 'failed'
    )) DEFAULT 'pending',
    processing_profile_json TEXT NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TIMESTAMP NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(user_id, file_hash)
);

CREATE TABLE IF NOT EXISTS document_versions (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL CHECK (version_number >= 1),
    processing_profile_json TEXT NOT NULL,
    statistics_json TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(document_id, version_number)
);

CREATE TABLE IF NOT EXISTS chapters (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    parent_id TEXT REFERENCES chapters(id) ON DELETE CASCADE, -- Nesting support
    title TEXT NOT NULL,
    level TEXT NOT NULL CHECK (level IN ('part', 'chapter', 'section', 'subsection')),
    order_index INTEGER NOT NULL CHECK (order_index >= 0),
    page_start INTEGER NOT NULL DEFAULT 1 CHECK (page_start >= 1),
    page_end INTEGER NOT NULL DEFAULT 1 CHECK (page_end >= page_start),
    text_start_char INTEGER NOT NULL DEFAULT 0 CHECK (text_start_char >= 0),
    text_end_char INTEGER NOT NULL DEFAULT 0 CHECK (text_end_char >= text_start_char),
    confidence_score REAL NOT NULL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    confidence_signals_json TEXT NOT NULL DEFAULT '{}',
    included_in_practice INTEGER NOT NULL CHECK (included_in_practice IN (0, 1)) DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(document_id, order_index)
);

CREATE TABLE IF NOT EXISTS sections (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chapter_id TEXT NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    order_index INTEGER NOT NULL CHECK (order_index >= 0),
    page_start INTEGER NOT NULL DEFAULT 1 CHECK (page_start >= 1),
    page_end INTEGER NOT NULL DEFAULT 1 CHECK (page_end >= page_start),
    text_start_char INTEGER NOT NULL DEFAULT 0 CHECK (text_start_char >= 0),
    text_end_char INTEGER NOT NULL DEFAULT 0 CHECK (text_end_char >= text_start_char),
    word_count INTEGER NOT NULL DEFAULT 0 CHECK (word_count >= 0),
    character_count INTEGER NOT NULL DEFAULT 0 CHECK (character_count >= 0),
    included_in_practice INTEGER NOT NULL CHECK (included_in_practice IN (0, 1)) DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(chapter_id, order_index)
);

CREATE TABLE IF NOT EXISTS paragraphs (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chapter_id TEXT NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    section_id TEXT NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    order_index INTEGER NOT NULL CHECK (order_index >= 0),
    source_text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    display_text TEXT NOT NULL,
    typing_text TEXT NOT NULL,
    offset_map_json TEXT NOT NULL, -- Serialized CharacterOffsetMap
    source_page INTEGER NOT NULL DEFAULT 1 CHECK (source_page >= 1),
    source_position_y REAL NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(section_id, order_index)
);

-- ============================================================================
-- READING & TYPING PROGRESSION (RESUME POINTER)
-- ============================================================================

CREATE TABLE IF NOT EXISTS reading_progress (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chapter_id TEXT NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    section_id TEXT NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    paragraph_id TEXT NOT NULL REFERENCES paragraphs(id) ON DELETE CASCADE,
    character_offset INTEGER NOT NULL DEFAULT 0 CHECK (character_offset >= 0),
    completion_percentage REAL NOT NULL DEFAULT 0.0 CHECK (completion_percentage >= 0.0 AND completion_percentage <= 100.0),
    is_completed INTEGER NOT NULL CHECK (is_completed IN (0, 1)) DEFAULT 0,
    last_practiced_at TIMESTAMP NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TIMESTAMP NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(user_id, document_id)
);

-- ============================================================================
-- TYPING SESSIONS & ERROR LOGGING
-- ============================================================================

CREATE TABLE IF NOT EXISTS typing_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chapter_id TEXT NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    section_id TEXT NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    state TEXT NOT NULL CHECK (state IN ('ready', 'active', 'paused', 'completed', 'aborted')) DEFAULT 'ready',
    session_mode TEXT NOT NULL CHECK (session_mode IN ('standard', 'lowercase', 'no_punctuation', 'letters_only', 'numbers', 'punctuation', 'quotes', 'custom')),
    error_handling_mode TEXT NOT NULL DEFAULT 'allow_with_backspace',
    active_seconds REAL NOT NULL DEFAULT 0.0 CHECK (active_seconds >= 0.0),
    total_characters INTEGER NOT NULL DEFAULT 0 CHECK (total_characters >= 0),
    correct_characters INTEGER NOT NULL DEFAULT 0 CHECK (correct_characters >= 0),
    incorrect_characters INTEGER NOT NULL DEFAULT 0 CHECK (incorrect_characters >= 0),
    backspaces INTEGER NOT NULL DEFAULT 0 CHECK (backspaces >= 0),
    net_wpm REAL NOT NULL DEFAULT 0.0 CHECK (net_wpm >= 0.0),
    gross_wpm REAL NOT NULL DEFAULT 0.0 CHECK (gross_wpm >= 0.0),
    accuracy_pct REAL NOT NULL DEFAULT 100.0 CHECK (accuracy_pct >= 0.0 AND accuracy_pct <= 100.0),
    consistency_pct REAL NOT NULL DEFAULT 100.0 CHECK (consistency_pct >= 0.0 AND consistency_pct <= 100.0),
    completed INTEGER NOT NULL CHECK (completed IN (0, 1)) DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS typing_errors (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES typing_sessions(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    section_id TEXT NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    expected_character TEXT NOT NULL,
    actual_character TEXT NOT NULL,
    character_position INTEGER NOT NULL CHECK (character_position >= 0),
    timestamp_ms INTEGER NOT NULL,
    resolved_via_backspace INTEGER NOT NULL CHECK (resolved_via_backspace IN (0, 1)) DEFAULT 0
);

-- ============================================================================
-- WEAK-KEY & BIGRAM AGGREGATES
-- ============================================================================

CREATE TABLE IF NOT EXISTS weak_key_aggregates (
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    character TEXT NOT NULL,
    error_count INTEGER NOT NULL DEFAULT 0 CHECK (error_count >= 0),
    total_occurrences INTEGER NOT NULL DEFAULT 0 CHECK (total_occurrences >= 0),
    common_substitutions_json TEXT NOT NULL DEFAULT '{}',
    last_error_at TIMESTAMP NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY(user_id, character)
);

CREATE TABLE IF NOT EXISTS weak_bigram_aggregates (
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bigram TEXT NOT NULL,
    error_count INTEGER NOT NULL DEFAULT 0 CHECK (error_count >= 0),
    total_occurrences INTEGER NOT NULL DEFAULT 0 CHECK (total_occurrences >= 0),
    last_error_at TIMESTAMP NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY(user_id, bigram)
);

-- ============================================================================
-- BOOKMARKS & NOTES
-- ============================================================================

CREATE TABLE IF NOT EXISTS bookmarks (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chapter_id TEXT NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    section_id TEXT NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    paragraph_id TEXT NOT NULL REFERENCES paragraphs(id) ON DELETE CASCADE,
    character_offset INTEGER NOT NULL DEFAULT 0 CHECK (character_offset >= 0),
    title TEXT NOT NULL,
    note_snippet TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chapter_id TEXT NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    section_id TEXT NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    paragraph_id TEXT NOT NULL REFERENCES paragraphs(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TIMESTAMP NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- ============================================================================
-- HABIT TRACKING & DAILY STREAKS
-- ============================================================================

CREATE TABLE IF NOT EXISTS daily_streaks (
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    practice_date DATE NOT NULL,
    active_seconds REAL NOT NULL DEFAULT 0.0 CHECK (active_seconds >= 0.0),
    characters_typed INTEGER NOT NULL DEFAULT 0 CHECK (characters_typed >= 0),
    qualified INTEGER NOT NULL CHECK (qualified IN (0, 1)) DEFAULT 0,
    PRIMARY KEY(user_id, practice_date)
);

-- ============================================================================
-- FULL-TEXT SEARCH (FTS5) VIRTUAL TABLE & TRIGGERS
-- ============================================================================

CREATE VIRTUAL TABLE IF NOT EXISTS document_fts USING fts5(
    document_id UNINDEXED,
    chapter_id UNINDEXED,
    section_id UNINDEXED,
    paragraph_id UNINDEXED,
    document_title,
    chapter_title,
    section_title,
    content,
    tokenize = 'porter unicode61 remove_diacritics 1'
);

-- Trigger: Index new paragraph into FTS
CREATE TRIGGER IF NOT EXISTS trg_paragraphs_fts_insert AFTER INSERT ON paragraphs
BEGIN
    INSERT INTO document_fts(
        document_id,
        chapter_id,
        section_id,
        paragraph_id,
        document_title,
        chapter_title,
        section_title,
        content
    )
    SELECT
        new.document_id,
        new.chapter_id,
        new.section_id,
        new.id,
        d.title,
        c.title,
        s.title,
        new.display_text
    FROM documents d
    JOIN chapters c ON c.id = new.chapter_id
    JOIN sections s ON s.id = new.section_id
    WHERE d.id = new.document_id;
END;

-- Trigger: Remove paragraph from FTS when deleted
CREATE TRIGGER IF NOT EXISTS trg_paragraphs_fts_delete AFTER DELETE ON paragraphs
BEGIN
    DELETE FROM document_fts WHERE paragraph_id = old.id;
END;

-- Trigger: Update updated_at on document update
CREATE TRIGGER IF NOT EXISTS trg_documents_updated_at AFTER UPDATE ON documents
BEGIN
    UPDATE documents
    SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
    WHERE id = old.id;
END;

-- ============================================================================
-- PERFORMANCE INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(user_id, status);
CREATE INDEX IF NOT EXISTS idx_chapters_doc_order ON chapters(document_id, order_index);
CREATE INDEX IF NOT EXISTS idx_sections_chap_order ON sections(chapter_id, order_index);
CREATE INDEX IF NOT EXISTS idx_paragraphs_sec_order ON paragraphs(section_id, order_index);
CREATE INDEX IF NOT EXISTS idx_reading_progress_user ON reading_progress(user_id, last_practiced_at DESC);
CREATE INDEX IF NOT EXISTS idx_typing_sessions_user_date ON typing_sessions(user_id, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_typing_sessions_doc ON typing_sessions(document_id, completed);
CREATE INDEX IF NOT EXISTS idx_typing_errors_session ON typing_errors(session_id);
CREATE INDEX IF NOT EXISTS idx_bookmarks_user_doc ON bookmarks(user_id, document_id);
CREATE INDEX IF NOT EXISTS idx_notes_user_doc ON notes(user_id, document_id);
