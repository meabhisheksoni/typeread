"""
TypeRead Analytics & Practice Drill Service
Coordinates overall metric aggregations, trend queries, and weak-key drill generation.
"""

from __future__ import annotations
from typing import List, Optional

from src.contracts.types import (
    AnalyticsOverview,
    AnalyticsTrends,
    DocumentAnalytics,
    WeakKeyAggregate,
    WeakKeyDrillPractice,
    GenerateWeakKeyDrillRequest,
)
from src.core.practice.drills import DrillGenerator
from src.storage.repositories.analytics_repo import AnalyticsRepository
from src.storage.repositories.document_repo import DocumentRepository


class AnalyticsService:
    def __init__(self, analytics_repo: AnalyticsRepository, doc_repo: DocumentRepository):
        self.analytics_repo = analytics_repo
        self.doc_repo = doc_repo

    def get_analytics_overview(self, user_id: str = "default_user") -> AnalyticsOverview:
        return self.analytics_repo.get_analytics_overview(user_id=user_id)

    def get_analytics_trends(self, user_id: str = "default_user", days: int = 30) -> AnalyticsTrends:
        return self.analytics_repo.get_analytics_trends(user_id=user_id, days=days)

    def get_document_analytics(self, user_id: str, document_id: str) -> DocumentAnalytics:
        return self.analytics_repo.get_document_analytics(user_id=user_id, document_id=document_id)

    def get_weak_keys(self, user_id: str = "default_user", limit: int = 10) -> List[WeakKeyAggregate]:
        return self.analytics_repo.get_weak_keys(user_id=user_id, limit=limit)

    def generate_weak_key_drill(
        self,
        request: GenerateWeakKeyDrillRequest,
        user_id: str = "default_user",
    ) -> WeakKeyDrillPractice:
        target_keys = request.targetKeys
        if not target_keys:
            top_weak = self.analytics_repo.get_weak_keys(user_id=user_id, limit=5)
            target_keys = [w.character for w in top_weak] if top_weak else ["e", "t", "a", "o", "i"]

        doc_words = None
        if request.documentId:
            doc_words = self.doc_repo.get_all_words_for_document(request.documentId)

        return DrillGenerator.generate(
            target_keys=target_keys,
            target_bigrams=None,
            word_count=request.wordCount,
            document_words=doc_words,
        )
