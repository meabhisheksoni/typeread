/**
 * TypeRead Core Service & IPC API Client
 * Adheres strictly to api.json and types.ts contracts.
 */

import type {
  DocumentId,
  ChapterId,
  SectionId,
  SessionId,
  BookmarkId,
  NoteId,
  AppError,
  DocumentEntity,
  DocumentStructureTree,
  IngestionPreview,
  StructureUpdateRequest,
  ReadingProgressEntity,
  ReadingPositionPointer,
  TypingSessionEntity,
  WeakKeyAggregate,
  WeakKeyDrillPractice,
  SearchQuery,
  SearchResults,
  BookmarkEntity,
  NoteEntity,
  UserSettings,
  BackupManifest,
  BackupValidationResult,
} from '../../.orchestrator/blackboard/contracts/types';

import type {
  ImportDocumentRequest,
  ExclusionUpdateRequest,
  StartSessionRequest,
  SubmitKeystrokesRequest,
  SetSessionStateRequest,
  KeystrokeBatchResult,
  SectionContent,
  AnalyticsOverview,
  AnalyticsTrends,
  DocumentAnalytics,
  CreateBookmarkRequest,
  CreateNoteRequest,
  UpdateNoteRequest,
  GenerateWeakKeyDrillRequest,
  ExportBackupRequest,
  BackupFileRequest,
  BackupRestoreResult,
} from './types';

export class ApiClientError extends Error {
  public readonly appError?: AppError;
  public readonly statusCode: number;

  constructor(message: string, statusCode: number, appError?: AppError) {
    super(message);
    this.name = 'ApiClientError';
    this.statusCode = statusCode;
    this.appError = appError;
  }
}

export interface ApiClientConfig {
  baseUrl?: string;
  fetchFn?: typeof fetch;
}

export class TypeReadApiClient {
  private readonly baseUrl: string;
  private readonly fetch: typeof fetch;

  constructor(config?: ApiClientConfig) {
    this.baseUrl = (config?.baseUrl ?? 'http://127.0.0.1:8765/api/v1').replace(/\/$/, '');
    this.fetch = config?.fetchFn ?? (typeof fetch !== 'undefined' ? fetch : (async () => {
      throw new Error('fetch is not defined in this environment');
    }) as unknown as typeof fetch);
  }

