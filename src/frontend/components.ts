/**
 * TypeRead UI Component Contracts, Layouts & State Renderers
 * Implements empty, loading, and error states for all asynchronous views.
 */

import type {
  DocumentEntity,
  TypingMetrics,
  WeakKeyAggregate,
  ThemeId,
  CaretStyle,
  TypingMode,
  ErrorHandlingMode,
} from '../../.orchestrator/blackboard/contracts/types';
import type { AsyncState } from './state';
import type { AnalyticsOverview } from './types';

/**
 * Standard View Identification
 */
export type ActiveView = 'home' | 'library' | 'reader' | 'stats' | 'settings';

/**
 * Visual Display Configuration
 */
export interface UiThemeConfig {
  theme: ThemeId;
  fontFamily: string;
  fontSizePt: number;
  lineHeightEm: number;
  contentWidthPx: number;
  caretStyle: CaretStyle;
  focusMode: boolean;
  zenMode: boolean;
}

/**
 * Reader & Typing Panel Layout Preferences
 */
export type ReaderLayout = 'split_vertical' | 'split_horizontal' | 'typing_only';

/**
 * Presentation View Model for Home Screen
 */
export interface HomeScreenViewModel {
  greeting: string;
  continueCard: {
    documentId: string;
    documentTitle: string;
    chapterTitle: string;
    completionPct: number;
    wpm: number;
    accuracyPct: number;
  } | null;
  recentDocuments: DocumentEntity[];
  overallStats: AnalyticsOverview | null;
}

/**
 * Presentation View Model for Dual Reader Display
 */
export interface DualReaderViewModel {
  sourceText: string;
  displayText: string;
  typingText: string;
  currentOffset: number;
  activeCharacter: string;
  metrics: TypingMetrics;
  isPaused: boolean;
  isCompleted: boolean;
  errorCount: number;
}

/**
 * Formatted View State Handler for Components
 */
export class ViewStateHandler {
  /**
   * Generates standard Empty State view according to PRD Section 125
   */
  public static renderLibraryEmptyState(): {
    title: string;
    description: string;
    actionLabel: string;
  } {
    return {
      title: 'Your library is empty.',
      description: 'Import a book, study PDF, or document to begin your first read-and-type session.',
      actionLabel: 'Add Document',
    };
  }

  /**
   * Generates standard Ingestion Processing state according to PRD Section 126
   */
  public static renderProcessingState(step: 'extracting' | 'structure' | 'material'): {
    title: string;
    stages: Array<{ name: string; completed: boolean; current: boolean }>;
  } {
    return {
      title: 'Preparing your document...',
      stages: [
        { name: 'Extracting text', completed: step !== 'extracting', current: step === 'extracting' },
        { name: 'Building structure', completed: step === 'material', current: step === 'structure' },
        { name: 'Preparing typing material', completed: false, current: step === 'material' },
      ],
    };
  }

  /**
   * Generates standard Completion State according to PRD Section 127
   */
  public static renderCompletionState(
    docTitle: string,
    avgWpm: number,
    accuracyPct: number,
    totalMinutes: number,
    wordsTyped: number
  ): {
    header: string;
    title: string;
    completion: string;
    metrics: Array<{ label: string; value: string }>;
    actions: string[];
  } {
    const hours = Math.floor(totalMinutes / 60);
    const mins = totalMinutes % 60;
    const timeFormatted = hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;

    return {
      header: 'Book Complete',
      title: docTitle,
      completion: '100% complete',
      metrics: [
        { label: 'Average WPM', value: String(Math.round(avgWpm)) },
        { label: 'Accuracy', value: `${accuracyPct.toFixed(1)}%` },
        { label: 'Practice Time', value: timeFormatted },
        { label: 'Words Typed', value: wordsTyped.toLocaleString() },
      ],
      actions: ['View Statistics', 'Start Revision', 'Return to Library'],
    };
  }

  /**
   * Formats crash recovery prompt according to PRD Section 70
   */
  public static renderCrashRecoveryPrompt(
    documentTitle: string,
    chapterTitle: string,
    progressPct: number
  ): {
    title: string;
    prompt: string;
    confirmLabel: string;
    cancelLabel: string;
  } {
    return {
      title: 'Resume Unfinished Session',
      prompt: `Unfinished practice session found for ${documentTitle}, ${chapterTitle} (${progressPct.toFixed(0)}%). Resume practice?`,
      confirmLabel: 'Resume Session',
      cancelLabel: 'Start Fresh',
    };
  }
}
