"""
TypeRead Search Service
Provides fast full-text search across documents and paragraphs.
"""

from __future__ import annotations

from src.contracts.types import SearchQuery, SearchResults
from src.storage.repositories.search_repo import SearchRepository


class SearchService:
    def __init__(self, search_repo: SearchRepository):
        self.search_repo = search_repo

    def search_documents(self, request: SearchQuery) -> SearchResults:
        return self.search_repo.search(request)
