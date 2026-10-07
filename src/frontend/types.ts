/**
 * TypeRead Frontend Domain Types & API Client Contracts
 * Adheres strictly to .orchestrator/blackboard/contracts/types.ts and api.json
 */

export * from '../../.orchestrator/blackboard/contracts/types';

import type {
  DocumentId,
  ChapterId,
  SectionId,
  ParagraphId,
  SessionId,
  BookmarkId,
  NoteId,
  TypingMode,
  ErrorHandlingMode,
  TypingSessionState,
  KeystrokeInput,
  TypingMetrics,
  ProcessingProfile,
  StructureUpdateRequest,
  ParagraphEntity,
} from '../../.orchestrator/blackboard/contracts/types';

export interface ImportDocumentRequest {
  readonly filePath: string;
  readonly profileOverride?: ProcessingProfile;
}

export interface ExclusionUpdateRequest {
  readonly targetType: 'chapter' | 'section';
  readonly targetId: ChapterId | SectionId | string;
  readonly includedInPractice: boolean;
}

export interface StartSessionRequest {
  readonly documentId: DocumentId;
  readonly chapterId: ChapterId;
  readonly sectionId: SectionId;
  readonly typingMode?: TypingMode;
  readonly errorHandlingMode?: ErrorHandlingMode;
}

export interface SubmitKeystrokesRequest {
  readonly keystrokes: readonly KeystrokeInput[];
}

export interface SetSessionStateRequest {
  readonly state: TypingSessionState;
}

export interface KeystrokeBatchResult {
  readonly currentPosition: number;
  readonly currentMetrics: TypingMetrics;
  readonly sectionCompleted: boolean;
}

export interface SectionContent {
  readonly sectionId: SectionId;
  readonly title: string;
  readonly paragraphs: readonly ParagraphEntity[];
}

export interface AnalyticsOverview {
  readonly totalSessions: number;
  readonly totalPracticeSeconds: number;
  readonly averageNetWpm: number;
  readonly averageAccuracyPct: number;
  readonly totalCharactersTyped: number;
  readonly booksCompleted: number;
}

export interface DailyActivityPoint {
  readonly date: string;
  readonly practiceSeconds: number;
  readonly charactersTyped: number;
  readonly avgNetWpm: number;
  readonly avgAccuracy: number;
}

export interface AnalyticsTrends {
  readonly dailyActivity: readonly DailyActivityPoint[];
}

export interface DocumentAnalytics {
  readonly documentId: DocumentId;
  readonly totalTimeSeconds: number;
  readonly charactersTyped: number;
  readonly currentProgressPct: number;
  readonly averageWpm: number;
  readonly averageAccuracyPct: number;
}

export interface CreateBookmarkRequest {
  readonly documentId: DocumentId;
  readonly chapterId: ChapterId;
  readonly sectionId: SectionId;
  readonly paragraphId: ParagraphId;
  readonly characterOffset: number;
  readonly title: string;
  readonly noteSnippet?: string;
}

export interface CreateNoteRequest {
  readonly documentId: DocumentId;
  readonly chapterId: ChapterId;
  readonly sectionId: SectionId;
  readonly paragraphId: ParagraphId;
  readonly content: string;
}

export interface UpdateNoteRequest {
  readonly content: string;
}

export interface GenerateWeakKeyDrillRequest {
  readonly wordCount?: number;
  readonly documentId?: DocumentId;
  readonly targetKeys?: readonly string[];
}

export interface ExportBackupRequest {
  readonly destinationDirectory: string;
}

export interface BackupFileRequest {
  readonly backupFilePath: string;
}

export interface BackupRestoreResult {
  readonly restoredAt: string;
  readonly documentsCount: number;
  readonly sessionsCount: number;
}
