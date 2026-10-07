"""
Unit tests for all supported document parsers: PDF, DOCX, HTML, TXT, Markdown.
"""

import tempfile
import pytest
from pathlib import Path

import fitz  # PyMuPDF
import docx

from src.contracts.types import DocumentFormat, ErrorCode
from src.core.errors import AppErrorException
from src.core.document.parsers import DocumentParserRegistry


def test_pdf_parser_text_extraction():
    # Create sample PDF using PyMuPDF
    with tempfile.TemporaryDirectory() as td:
        pdf_path = str(Path(td) / "sample.pdf")
        pdf_doc = fitz.open()
        page = pdf_doc.new_page()
        page.insert_text((50, 72), "Chapter 1: The Principle of Focus", fontsize=18)
        page.insert_text((50, 120), "Reading while typing reinforces muscular and semantic memory.", fontsize=12)
        pdf_doc.save(pdf_path)
        pdf_doc.close()

        raw_doc = DocumentParserRegistry.parse(pdf_path)
        assert raw_doc.format == DocumentFormat.PDF
        assert len(raw_doc.pages) == 1
        texts = [l.text for l in raw_doc.pages[0].lines]
        assert any("The Principle of Focus" in t for t in texts)
        assert any("Reading while typing" in t for t in texts)


def test_pdf_parser_scanned_image_raises_ocr_required():
    # Empty page with 0 text
    with tempfile.TemporaryDirectory() as td:
        pdf_path = str(Path(td) / "scanned.pdf")
        pdf_doc = fitz.open()
        pdf_doc.new_page()
        pdf_doc.save(pdf_path)
        pdf_doc.close()

        with pytest.raises(AppErrorException) as exc_info:
            DocumentParserRegistry.parse(pdf_path)
        assert exc_info.value.code == ErrorCode.OCR_REQUIRED


def test_docx_parser():
    with tempfile.TemporaryDirectory() as td:
        docx_path = str(Path(td) / "sample.docx")
        doc = docx.Document()
        doc.add_heading("Chapter 2: Deep Reading", level=1)
        doc.add_paragraph("Deliberate practice transforms passive habits into active mastery.")
        doc.save(docx_path)

        raw_doc = DocumentParserRegistry.parse(docx_path)
    assert raw_doc.format == DocumentFormat.DOCX
    texts = [l.text for l in raw_doc.pages[0].lines]
    assert any("Deep Reading" in t for t in texts)
    assert any("Deliberate practice" in t for t in texts)


def test_html_parser():
    html_content = """
    <!DOCTYPE html>
    <html>
      <head><title>HTML Book</title></head>
      <body>
        <h1>Chapter 3: The Architecture</h1>
        <p>Offline first architecture guarantees responsiveness and data privacy.</p>
      </body>
    </html>
    """
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(html_content)
        html_path = f.name

    raw_doc = DocumentParserRegistry.parse(html_path)
    assert raw_doc.format == DocumentFormat.HTML
    assert raw_doc.title == "HTML Book"
    texts = [l.text for l in raw_doc.pages[0].lines]
    assert any("The Architecture" in t for t in texts)
    assert any("Offline first" in t for t in texts)
