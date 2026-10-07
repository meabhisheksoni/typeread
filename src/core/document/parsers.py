"""
TypeRead Document Parsers
Supports PDF, EPUB, DOCX, TXT, Markdown, HTML.
Pure Python extraction with zero cloud dependencies.
"""

from __future__ import annotations
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from pathlib import Path

from src.contracts.types import DocumentFormat, ErrorCode
from src.core.errors import AppErrorException


@dataclass
class RawLine:
    text: str
    page_number: int
    font_size: float = 12.0
    is_bold: bool = False
    position_y: float = 0.0
    position_x: float = 0.0
    line_width: float = 0.0
    is_heading_hint: bool = False
    heading_level_hint: Optional[int] = None


@dataclass
class RawPage:
    page_number: int
    lines: List[RawLine] = field(default_factory=list)


@dataclass
class RawDocumentContent:
    title: str
    author: str
    format: DocumentFormat
    pages: List[RawPage] = field(default_factory=list)
    raw_text: str = ""


class DocumentParserRegistry:
    @staticmethod
    def detect_format(file_path: str) -> DocumentFormat:
        ext = Path(file_path).suffix.lower().lstrip(".")
        format_map = {
            "pdf": DocumentFormat.PDF,
            "epub": DocumentFormat.EPUB,
            "docx": DocumentFormat.DOCX,
            "txt": DocumentFormat.TXT,
            "text": DocumentFormat.TXT,
            "md": DocumentFormat.MARKDOWN,
            "markdown": DocumentFormat.MARKDOWN,
            "html": DocumentFormat.HTML,
            "htm": DocumentFormat.HTML,
        }
        if ext in format_map:
            return format_map[ext]
        raise AppErrorException.bad_request(
            code=ErrorCode.UNSUPPORTED_FORMAT,
            message=f"Unsupported file format: '.{ext}'",
            field="filePath",
            suggested_action="Please provide a PDF, EPUB, DOCX, TXT, Markdown, or HTML file.",
        )

    @classmethod
    def parse(cls, file_path: str, format_override: Optional[DocumentFormat] = None) -> RawDocumentContent:
        if not os.path.exists(file_path):
            raise AppErrorException.bad_request(
                code=ErrorCode.FILE_NOT_FOUND,
                message=f"File not found at path: {file_path}",
                field="filePath",
            )

        if not os.path.isfile(file_path) or not os.access(file_path, os.R_OK):
            raise AppErrorException.bad_request(
                code=ErrorCode.FILE_UNREADABLE,
                message=f"File is not readable or permission denied: {file_path}",
                field="filePath",
            )

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise AppErrorException.bad_request(
                code=ErrorCode.EMPTY_DOCUMENT,
                message="Document is empty (0 bytes)",
                field="filePath",
            )

        doc_format = format_override or cls.detect_format(file_path)

        try:
            if doc_format == DocumentFormat.PDF:
                return cls._parse_pdf(file_path)
            elif doc_format == DocumentFormat.EPUB:
                return cls._parse_epub(file_path)
            elif doc_format == DocumentFormat.DOCX:
                return cls._parse_docx(file_path)
            elif doc_format == DocumentFormat.TXT:
                return cls._parse_txt(file_path)
            elif doc_format == DocumentFormat.MARKDOWN:
                return cls._parse_markdown(file_path)
            elif doc_format == DocumentFormat.HTML:
                return cls._parse_html(file_path)
            else:
                raise AppErrorException.bad_request(
                    code=ErrorCode.UNSUPPORTED_FORMAT,
                    message=f"Unsupported document format: {doc_format}",
                )
        except AppErrorException:
            raise
        except Exception as e:
            raise AppErrorException.unprocessable(
                code=ErrorCode.PARSING_FAILED,
                message=f"Failed to parse document: {str(e)}",
                suggested_action="Ensure the file is not corrupted or password-protected.",
            )

    @staticmethod
    def _parse_pdf(file_path: str) -> RawDocumentContent:
        import fitz  # PyMuPDF

        try:
            doc = fitz.open(file_path)
        except Exception as e:
            raise AppErrorException.unprocessable(
                code=ErrorCode.CORRUPTED_DOCUMENT,
                message=f"Could not open PDF: {str(e)}",
            )

        if doc.is_encrypted:
            raise AppErrorException.unprocessable(
                code=ErrorCode.FILE_UNREADABLE,
                message="PDF is password protected or encrypted.",
            )

        meta = doc.metadata or {}
        title = meta.get("title") or Path(file_path).stem
        author = meta.get("author") or "Unknown"

        # Extract PDF Table of Contents (Outline) if available
        toc = doc.get_toc() or []
        toc_lookup: dict[int, list[tuple[int, str]]] = {}
        for item in toc:
            if len(item) >= 3:
                lvl, t_title, p_num = item[0], str(item[1]).strip().lower(), item[2]
                if t_title:
                    toc_lookup.setdefault(p_num, []).append((lvl, t_title))

        pages: List[RawPage] = []
        total_extracted_chars = 0

        for page_idx, page in enumerate(doc):
            page_num = page_idx + 1
            raw_page = RawPage(page_number=page_num)

            # Extract detailed text blocks with font sizes and weights
            text_page = page.get_text("dict")
            blocks = text_page.get("blocks", [])

            for block in blocks:
                if block.get("type") == 0:  # Text block
                    for line in block.get("lines", []):
                        spans = line.get("spans", [])
                        if not spans:
                            continue
                        line_text = "".join(s.get("text", "") for s in spans).strip()
                        if not line_text:
                            continue

                        # Compute average font size and detect bold flags
                        sizes = [s.get("size", 12.0) for s in spans if s.get("text", "").strip()]
                        avg_size = sum(sizes) / len(sizes) if sizes else 12.0
                        flags = [s.get("flags", 0) for s in spans]
                        # In PyMuPDF, bit 4 (16) is bold, bit 1 (2) is italic
                        is_bold = any(bool(f & 16) for f in flags)
                        bbox = line.get("bbox", (0, 0, 0, 0))
                        pos_x = bbox[0]
                        pos_y = bbox[1]
                        line_width = bbox[2] - bbox[0]

                        # Check if line matches PDF outline / TOC
                        is_heading_hint = False
                        heading_level_hint = None
                        if page_num in toc_lookup:
                            for lvl, t_title in toc_lookup[page_num]:
                                lt_lower = line_text.lower()
                                if t_title == lt_lower or t_title in lt_lower or lt_lower in t_title:
                                    is_heading_hint = True
                                    heading_level_hint = lvl
                                    break

                        raw_page.lines.append(
                            RawLine(
                                text=line_text,
                                page_number=page_num,
                                font_size=avg_size,
                                is_bold=is_bold,
                                position_y=pos_y,
                                position_x=pos_x,
                                line_width=line_width,
                                is_heading_hint=is_heading_hint,
                                heading_level_hint=heading_level_hint,
                            )
                        )
                        total_extracted_chars += len(line_text)

            pages.append(raw_page)

        doc.close()

        if total_extracted_chars == 0:
            raise AppErrorException.unprocessable(
                code=ErrorCode.OCR_REQUIRED,
                message="No extractable text found in PDF. Document appears to be a scanned image.",
                suggested_action="Run OCR on document to extract readable text.",
            )

        return RawDocumentContent(
            title=title,
            author=author,
            format=DocumentFormat.PDF,
            pages=pages,
        )

    @staticmethod
    def _parse_epub(file_path: str) -> RawDocumentContent:
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup

        try:
            book = epub.read_epub(file_path)
        except Exception as e:
            raise AppErrorException.unprocessable(
                code=ErrorCode.CORRUPTED_DOCUMENT,
                message=f"Could not open EPUB: {str(e)}",
            )

        title = book.get_metadata("DC", "title")
        title_str = title[0][0] if title else Path(file_path).stem
        creator = book.get_metadata("DC", "creator")
        author_str = creator[0][0] if creator else "Unknown"

        pages: List[RawPage] = []
        page_num = 1

        items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
        for item in items:
            soup = BeautifulSoup(item.get_content(), "html.parser")
            raw_page = RawPage(page_number=page_num)

            for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p"]):
                text = tag.get_text().strip()
                if not text:
                    continue
                tag_name = tag.name.lower()
                is_heading = tag_name.startswith("h")
                level_hint = int(tag_name[1]) if is_heading else None

                raw_page.lines.append(
                    RawLine(
                        text=text,
                        page_number=page_num,
                        font_size=18.0 if is_heading else 12.0,
                        is_bold=is_heading,
                        is_heading_hint=is_heading,
                        heading_level_hint=level_hint,
                    )
                )

            if raw_page.lines:
                pages.append(raw_page)
                page_num += 1

        if not pages:
            raise AppErrorException.bad_request(
                code=ErrorCode.EMPTY_DOCUMENT,
                message="EPUB contains no readable text content.",
            )

        return RawDocumentContent(
            title=title_str,
            author=author_str,
            format=DocumentFormat.EPUB,
            pages=pages,
        )

    @staticmethod
    def _parse_docx(file_path: str) -> RawDocumentContent:
        import docx

        try:
            doc = docx.Document(file_path)
        except Exception as e:
            raise AppErrorException.unprocessable(
                code=ErrorCode.CORRUPTED_DOCUMENT,
                message=f"Could not open DOCX: {str(e)}",
            )

        title = Path(file_path).stem
        author = "Unknown"
        if doc.core_properties:
            if doc.core_properties.title:
                title = doc.core_properties.title
            if doc.core_properties.author:
                author = doc.core_properties.author

        raw_page = RawPage(page_number=1)
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue

            style_name = p.style.name.lower() if p.style else ""
            is_heading = "heading" in style_name
            level_hint = None
            if is_heading:
                m = re.search(r"\d+", style_name)
                level_hint = int(m.group(0)) if m else 1

            is_bold = any(run.bold for run in p.runs if run.bold is not None)

            raw_page.lines.append(
                RawLine(
                    text=text,
                    page_number=1,
                    font_size=18.0 if is_heading else 12.0,
                    is_bold=is_heading or is_bold,
                    is_heading_hint=is_heading,
                    heading_level_hint=level_hint,
                )
            )

        if not raw_page.lines:
            raise AppErrorException.bad_request(
                code=ErrorCode.EMPTY_DOCUMENT,
                message="DOCX contains no text content.",
            )

        return RawDocumentContent(
            title=title,
            author=author,
            format=DocumentFormat.DOCX,
            pages=[raw_page],
        )

    @staticmethod
    def _parse_txt(file_path: str) -> RawDocumentContent:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            raise AppErrorException.unprocessable(
                code=ErrorCode.FILE_UNREADABLE,
                message=f"Could not read text file: {str(e)}",
            )

        if not content.strip():
            raise AppErrorException.bad_request(
                code=ErrorCode.EMPTY_DOCUMENT,
                message="Text file is empty.",
            )

        title = Path(file_path).stem
        pages: List[RawPage] = []
        raw_page = RawPage(page_number=1)

        for line in content.splitlines():
            line_str = line.strip()
            if line_str:
                raw_page.lines.append(RawLine(text=line_str, page_number=1))

        pages.append(raw_page)
        return RawDocumentContent(
            title=title,
            author="Unknown",
            format=DocumentFormat.TXT,
            pages=pages,
            raw_text=content,
        )

    @staticmethod
    def _parse_markdown(file_path: str) -> RawDocumentContent:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            raise AppErrorException.unprocessable(
                code=ErrorCode.FILE_UNREADABLE,
                message=f"Could not read markdown file: {str(e)}",
            )

        if not content.strip():
            raise AppErrorException.bad_request(
                code=ErrorCode.EMPTY_DOCUMENT,
                message="Markdown file is empty.",
            )

        title = Path(file_path).stem
        pages: List[RawPage] = []
        raw_page = RawPage(page_number=1)

        for line in content.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
            if heading_match:
                level = len(heading_match.group(1))
                h_text = heading_match.group(2).strip()
                raw_page.lines.append(
                    RawLine(
                        text=h_text,
                        page_number=1,
                        font_size=20.0 - level * 1.5,
                        is_bold=True,
                        is_heading_hint=True,
                        heading_level_hint=level,
                    )
                )
            else:
                raw_page.lines.append(RawLine(text=stripped, page_number=1))

        pages.append(raw_page)
        return RawDocumentContent(
            title=title,
            author="Unknown",
            format=DocumentFormat.MARKDOWN,
            pages=pages,
            raw_text=content,
        )

    @staticmethod
    def _parse_html(file_path: str) -> RawDocumentContent:
        from bs4 import BeautifulSoup

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                html_text = f.read()
        except Exception as e:
            raise AppErrorException.unprocessable(
                code=ErrorCode.FILE_UNREADABLE,
                message=f"Could not read HTML file: {str(e)}",
            )

        if not html_text.strip():
            raise AppErrorException.bad_request(
                code=ErrorCode.EMPTY_DOCUMENT,
                message="HTML file is empty.",
            )

        soup = BeautifulSoup(html_text, "html.parser")
        title_tag = soup.find("title")
        title = title_tag.get_text().strip() if title_tag else Path(file_path).stem

        pages: List[RawPage] = []
        raw_page = RawPage(page_number=1)

        for el in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li"]):
            text = el.get_text().strip()
            if not text:
                continue
            tag_name = el.name.lower()
            is_heading = tag_name.startswith("h")
            level_hint = int(tag_name[1]) if is_heading else None

            raw_page.lines.append(
                RawLine(
                    text=text,
                    page_number=1,
                    font_size=18.0 if is_heading else 12.0,
                    is_bold=is_heading,
                    is_heading_hint=is_heading,
                    heading_level_hint=level_hint,
                )
            )

        if not raw_page.lines:
            raise AppErrorException.bad_request(
                code=ErrorCode.EMPTY_DOCUMENT,
                message="HTML contains no readable text content.",
            )

        pages.append(raw_page)
        return RawDocumentContent(
            title=title,
            author="Unknown",
            format=DocumentFormat.HTML,
            pages=pages,
        )
