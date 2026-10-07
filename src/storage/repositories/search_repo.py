"""
TypeRead Full-Text Search (FTS5) Repository
Performs fast offline search across paragraphs, chapters, and sections with snippet extraction.
"""

from __future__ import annotations
import re
from typing import List, Optional

from src.contracts.types import (
    SearchQuery,
    SearchResults,
    SearchResultItem,
    DocumentId,
    ChapterId,
    SectionId,
    ParagraphId,
)
from src.storage.db import Database


class SearchRepository:
    def __init__(self, db: Database):
        self.db = db

    def search(self, query_params: SearchQuery) -> SearchResults:
        raw_q = query_params.query.strip()
        if not raw_q:
            return SearchResults(query=query_params.query, total_matches=0, items=[])

        # Sanitize query for FTS5 (escape special chars, match tokens)
        sanitized_tokens = re.findall(r"\w+", raw_q)
        if not sanitized_tokens:
            return SearchResults(query=query_params.query, total_matches=0, items=[])

        fts_expression = " ".join(f'"{t}"*' for t in sanitized_tokens)

        doc_filter_sql = "AND fts.document_id = ?" if query_params.document_id else ""
        params: List[object] = [fts_expression]
        if query_params.document_id:
            params.append(query_params.document_id)

        items: List[SearchResultItem] = []
        total_matches = 0

        with self.db.cursor() as cur:
            # Count total
            count_sql = f"""
                SELECT COUNT(*) as cnt
                FROM document_fts fts
                WHERE document_fts MATCH ? {doc_filter_sql};
            """
            cur.execute(count_sql, params)
            total_matches = cur.fetchone()["cnt"]

            # Query results with rank and snippet
            search_sql = f"""
                SELECT 
                    fts.document_id,
                    fts.document_title,
                    fts.chapter_id,
                    fts.chapter_title,
                    fts.section_id,
                    fts.section_title,
                    fts.paragraph_id,
                    p.source_page,
                    snippet(document_fts, 7, '<b>', '</b>', '...', 15) as snippet_text,
                    rank as rank_score
                FROM document_fts fts
                JOIN paragraphs p ON p.id = fts.paragraph_id
                WHERE document_fts MATCH ? {doc_filter_sql}
                ORDER BY rank ASC
                LIMIT ? OFFSET ?;
            """
            query_args = list(params) + [query_params.limit, query_params.offset]
            cur.execute(search_sql, query_args)

            for r in cur.fetchall():
                items.append(
                    SearchResultItem(
                        document_id=DocumentId(r["document_id"]),
                        document_title=r["document_title"],
                        chapter_id=ChapterId(r["chapter_id"]),
                        chapter_title=r["chapter_title"],
                        section_id=SectionId(r["section_id"]),
                        section_title=r["section_title"],
                        paragraph_id=ParagraphId(r["paragraph_id"]),
                        page_number=r["source_page"],
                        matched_snippet=r["snippet_text"],
                        character_offset=0,
                        rank_score=round(abs(float(r["rank_score"])), 4),
                    )
                )

        return SearchResults(
            query=query_params.query,
            total_matches=total_matches,
            items=items,
        )
