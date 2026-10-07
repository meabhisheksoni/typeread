"""
TypeRead Analytics Repository
Calculates overall statistics, 30-day trends, document breakdowns, and weak key aggregates.
"""

from __future__ import annotations
import json
from datetime import datetime, date, timedelta, timezone
from typing import List, Optional, Dict, Any

from src.contracts.types import (
    AnalyticsOverview,
    AnalyticsTrends,
    TrendDayItem,
    DocumentAnalytics,
    ChapterBreakdownItem,
    WeakKeyAggregate,
    WeakBigramAggregate,
    SubstitutionCount,
    ErrorCode,
)
from src.core.errors import AppErrorException
from src.storage.db import Database


class AnalyticsRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_analytics_overview(self, user_id: str = "default_user") -> AnalyticsOverview:
        with self.db.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    COALESCE(AVG(net_wpm), 0.0) as avg_wpm,
                    COALESCE(MAX(net_wpm), 0.0) as best_wpm,
                    COALESCE(AVG(accuracy_pct), 100.0) as avg_accuracy,
                    COALESCE(SUM(active_seconds), 0.0) as total_active_sec,
                    COALESCE(SUM(total_characters), 0) as total_chars,
                    COALESCE(COUNT(*), 0) as session_count
                FROM typing_sessions
                WHERE user_id = ?;
                """,
                (user_id,),
            )
            agg = cur.fetchone()

            avg_wpm = round(agg["avg_wpm"], 2)
            best_wpm = round(agg["best_wpm"], 2)
            avg_acc = round(agg["avg_accuracy"], 2)
            total_active_sec = round(agg["total_active_sec"], 2)
            total_chars = agg["total_chars"]
            total_words = int(total_chars / 5)

            # Count completed chapters and books
            cur.execute(
                "SELECT COUNT(*) as comp_books FROM reading_progress WHERE user_id = ? AND is_completed = 1;",
                (user_id,),
            )
            comp_books = cur.fetchone()["comp_books"]

            # Completed chapters count
            cur.execute(
                """
                SELECT COUNT(DISTINCT chapter_id) as comp_chaps
                FROM typing_sessions
                WHERE user_id = ? AND completed = 1;
                """,
                (user_id,),
            )
            comp_chaps = cur.fetchone()["comp_chaps"]

            # Daily streaks
            cur.execute(
                """
                SELECT practice_date, qualified 
                FROM daily_streaks 
                WHERE user_id = ? AND qualified = 1
                ORDER BY practice_date DESC;
                """,
                (user_id,),
            )
            streak_rows = [r["practice_date"] for r in cur.fetchall()]

            current_streak, longest_streak = self._calculate_streaks(streak_rows)

            return AnalyticsOverview(
                averageWpm=avg_wpm,
                bestWpm=best_wpm,
                averageAccuracy=avg_acc,
                totalActiveTimeSeconds=total_active_sec,
                totalWordsTyped=total_words,
                totalCharactersTyped=total_chars,
                currentDailyStreakDays=current_streak,
                longestDailyStreakDays=longest_streak,
                completedChaptersCount=comp_chaps,
                completedBooksCount=comp_books,
            )

    def get_analytics_trends(self, user_id: str = "default_user", days: int = 30) -> AnalyticsTrends:
        items: List[TrendDayItem] = []
        today = date.today()

        with self.db.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    DATE(start_time) as p_date,
                    COALESCE(SUM(active_seconds), 0.0) as act_sec,
                    COALESCE(AVG(net_wpm), 0.0) as avg_wpm,
                    COALESCE(AVG(accuracy_pct), 100.0) as avg_acc,
                    COALESCE(SUM(total_characters) / 5, 0) as words
                FROM typing_sessions
                WHERE user_id = ? AND DATE(start_time) >= DATE('now', ?)
                GROUP BY DATE(start_time)
                ORDER BY p_date ASC;
                """,
                (user_id, f"-{days} days"),
            )
            rows_by_date = {r["p_date"]: r for r in cur.fetchall()}

            for i in range(days - 1, -1, -1):
                d_str = (today - timedelta(days=i)).isoformat()
                if d_str in rows_by_date:
                    r = rows_by_date[d_str]
                    items.append(
                        TrendDayItem(
                            date=d_str,
                            activeSeconds=round(r["act_sec"], 2),
                            averageWpm=round(r["avg_wpm"], 2),
                            accuracyPct=round(r["avg_acc"], 2),
                            wordsTyped=int(r["words"]),
                        )
                    )
                else:
                    items.append(
                        TrendDayItem(
                            date=d_str,
                            activeSeconds=0.0,
                            averageWpm=0.0,
                            accuracyPct=100.0,
                            wordsTyped=0,
                        )
                    )

        return AnalyticsTrends(days=items)

    def get_document_analytics(self, user_id: str, document_id: str) -> DocumentAnalytics:
        with self.db.cursor() as cur:
            cur.execute("SELECT title, character_count FROM documents WHERE id = ?;", (document_id,))
            doc = cur.fetchone()
            if not doc:
                raise AppErrorException.not_found(
                    code=ErrorCode.DOCUMENT_NOT_FOUND,
                    message=f"Document {document_id} not found",
                    field="documentId",
                )

            cur.execute(
                """
                SELECT 
                    COALESCE(SUM(active_seconds), 0.0) as act_sec,
                    COALESCE(SUM(total_characters) / 5, 0) as words,
                    COALESCE(AVG(net_wpm), 0.0) as avg_wpm,
                    COALESCE(AVG(accuracy_pct), 100.0) as avg_acc,
                    COUNT(*) as sessions_cnt
                FROM typing_sessions
                WHERE user_id = ? AND document_id = ?;
                """,
                (user_id, document_id),
            )
            overall = cur.fetchone()

            # Reading progress
            cur.execute(
                "SELECT completion_percentage FROM reading_progress WHERE user_id = ? AND document_id = ?;",
                (user_id, document_id),
            )
            prog = cur.fetchone()
            comp_pct = prog["completion_percentage"] if prog else 0.0

            # Chapter breakdown
            cur.execute(
                """
                SELECT 
                    c.id as chapter_id, c.title,
                    COALESCE(AVG(ts.net_wpm), 0.0) as avg_wpm,
                    COALESCE(AVG(ts.accuracy_pct), 100.0) as avg_acc,
                    COALESCE(SUM(ts.active_seconds), 0.0) as time_typed
                FROM chapters c
                LEFT JOIN typing_sessions ts ON ts.chapter_id = c.id AND ts.user_id = ?
                WHERE c.document_id = ?
                GROUP BY c.id
                ORDER BY c.order_index ASC;
                """,
                (user_id, document_id),
            )

            breakdown: List[ChapterBreakdownItem] = []
            for c in cur.fetchall():
                breakdown.append(
                    ChapterBreakdownItem(
                        chapterId=c["chapter_id"],
                        title=c["title"],
                        completionPercentage=comp_pct,
                        averageWpm=round(c["avg_wpm"], 2),
                        accuracyPct=round(c["avg_acc"], 2),
                        timeTypedSeconds=round(c["time_typed"], 2),
                    )
                )

            return DocumentAnalytics(
                documentId=document_id,
                completionPercentage=round(comp_pct, 2),
                timeTypedSeconds=round(overall["act_sec"], 2),
                wordsTyped=int(overall["words"]),
                averageWpm=round(overall["avg_wpm"], 2),
                accuracyPct=round(overall["avg_acc"], 2),
                sessionsCount=overall["sessions_cnt"],
                chapterBreakdown=breakdown,
            )

    def get_weak_keys(self, user_id: str = "default_user", limit: int = 10) -> List[WeakKeyAggregate]:
        aggregates: List[WeakKeyAggregate] = []
        with self.db.cursor() as cur:
            cur.execute(
                """
                SELECT character, error_count, total_occurrences, common_substitutions_json
                FROM weak_key_aggregates
                WHERE user_id = ?
                ORDER BY error_count DESC
                LIMIT ?;
                """,
                (user_id, limit),
            )
            for r in cur.fetchall():
                subs_data = json.loads(r["common_substitutions_json"])
                subs = [SubstitutionCount(substituted_for=k, count=v) for k, v in subs_data.items()]
                total = max(1, r["total_occurrences"])
                err_rate = round((r["error_count"] / float(total)) * 100.0, 2)
                aggregates.append(
                    WeakKeyAggregate(
                        character=r["character"],
                        error_count=r["error_count"],
                        total_occurrences=total,
                        error_rate_pct=err_rate,
                        common_substitutions=subs,
                    )
                )
        return aggregates

    def update_weak_keys_and_bigrams(
        self,
        user_id: str,
        weak_keys: List[WeakKeyAggregate],
        weak_bigrams: List[WeakBigramAggregate],
    ) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.db.transaction() as cur:
            for wk in weak_keys:
                subs_dict = {s.substituted_for: s.count for s in wk.common_substitutions}
                cur.execute(
                    """
                    INSERT INTO weak_key_aggregates (user_id, character, error_count, total_occurrences, common_substitutions_json, last_error_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, character) DO UPDATE SET
                        error_count = error_count + excluded.error_count,
                        total_occurrences = total_occurrences + excluded.total_occurrences,
                        common_substitutions_json = excluded.common_substitutions_json,
                        last_error_at = excluded.last_error_at;
                    """,
                    (user_id, wk.character, wk.error_count, wk.total_occurrences, json.dumps(subs_dict), now_iso),
                )

            for bg in weak_bigrams:
                cur.execute(
                    """
                    INSERT INTO weak_bigram_aggregates (user_id, bigram, error_count, total_occurrences, last_error_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, bigram) DO UPDATE SET
                        error_count = error_count + excluded.error_count,
                        total_occurrences = total_occurrences + excluded.total_occurrences,
                        last_error_at = excluded.last_error_at;
                    """,
                    (user_id, bg.bigram, bg.error_count, bg.total_occurrences, now_iso),
                )

    def record_daily_streak(self, user_id: str, active_seconds: float, chars_typed: int) -> None:
        today_str = date.today().isoformat()
        with self.db.transaction() as cur:
            cur.execute(
                """
                INSERT INTO daily_streaks (user_id, practice_date, active_seconds, characters_typed, qualified)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, practice_date) DO UPDATE SET
                    active_seconds = active_seconds + excluded.active_seconds,
                    characters_typed = characters_typed + excluded.characters_typed,
                    qualified = CASE WHEN (active_seconds + excluded.active_seconds >= 60.0) THEN 1 ELSE 0 END;
                """,
                (user_id, today_str, active_seconds, chars_typed, 1 if active_seconds >= 60.0 else 0),
            )

    @staticmethod
    def _calculate_streaks(qualified_dates: List[str]) -> Tuple[int, int]:
        if not qualified_dates:
            return 0, 0

        date_set = {datetime.strptime(d, "%Y-%m-%d").date() for d in qualified_dates}
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Current streak
        current_streak = 0
        curr_ptr = today if today in date_set else (yesterday if yesterday in date_set else None)

        if curr_ptr:
            while curr_ptr in date_set:
                current_streak += 1
                curr_ptr -= timedelta(days=1)

        # Longest streak
        sorted_dates = sorted(date_set)
        longest = 0
        current_run = 0
        prev_d: Optional[date] = None

        for d in sorted_dates:
            if prev_d and d == prev_d + timedelta(days=1):
                current_run += 1
            else:
                current_run = 1
            longest = max(longest, current_run)
            prev_d = d

        return current_streak, max(current_streak, longest)
