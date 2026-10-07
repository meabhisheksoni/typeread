"""
TypeRead Document Service
Coordinates file ingestion, structure previews, commits, exclusions, and reading progression.
Directly implements operations from api.json.
"""

from __future__ import annotations
import os
from typing import List, Optional, Dict, Tuple

from src.contracts.types import (
    DocumentEntity,
    DocumentLibraryCard,
    DocumentStructureTree,
    SectionContentResponse,
    ReadingProgressEntity,
    ReadingPositionPointer,
    ImportDocumentRequest,
    StructureUpdateRequest,
    ExclusionUpdateRequest,
    IngestionPreview,
    IngestionStatus,
    ErrorCode,
)
from src.core.errors import AppErrorException
from src.core.document.pipeline import IngestionPipeline
from src.storage.filesystem import FileSystemManager
from src.storage.repositories.document_repo import DocumentRepository
from src.storage.repositories.progress_repo import ProgressRepository


class DocumentService:
    def __init__(
        self,
        doc_repo: DocumentRepository,
        progress_repo: ProgressRepository,
        fs: FileSystemManager,
    ):
        self.doc_repo = doc_repo
        self.progress_repo = progress_repo
        self.fs = fs
        # Cache of uncommitted staged documents: doc_id -> (preview, doc_entity, chapters, sections, paragraphs)
        self._staged_imports: Dict[str, Tuple] = {}

    def import_document(self, req: ImportDocumentRequest, user_id: str = "default_user") -> IngestionPreview:
        # Check duplicate hash before parsing
        if os.path.exists(req.filePath):
            file_hash = IngestionPipeline.calculate_file_hash(req.filePath)
            existing = self.doc_repo.get_document_by_hash(file_hash, user_id)
            if existing and existing.status == IngestionStatus.COMMITTED:
                raise AppErrorException.conflict(
                    code=ErrorCode.DOCUMENT_ALREADY_EXISTS,
                    message=f"Document with identical content hash already exists: {file_hash}",
                    field="filePath",
                    suggested_action="Open the existing document in your library or rename/modify before import.",
                )

        pipeline = IngestionPipeline(profile=req.profileOverride)
        preview, doc_entity, chapters, sections, paragraphs = pipeline.process(
            file_path=req.filePath,
            user_id=user_id,
            profile_override=req.profileOverride,
        )

        # Stage for commit
        self._staged_imports[str(doc_entity.id)] = (preview, doc_entity, chapters, sections, paragraphs)
        return preview

    def commit_document(
        self,
        document_id: str,
        request: StructureUpdateRequest,
        user_id: str = "default_user",
    ) -> DocumentEntity:
        if document_id not in self._staged_imports:
            raise AppErrorException.not_found(
                code=ErrorCode.DOCUMENT_NOT_FOUND,
                message=f"No staged import found for document ID: {document_id}",
                field="documentId",
                suggested_action="Please re-run importDocument before committing.",
            )

        preview, doc_entity, chapters, sections, paragraphs = self._staged_imports.pop(document_id)

        # Store immutable source file in TypeRead filesystem store
        persisted_source_path = self.fs.store_document_source(str(doc_entity.id), doc_entity.file_path)

        # Apply user edits from StructureUpdateRequest if provided
        final_title = request.title or doc_entity.title
        final_author = request.author or doc_entity.author

        # If chapter/section edits were supplied, apply them to entity lists
        if request.chapters:
            chap_updates_by_id = {c.id: c for c in request.chapters}
            sec_updates_by_id = {}
            for c in request.chapters:
                for s in c.sections:
                    sec_updates_by_id[s.id] = s

            updated_chapters = []
            for c in chapters:
                if str(c.id) in chap_updates_by_id:
                    u = chap_updates_by_id[str(c.id)]
                    updated_chapters.append(
                        type(c)(
                            id=c.id,
                            document_id=c.document_id,
                            parent_id=c.parent_id,
                            title=u.title,
                            level=c.level,
                            order_index=u.order_index,
                            page_start=c.page_start,
                            page_end=c.page_end,
                            text_start_char=c.text_start_char,
                            text_end_char=c.text_end_char,
                            confidence=c.confidence,
                            included_in_practice=u.included_in_practice,
                            created_at=c.created_at,
                        )
                    )
                else:
                    updated_chapters.append(c)
            chapters = updated_chapters

            updated_sections = []
            for s in sections:
                if str(s.id) in sec_updates_by_id:
                    u = sec_updates_by_id[str(s.id)]
                    updated_sections.append(
                        type(s)(
                            id=s.id,
                            document_id=s.document_id,
                            chapter_id=s.chapter_id,
                            title=u.title,
                            order_index=u.order_index,
                            page_start=s.page_start,
                            page_end=s.page_end,
                            text_start_char=s.text_start_char,
                            text_end_char=s.text_end_char,
                            word_count=s.word_count,
                            character_count=s.character_count,
                            included_in_practice=u.included_in_practice,
                            created_at=s.created_at,
                        )
                    )
                else:
                    updated_sections.append(s)
            sections = updated_sections

        # Final committed entity
        committed_entity = DocumentEntity(
            id=doc_entity.id,
            user_id=doc_entity.user_id,
            title=final_title,
            author=final_author,
            file_name=doc_entity.file_name,
            file_path=persisted_source_path,
            file_hash=doc_entity.file_hash,
            source_format=doc_entity.source_format,
            word_count=doc_entity.word_count,
            character_count=doc_entity.character_count,
            status=IngestionStatus.COMMITTED,
            processing_profile=doc_entity.processing_profile,
            created_at=doc_entity.created_at,
            updated_at=doc_entity.updated_at,
            error_message=None,
        )

        self.doc_repo.save_document(committed_entity, chapters, sections, paragraphs)
        return committed_entity

    def list_documents(self, user_id: str = "default_user", limit: int = 50, offset: int = 0) -> List[DocumentLibraryCard]:
        return self.doc_repo.list_documents(user_id=user_id, limit=limit, offset=offset)

    def get_document(self, document_id: str) -> DocumentEntity:
        doc = self.doc_repo.get_document_by_id(document_id)
        if not doc:
            raise AppErrorException.not_found(
                code=ErrorCode.DOCUMENT_NOT_FOUND,
                message=f"Document {document_id} not found",
                field="documentId",
            )
        return doc

    def delete_document(self, document_id: str) -> None:
        deleted = self.doc_repo.delete_document(document_id)
        if not deleted:
            raise AppErrorException.not_found(
                code=ErrorCode.DOCUMENT_NOT_FOUND,
                message=f"Document {document_id} not found",
                field="documentId",
            )

    def get_document_structure(self, document_id: str) -> DocumentStructureTree:
        tree = self.doc_repo.get_document_structure(document_id)
        if not tree:
            raise AppErrorException.not_found(
                code=ErrorCode.DOCUMENT_NOT_FOUND,
                message=f"Document structure for {document_id} not found",
                field="documentId",
            )
        return tree

    def update_document_structure(self, document_id: str, request: StructureUpdateRequest) -> DocumentStructureTree:
        return self.doc_repo.update_document_structure(document_id, request)

    def update_exclusions(self, document_id: str, request: ExclusionUpdateRequest) -> None:
        self.doc_repo.update_exclusions(
            doc_id=document_id,
            target_type=request.targetType,
            target_id=request.targetId,
            included=request.includedInPractice,
        )

    def get_section_content(self, document_id: str, section_id: str) -> SectionContentResponse:
        content = self.doc_repo.get_section_content(document_id, section_id)
        if not content:
            raise AppErrorException.not_found(
                code=ErrorCode.SECTION_NOT_FOUND,
                message=f"Section {section_id} not found in document {document_id}",
                field="sectionId",
            )
        return content

    def get_document_progress(self, document_id: str, user_id: str = "default_user") -> ReadingProgressEntity:
        prog = self.progress_repo.get_progress(user_id=user_id, document_id=document_id)
        if not prog:
            raise AppErrorException.not_found(
                code=ErrorCode.DOCUMENT_NOT_FOUND,
                message=f"Reading progress for document {document_id} not found",
                field="documentId",
            )
        return prog

    def update_document_progress(
        self,
        document_id: str,
        pointer: ReadingPositionPointer,
        user_id: str = "default_user",
    ) -> ReadingProgressEntity:
        return self.progress_repo.update_position(user_id=user_id, pointer=pointer)
