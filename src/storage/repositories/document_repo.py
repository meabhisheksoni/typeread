"""
TypeRead Document Repository
Full persistence for documents, chapters, sections, paragraphs, and structure trees.
"""

from __future__ import annotations
import json
from typing import List, Optional, Tuple, Dict, Any

from src.contracts.types import (
    DocumentEntity,
    ChapterEntity,
    SectionEntity,
    ParagraphEntity,
    DocumentLibraryCard,
    DocumentStructureTree,
    TreeChapterNode,
    TreeSectionNode,
    SectionContentResponse,
    SectionParagraphItem,
    StructureUpdateRequest,
    DocumentFormat,
    IngestionStatus,
    StructuralLevel,
    ProcessingProfile,
    CharacterOffsetMap,
    TextRepresentations,
    StructuralNodeConfidence,
    StructuralNodeSignals,
    ErrorCode,
)
from src.core.errors import AppErrorException
from src.storage.db import Database


class DocumentRepository:
    def __init__(self, db: Database):
        self.db = db

    def save_document(
        self,
        doc: DocumentEntity,
        chapters: List[ChapterEntity],
        sections: List[SectionEntity],
        paragraphs: List[ParagraphEntity],
    ) -> None:
        with self.db.transaction() as cur:
            # Check for existing document with same user_id and file_hash
            cur.execute(
                "SELECT id FROM documents WHERE user_id = ? AND file_hash = ? AND id != ?;",
                (doc.user_id, doc.file_hash, doc.id),
            )
            if cur.fetchone():
                raise AppErrorException.conflict(
                    code=ErrorCode.DOCUMENT_ALREADY_EXISTS,
                    message=f"Document with identical content hash already exists: {doc.file_hash}",
                    field="fileHash",
                )

            # Insert document
            profile_json = json.dumps(doc.processing_profile.__dict__)
            cur.execute(
                """
                INSERT OR REPLACE INTO documents (
                    id, user_id, title, author, file_name, file_path, file_hash,
                    source_format, word_count, character_count, status,
                    processing_profile_json, error_message, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    doc.id,
                    doc.user_id,
                    doc.title,
                    doc.author,
                    doc.file_name,
                    doc.file_path,
                    doc.file_hash,
                    doc.source_format.value,
                    doc.word_count,
                    doc.character_count,
                    doc.status.value,
                    profile_json,
                    doc.error_message,
                    doc.created_at,
                    doc.updated_at,
                ),
            )

            # Insert chapters
            for chap in chapters:
                signals_json = json.dumps(chap.confidence.signals.__dict__)
                cur.execute(
                    """
                    INSERT OR REPLACE INTO chapters (
                        id, document_id, parent_id, title, level, order_index,
                        page_start, page_end, text_start_char, text_end_char,
                        confidence_score, confidence_signals_json, included_in_practice, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        chap.id,
                        chap.document_id,
                        chap.parent_id,
                        chap.title,
                        chap.level.value,
                        chap.order_index,
                        chap.page_start,
                        chap.page_end,
                        chap.text_start_char,
                        chap.text_end_char,
                        chap.confidence.score,
                        signals_json,
                        1 if chap.included_in_practice else 0,
                        chap.created_at,
                    ),
                )

            # Insert sections
            for sec in sections:
                cur.execute(
                    """
                    INSERT OR REPLACE INTO sections (
                        id, document_id, chapter_id, title, order_index,
                        page_start, page_end, text_start_char, text_end_char,
                        word_count, character_count, included_in_practice, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        sec.id,
                        sec.document_id,
                        sec.chapter_id,
                        sec.title,
                        sec.order_index,
                        sec.page_start,
                        sec.page_end,
                        sec.text_start_char,
                        sec.text_end_char,
                        sec.word_count,
                        sec.character_count,
                        1 if sec.included_in_practice else 0,
                        sec.created_at,
                    ),
                )

            # Insert paragraphs (and FTS triggers will index them)
            for p in paragraphs:
                offset_json = json.dumps({
                    "typing_to_display_indices": list(p.representations.offset_map.typing_to_display_indices),
                    "display_to_source_indices": list(p.representations.offset_map.display_to_source_indices),
                })
                cur.execute(
                    """
                    INSERT OR REPLACE INTO paragraphs (
                        id, document_id, chapter_id, section_id, order_index,
                        source_text, normalized_text, display_text, typing_text,
                        offset_map_json, source_page, source_position_y, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        p.id,
                        p.document_id,
                        p.chapter_id,
                        p.section_id,
                        p.order_index,
                        p.representations.source_text,
                        p.representations.normalized_text,
                        p.representations.display_text,
                        p.representations.typing_text,
                        offset_json,
                        p.source_page,
                        p.source_position_y,
                        p.created_at,
                    ),
                )

            # Initialize initial reading progress pointer at first paragraph
            if chapters and sections and paragraphs:
                first_chap = chapters[0]
                first_sec = [s for s in sections if s.chapter_id == first_chap.id][0]
                first_para = [p for p in paragraphs if p.section_id == first_sec.id][0]
                cur.execute(
                    """
                    INSERT OR IGNORE INTO reading_progress (
                        id, user_id, document_id, chapter_id, section_id, paragraph_id,
                        character_offset, completion_percentage, is_completed, last_practiced_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 0, 0.0, 0, ?, ?);
                    """,
                    (
                        f"prog_{doc.id}",
                        doc.user_id,
                        doc.id,
                        first_chap.id,
                        first_sec.id,
                        first_para.id,
                        doc.created_at,
                        doc.created_at,
                    ),
                )

    def get_document_by_id(self, doc_id: str) -> Optional[DocumentEntity]:
        with self.db.cursor() as cur:
            cur.execute("SELECT * FROM documents WHERE id = ?;", (doc_id,))
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_document_entity(row)

    def get_document_by_hash(self, file_hash: str, user_id: str) -> Optional[DocumentEntity]:
        with self.db.cursor() as cur:
            cur.execute("SELECT * FROM documents WHERE file_hash = ? AND user_id = ?;", (file_hash, user_id))
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_document_entity(row)

    def list_documents(self, user_id: str = "default_user", limit: int = 50, offset: int = 0) -> List[DocumentLibraryCard]:
        cards: List[DocumentLibraryCard] = []
        with self.db.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    d.id, d.title, d.author, d.source_format, d.word_count,
                    COALESCE(rp.completion_percentage, 0.0) as completion_pct,
                    COALESCE(c.title, 'Beginning') as current_chap_title,
                    COALESCE(AVG(ts.net_wpm), 0.0) as avg_wpm,
                    COALESCE(AVG(ts.accuracy_pct), 100.0) as avg_accuracy,
                    rp.last_practiced_at
                FROM documents d
                LEFT JOIN reading_progress rp ON rp.document_id = d.id AND rp.user_id = d.user_id
                LEFT JOIN chapters c ON c.id = rp.chapter_id
                LEFT JOIN typing_sessions ts ON ts.document_id = d.id
                WHERE d.user_id = ? AND d.status = 'committed'
                GROUP BY d.id
                ORDER BY COALESCE(rp.last_practiced_at, d.created_at) DESC
                LIMIT ? OFFSET ?;
                """,
                (user_id, limit, offset),
            )
            for r in cur.fetchall():
                cards.append(
                    DocumentLibraryCard(
                        id=r["id"],
                        title=r["title"],
                        author=r["author"],
                        sourceFormat=DocumentFormat(r["source_format"]),
                        completionPercentage=round(r["completion_pct"], 2),
                        currentChapterTitle=r["current_chap_title"],
                        averageWpm=round(r["avg_wpm"], 2),
                        averageAccuracy=round(r["avg_accuracy"], 2),
                        totalWords=r["word_count"],
                        lastPracticedAt=r["last_practiced_at"],
                    )
                )
        return cards

    def delete_document(self, doc_id: str) -> bool:
        with self.db.transaction() as cur:
            cur.execute("DELETE FROM documents WHERE id = ?;", (doc_id,))
            return cur.rowcount > 0

    def get_document_structure(self, doc_id: str) -> Optional[DocumentStructureTree]:
        doc = self.get_document_by_id(doc_id)
        if not doc:
            return None

        with self.db.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM chapters 
                WHERE document_id = ? 
                ORDER BY order_index ASC;
                """,
                (doc_id,),
            )
            chapter_rows = cur.fetchall()

            cur.execute(
                """
                SELECT * FROM sections 
                WHERE document_id = ? 
                ORDER BY chapter_id, order_index ASC;
                """,
                (doc_id,),
            )
            section_rows = cur.fetchall()

            sections_by_chap: Dict[str, List[TreeSectionNode]] = {}
            for s in section_rows:
                node = TreeSectionNode(
                    id=s["id"],
                    title=s["title"],
                    orderIndex=s["order_index"],
                    pageStart=s["page_start"],
                    pageEnd=s["page_end"],
                    wordCount=s["word_count"],
                    characterCount=s["character_count"],
                    includedInPractice=bool(s["included_in_practice"]),
                )
                sections_by_chap.setdefault(s["chapter_id"], []).append(node)

            chapters_tree: List[TreeChapterNode] = []
            for c in chapter_rows:
                c_id = c["id"]
                chap_node = TreeChapterNode(
                    id=c_id,
                    title=c["title"],
                    level=StructuralLevel(c["level"]),
                    orderIndex=c["order_index"],
                    pageStart=c["page_start"],
                    pageEnd=c["page_end"],
                    includedInPractice=bool(c["included_in_practice"]),
                    sections=sections_by_chap.get(c_id, []),
                )
                chapters_tree.append(chap_node)

            return DocumentStructureTree(
                document=doc,
                chapters=chapters_tree,
            )

    def update_document_structure(self, doc_id: str, request: StructureUpdateRequest) -> DocumentStructureTree:
        doc = self.get_document_by_id(doc_id)
        if not doc:
            raise AppErrorException.not_found(
                code=ErrorCode.DOCUMENT_NOT_FOUND,
                message=f"Document not found: {doc_id}",
                field="documentId",
            )

        with self.db.transaction() as cur:
            if request.title or request.author:
                cur.execute(
                    """
                    UPDATE documents 
                    SET title = COALESCE(?, title), author = COALESCE(?, author)
                    WHERE id = ?;
                    """,
                    (request.title, request.author, doc_id),
                )

            for chap in request.chapters:
                cur.execute(
                    """
                    UPDATE chapters 
                    SET title = ?, order_index = ?, included_in_practice = ?
                    WHERE id = ? AND document_id = ?;
                    """,
                    (chap.title, chap.order_index, 1 if chap.included_in_practice else 0, chap.id, doc_id),
                )
                for sec in chap.sections:
                    cur.execute(
                        """
                        UPDATE sections 
                        SET title = ?, order_index = ?, included_in_practice = ?
                        WHERE id = ? AND chapter_id = ? AND document_id = ?;
                        """,
                        (sec.title, sec.order_index, 1 if sec.included_in_practice else 0, sec.id, chap.id, doc_id),
                    )

        tree = self.get_document_structure(doc_id)
        if not tree:
            raise AppErrorException.server_error(ErrorCode.DATABASE_ERROR, "Failed to load updated structure")
        return tree

    def update_exclusions(self, doc_id: str, target_type: str, target_id: str, included: bool) -> bool:
        doc = self.get_document_by_id(doc_id)
        if not doc:
            raise AppErrorException.not_found(
                code=ErrorCode.DOCUMENT_NOT_FOUND,
                message=f"Document not found: {doc_id}",
                field="documentId",
            )

        with self.db.transaction() as cur:
            flag = 1 if included else 0
            if target_type == "chapter":
                cur.execute(
                    "UPDATE chapters SET included_in_practice = ? WHERE id = ? AND document_id = ?;",
                    (flag, target_id, doc_id),
                )
                cur.execute(
                    "UPDATE sections SET included_in_practice = ? WHERE chapter_id = ? AND document_id = ?;",
                    (flag, target_id, doc_id),
                )
                return cur.rowcount > 0
            elif target_type == "section":
                cur.execute(
                    "UPDATE sections SET included_in_practice = ? WHERE id = ? AND document_id = ?;",
                    (flag, target_id, doc_id),
                )
                return cur.rowcount > 0
            else:
                raise AppErrorException.bad_request(
                    code=ErrorCode.UNSUPPORTED_FORMAT,
                    message=f"Invalid exclusion targetType: {target_type}",
                )

    def get_section_content(self, doc_id: str, section_id: str) -> Optional[SectionContentResponse]:
        with self.db.cursor() as cur:
            cur.execute(
                "SELECT title FROM sections WHERE id = ? AND document_id = ?;",
                (section_id, doc_id),
            )
            sec_row = cur.fetchone()
            if not sec_row:
                return None

            cur.execute(
                """
                SELECT id, order_index, source_text, display_text, typing_text, offset_map_json
                FROM paragraphs 
                WHERE section_id = ? AND document_id = ?
                ORDER BY order_index ASC;
                """,
                (section_id, doc_id),
            )
            para_rows = cur.fetchall()

            paragraphs: List[SectionParagraphItem] = []
            for p in para_rows:
                offset_data = json.loads(p["offset_map_json"])
                paragraphs.append(
                    SectionParagraphItem(
                        id=p["id"],
                        orderIndex=p["order_index"],
                        sourceText=p["source_text"],
                        displayText=p["display_text"],
                        typingText=p["typing_text"],
                        typingToDisplayIndices=offset_data.get("typing_to_display_indices", []),
                    )
                )

            return SectionContentResponse(
                sectionId=section_id,
                title=sec_row["title"],
                paragraphs=paragraphs,
            )

    def get_all_words_for_document(self, doc_id: str) -> List[str]:
        words: List[str] = []
        with self.db.cursor() as cur:
            cur.execute("SELECT display_text FROM paragraphs WHERE document_id = ?;", (doc_id,))
            for r in cur.fetchall():
                words.extend(r["display_text"].split())
        return list(set(words))

    @staticmethod
    def _row_to_document_entity(row: Any) -> DocumentEntity:
        profile_dict = json.loads(row["processing_profile_json"])
        return DocumentEntity(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            author=row["author"],
            file_name=row["file_name"],
            file_path=row["file_path"],
            file_hash=row["file_hash"],
            source_format=DocumentFormat(row["source_format"]),
            word_count=row["word_count"],
            character_count=row["character_count"],
            status=IngestionStatus(row["status"]),
            processing_profile=ProcessingProfile.from_dict(profile_dict),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            error_message=row["error_message"],
        )
