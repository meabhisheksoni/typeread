/**
 * TypeRead Frontend State Stores & Flow Hooks
 * Handles loading, empty, and error states for all asynchronous data flows.
 */

import type {
  DocumentId,
  ChapterId,
  SectionId,
  ParagraphId,
  SessionId,
  DocumentEntity,
  DocumentStructureTree,
  IngestionPreview,
  StructureUpdateRequest,
  ReadingProgressEntity,
  ReadingPositionPointer,
  TypingSessionEntity,
  TypingMode,
  ErrorHandlingMode,
  KeystrokeInput,
  TypingMetrics,
  WeakKeyAggregate,
  WeakKeyDrillPractice,
  UserSettings,
  SearchResults,
  SearchQuery,
  BookmarkEntity,
  NoteEntity,
} from '../../.orchestrator/blackboard/contracts/types';

import { TypeReadApiClient, ApiClientError } from './apiClient';
import type { SectionContent, AnalyticsOverview, AnalyticsTrends, DocumentAnalytics } from './types';

export type AsyncStatus = 'idle' | 'loading' | 'success' | 'error';

export interface AsyncState<T> {
  status: AsyncStatus;
  data: T | null;
  error: string | null;
  isEmpty: boolean;
}

export function createInitialAsyncState<T>(initialData: T | null = null): AsyncState<T> {
  return {
    status: 'idle',
    data: initialData,
    error: null,
    isEmpty: initialData === null || (Array.isArray(initialData) && initialData.length === 0),
  };
}

/**
 * State store for Document Library
 */
export class LibraryStore {
  private state: AsyncState<DocumentEntity[]> = createInitialAsyncState<DocumentEntity[]>([]);
  private listeners: Array<(state: AsyncState<DocumentEntity[]>) => void> = [];

  constructor(private readonly api: TypeReadApiClient) {}

  public subscribe(listener: (state: AsyncState<DocumentEntity[]>) => void): () => void {
    this.listeners.push(listener);
    listener(this.state);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== listener);
    };
  }

  private notify(): void {
    for (const listener of this.listeners) {
      listener(this.state);
    }
  }

  public getState(): AsyncState<DocumentEntity[]> {
    return this.state;
  }

  public async fetchDocuments(): Promise<void> {
    this.state = { ...this.state, status: 'loading', error: null };
    this.notify();

    try {
      const docs = await this.api.listDocuments();
      this.state = {
        status: 'success',
        data: docs,
        error: null,
        isEmpty: docs.length === 0,
      };
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      this.state = {
        status: 'error',
        data: null,
        error: errorMsg,
        isEmpty: true,
      };
    }
    this.notify();
  }

  public async deleteDocument(docId: DocumentId): Promise<void> {
    await this.api.deleteDocument(docId);
    if (this.state.data) {
      const updated = this.state.data.filter((d) => d.id !== docId);
      this.state = {
        ...this.state,
        data: updated,
        isEmpty: updated.length === 0,
      };
      this.notify();
    }
  }
}

/**
 * State store for Active Typing Session
 */
export class TypingSessionStore {
  private sessionState: AsyncState<TypingSessionEntity> = createInitialAsyncState<TypingSessionEntity>();
  private activeSectionContent: AsyncState<SectionContent> = createInitialAsyncState<SectionContent>();
  private currentOffset: number = 0;
  private metrics: TypingMetrics | null = null;
  private listeners: Array<() => void> = [];

  constructor(private readonly api: TypeReadApiClient) {}

  public subscribe(listener: () => void): () => void {
    this.listeners.push(listener);
    listener();
    return () => {
      this.listeners = this.listeners.filter((l) => l !== listener);
    };
  }

  private notify(): void {
    for (const listener of this.listeners) {
      listener();
    }
  }

  public getSession(): AsyncState<TypingSessionEntity> {
    return this.sessionState;
  }

  public getSectionContent(): AsyncState<SectionContent> {
    return this.activeSectionContent;
  }

  public getCurrentOffset(): number {
    return this.currentOffset;
  }

  public getMetrics(): TypingMetrics | null {
    return this.metrics;
  }

  public async startSession(
    documentId: DocumentId,
    chapterId: ChapterId,
    sectionId: SectionId,
    mode: TypingMode = 'standard',
    errorHandling: ErrorHandlingMode = 'allow_with_backspace'
  ): Promise<void> {
    this.sessionState = { ...this.sessionState, status: 'loading', error: null };
    this.activeSectionContent = { ...this.activeSectionContent, status: 'loading', error: null };
    this.currentOffset = 0;
    this.notify();

    try {
      const [session, content] = await Promise.all([
        this.api.startSession({
          documentId,
          chapterId,
          sectionId,
          typingMode: mode,
          errorHandlingMode: errorHandling,
        }),
        this.api.getSectionContent(documentId, sectionId),
      ]);

      this.sessionState = {
        status: 'success',
        data: session,
        error: null,
        isEmpty: false,
      };
      this.activeSectionContent = {
        status: 'success',
        data: content,
        error: null,
        isEmpty: content.paragraphs.length === 0,
      };
      this.metrics = session.metrics;
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      this.sessionState = {
        status: 'error',
        data: null,
        error: errorMsg,
        isEmpty: true,
      };
      this.activeSectionContent = {
        status: 'error',
        data: null,
        error: errorMsg,
        isEmpty: true,
      };
    }
    this.notify();
  }