  private async request<T>(
    method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE',
    path: string,
    body?: unknown,
    queryParams?: Record<string, string | number | boolean | undefined>
  ): Promise<T> {
    let url = `${this.baseUrl}${path}`;
    if (queryParams) {
      const sp = new URLSearchParams();
      for (const [key, value] of Object.entries(queryParams)) {
        if (value !== undefined) {
          sp.append(key, String(value));
        }
      }
      const qs = sp.toString();
      if (qs) {
        url += `?${qs}`;
      }
    }

    const headers: Record<string, string> = {
      'Accept': 'application/json',
    };
    if (body !== undefined) {
      headers['Content-Type'] = 'application/json';
    }

    const response = await this.fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });

    if (response.status === 204) {
      return undefined as unknown as T;
    }

    const contentType = response.headers?.get('content-type') ?? '';
    const isJson = contentType.includes('application/json');
    const data = isJson ? await response.json() : await response.text();

    if (!response.ok) {
      const appErr = isJson ? (data as AppError) : undefined;
      const message = appErr?.message || `HTTP ${response.status}: Request failed`;
      throw new ApiClientError(message, response.status, appErr);
    }

    return data as T;
  }

  // ==========================================================================
  // DOCUMENTS
  // ==========================================================================

  public async importDocument(request: ImportDocumentRequest): Promise<IngestionPreview> {
    return this.request<IngestionPreview>('POST', '/documents/import', request);
  }

  public async commitDocument(
    documentId: DocumentId,
    request: StructureUpdateRequest
  ): Promise<DocumentEntity> {
    return this.request<DocumentEntity>('POST', `/documents/${documentId}/commit`, request);
  }

  public async listDocuments(limit: number = 50, offset: number = 0): Promise<DocumentEntity[]> {
    return this.request<DocumentEntity[]>('GET', '/documents', undefined, { limit, offset });
  }

  public async getDocument(documentId: DocumentId): Promise<DocumentEntity> {
    return this.request<DocumentEntity>('GET', `/documents/${documentId}`);
  }

  public async deleteDocument(documentId: DocumentId): Promise<void> {
    return this.request<void>('DELETE', `/documents/${documentId}`);
  }

  public async getDocumentStructure(documentId: DocumentId): Promise<DocumentStructureTree> {
    return this.request<DocumentStructureTree>('GET', `/documents/${documentId}/structure`);
  }

  public async updateDocumentStructure(
    documentId: DocumentId,
    request: StructureUpdateRequest
  ): Promise<DocumentStructureTree> {
    return this.request<DocumentStructureTree>('PUT', `/documents/${documentId}/structure`, request);
  }

  public async updateExclusions(
    documentId: DocumentId,
    request: ExclusionUpdateRequest
  ): Promise<void> {
    return this.request<void>('PATCH', `/documents/${documentId}/exclusions`, request);
  }

  public async getSectionContent(
    documentId: DocumentId,
    sectionId: SectionId
  ): Promise<SectionContent> {
    return this.request<SectionContent>('GET', `/documents/${documentId}/sections/${sectionId}/content`);
  }

  public async getDocumentProgress(documentId: DocumentId): Promise<ReadingProgressEntity> {
    return this.request<ReadingProgressEntity>('GET', `/documents/${documentId}/progress`);
  }

  public async updateDocumentProgress(
    documentId: DocumentId,
    pointer: ReadingPositionPointer
  ): Promise<ReadingProgressEntity> {
    return this.request<ReadingProgressEntity>('PUT', `/documents/${documentId}/progress`, pointer);
  }

  // ==========================================================================
  // SESSIONS
  // ==========================================================================

  public async startSession(request: StartSessionRequest): Promise<TypingSessionEntity> {
    return this.request<TypingSessionEntity>('POST', '/sessions/start', request);
  }

  public async submitKeystrokes(
    sessionId: SessionId,
    request: SubmitKeystrokesRequest
  ): Promise<KeystrokeBatchResult> {
    return this.request<KeystrokeBatchResult>('POST', `/sessions/${sessionId}/keystrokes`, request);
  }

  public async setSessionState(
    sessionId: SessionId,
    request: SetSessionStateRequest
  ): Promise<TypingSessionEntity> {
    return this.request<TypingSessionEntity>('POST', `/sessions/${sessionId}/state`, request);
  }

  public async completeSession(sessionId: SessionId): Promise<TypingSessionEntity> {
    return this.request<TypingSessionEntity>('POST', `/sessions/${sessionId}/complete`);
  }

  public async abortSession(sessionId: SessionId): Promise<TypingSessionEntity> {
    return this.request<TypingSessionEntity>('POST', `/sessions/${sessionId}/abort`);
  }

  public async getActiveSession(): Promise<TypingSessionEntity | null> {
    return this.request<TypingSessionEntity | null>('GET', '/sessions/active');
  }

  // ==========================================================================
  // ANALYTICS & PRACTICE
  // ==========================================================================

  public async getAnalyticsOverview(): Promise<AnalyticsOverview> {
    return this.request<AnalyticsOverview>('GET', '/analytics/overview');
  }

  public async getAnalyticsTrends(days: number = 30): Promise<AnalyticsTrends> {
    return this.request<AnalyticsTrends>('GET', '/analytics/trends', undefined, { days });
  }

  public async getDocumentAnalytics(documentId: DocumentId): Promise<DocumentAnalytics> {
    return this.request<DocumentAnalytics>('GET', `/analytics/documents/${documentId}`);
  }

  public async getWeakKeys(limit: number = 10): Promise<WeakKeyAggregate[]> {
    return this.request<WeakKeyAggregate[]>('GET', '/analytics/weak-keys', undefined, { limit });
  }

  public async generateWeakKeyDrill(
    request: GenerateWeakKeyDrillRequest
  ): Promise<WeakKeyDrillPractice> {
    return this.request<WeakKeyDrillPractice>('POST', '/practice/drills/generate', request);
  }

  // ==========================================================================
  // SEARCH
  // ==========================================================================

  public async searchDocuments(request: SearchQuery): Promise<SearchResults> {
    return this.request<SearchResults>('POST', '/search', request);
  }

  // ==========================================================================
  // BOOKMARKS & NOTES
  // ==========================================================================

  public async listBookmarks(documentId?: DocumentId): Promise<BookmarkEntity[]> {
    return this.request<BookmarkEntity[]>('GET', '/bookmarks', undefined, { documentId });
  }

  public async createBookmark(request: CreateBookmarkRequest): Promise<BookmarkEntity> {
    return this.request<BookmarkEntity>('POST', '/bookmarks', request);
  }

  public async deleteBookmark(bookmarkId: BookmarkId): Promise<void> {
    return this.request<void>('DELETE', `/bookmarks/${bookmarkId}`);
  }

  public async listNotes(documentId?: DocumentId): Promise<NoteEntity[]> {
    return this.request<NoteEntity[]>('GET', '/notes', undefined, { documentId });
  }

  public async createNote(request: CreateNoteRequest): Promise<NoteEntity> {
    return this.request<NoteEntity>('POST', '/notes', request);
  }

  public async updateNote(noteId: NoteId, request: UpdateNoteRequest): Promise<NoteEntity> {
    return this.request<NoteEntity>('PUT', `/notes/${noteId}`, request);
  }

  public async deleteNote(noteId: NoteId): Promise<void> {
    return this.request<void>('DELETE', `/notes/${noteId}`);
  }

  // ==========================================================================
  // SETTINGS
  // ==========================================================================

  public async getSettings(): Promise<UserSettings> {
    return this.request<UserSettings>('GET', '/settings');
  }

  public async updateSettings(settings: UserSettings): Promise<UserSettings> {
    return this.request<UserSettings>('PUT', '/settings', settings);
  }

  // ==========================================================================
  // BACKUP & RESTORE
  // ==========================================================================

  public async exportBackup(request: ExportBackupRequest): Promise<BackupManifest> {
    return this.request<BackupManifest>('POST', '/backup/export', request);
  }

  public async validateBackup(request: BackupFileRequest): Promise<BackupValidationResult> {
    return this.request<BackupValidationResult>('POST', '/backup/validate', request);
  }

  public async restoreBackup(request: BackupFileRequest): Promise<BackupRestoreResult> {
    return this.request<BackupRestoreResult>('POST', '/backup/restore', request);
  }
}