  public async submitKeystrokes(
    sessionId: SessionId,
    keystrokes: readonly KeystrokeInput[]
  ): Promise<boolean> {
    if (keystrokes.length === 0) return false;

    try {
      const result = await this.api.submitKeystrokes(sessionId, { keystrokes });
      this.currentOffset = result.currentPosition;
      this.metrics = result.currentMetrics;
      this.notify();
      return result.sectionCompleted;
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      this.sessionState = {
        ...this.sessionState,
        error: errorMsg,
      };
      this.notify();
      return false;
    }
  }

  public async pauseSession(sessionId: SessionId): Promise<void> {
    try {
      const updated = await this.api.setSessionState(sessionId, { state: 'paused' });
      this.sessionState = {
        ...this.sessionState,
        data: updated,
      };
      this.notify();
    } catch (err: unknown) {
      console.error('Failed to pause session', err);
    }
  }

  public async resumeSession(sessionId: SessionId): Promise<void> {
    try {
      const updated = await this.api.setSessionState(sessionId, { state: 'active' });
      this.sessionState = {
        ...this.sessionState,
        data: updated,
      };
      this.notify();
    } catch (err: unknown) {
      console.error('Failed to resume session', err);
    }
  }

  public async completeSession(sessionId: SessionId): Promise<void> {
    try {
      const updated = await this.api.completeSession(sessionId);
      this.sessionState = {
        ...this.sessionState,
        data: updated,
      };
      this.notify();
    } catch (err: unknown) {
      console.error('Failed to complete session', err);
    }
  }
}

/**
 * State store for Analytics
 */
export class AnalyticsStore {
  private overview: AsyncState<AnalyticsOverview> = createInitialAsyncState<AnalyticsOverview>();
  private weakKeys: AsyncState<WeakKeyAggregate[]> = createInitialAsyncState<WeakKeyAggregate[]>([]);
  private trends: AsyncState<AnalyticsTrends> = createInitialAsyncState<AnalyticsTrends>();
  private listeners: Array<() => void> = [];

  constructor(private readonly api: TypeReadApiClient) {}

  public subscribe(listener: () => void): () => void {
    this.listeners.push(listener);
    listener();
    return () => {
      this.listeners = this.listeners.filter((l) => l !== listener);
    };
  }

  private notify(): void {
    for (const listener of this.listeners) {
      listener();
    }
  }

  public getOverview(): AsyncState<AnalyticsOverview> {
    return this.overview;
  }

  public getWeakKeys(): AsyncState<WeakKeyAggregate[]> {
    return this.weakKeys;
  }

  public getTrends(): AsyncState<AnalyticsTrends> {
    return this.trends;
  }

  public async loadAll(days: number = 30): Promise<void> {
    this.overview = { ...this.overview, status: 'loading', error: null };
    this.weakKeys = { ...this.weakKeys, status: 'loading', error: null };
    this.trends = { ...this.trends, status: 'loading', error: null };
    this.notify();

    try {
      const [overviewData, weakKeysData, trendsData] = await Promise.all([
        this.api.getAnalyticsOverview(),
        this.api.getWeakKeys(10),
        this.api.getAnalyticsTrends(days),
      ]);

      this.overview = {
        status: 'success',
        data: overviewData,
        error: null,
        isEmpty: overviewData.totalSessions === 0,
      };
      this.weakKeys = {
        status: 'success',
        data: weakKeysData,
        error: null,
        isEmpty: weakKeysData.length === 0,
      };
      this.trends = {
        status: 'success',
        data: trendsData,
        error: null,
        isEmpty: trendsData.dailyActivity.length === 0,
      };
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      this.overview = { status: 'error', data: null, error: errorMsg, isEmpty: true };
      this.weakKeys = { status: 'error', data: null, error: errorMsg, isEmpty: true };
      this.trends = { status: 'error', data: null, error: errorMsg, isEmpty: true };
    }
    this.notify();
  }

  public async generateWeakKeyDrill(
    wordCount: number = 100,
    targetKeys?: readonly string[]
  ): Promise<WeakKeyDrillPractice> {
    return this.api.generateWeakKeyDrill({ wordCount, targetKeys });
  }
}
