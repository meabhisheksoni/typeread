"""
TypeRead Background Book Extraction & Chapter Segmentation Engine
Supports PDF (via PyMuPDF), EPUB (via zipfile & standard library), and TXT/Markdown.
Extracts outline, table of contents, and clean chapter-by-chapter text.
"""

from __future__ import annotations
import sys
import os
import re
import json
import zipfile
import html
from html.parser import HTMLParser
from typing import List, Dict, Any, Optional

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.ignore = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() in ('script', 'style', 'nav', 'head'):
            self.ignore = True
        elif tag.lower() in ('p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'li'):
            self.text_parts.append('\n')

    def handle_endtag(self, tag):
        if tag.lower() in ('script', 'style', 'nav', 'head'):
            self.ignore = False
        elif tag.lower() in ('p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'):
            self.text_parts.append('\n')

    def handle_data(self, data):
        if not self.ignore:
            self.text_parts.append(data)

    def get_text(self) -> str:
        raw = "".join(self.text_parts)
        # Normalize excessive newlines and spaces
        cleaned = re.sub(r'[ \t]+', ' ', raw)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        return cleaned.strip()


def clean_text(text: str) -> str:
    """Normalize whitespace and unescape HTML entities."""
    text = html.unescape(text)
    text = re.sub(r'\r\n|\r', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def parse_pdf(file_path: str) -> Dict[str, Any]:
    if not fitz:
        raise RuntimeError("PyMuPDF (fitz) is not installed.")

    doc = fitz.open(file_path)
    title = doc.metadata.get("title") or os.path.splitext(os.path.basename(file_path))[0]
    author = doc.metadata.get("author") or "Unknown Author"

    toc = doc.get_toc()  # [[lvl, title, page_1_indexed], ...]
    chapters = []

    if toc and len(toc) > 0:
        # Filter for top levels or valid chapter entries
        entries = []
        for item in toc:
            lvl, t, page = item[0], item[1].strip(), item[2]
            if page <= doc.page_count:
                entries.append((t, page - 1))  # 0-indexed page

        # Deduplicate consecutive entries on same page with similar titles
        filtered_entries = []
        for t, page in entries:
            if not filtered_entries or filtered_entries[-1][1] != page or len(t) > len(filtered_entries[-1][0]):
                filtered_entries.append((t, page))

        # Extract text slice between chapter boundaries
        for i, (ch_title, start_page) in enumerate(filtered_entries):
            end_page = filtered_entries[i + 1][1] if i + 1 < len(filtered_entries) else doc.page_count
            ch_text_parts = []
            for p in range(start_page, min(end_page, doc.page_count)):
                page = doc.load_page(p)
                ch_text_parts.append(page.get_text("text"))

            ch_text = clean_text("\n".join(ch_text_parts))
            if len(ch_text) >= 20:  # Skip empty marker pages
                chapters.append({
                    "id": f"c{len(chapters) + 1}",
                    "title": ch_title,
                    "text": ch_text
                })

    # Fallback if no TOC outline found or TOC extraction was empty
    if not chapters:
        all_pages_text = []
        for p in range(doc.page_count):
            page = doc.load_page(p)
            all_pages_text.append(page.get_text("text"))
        full_text = clean_text("\n".join(all_pages_text))
        chapters = split_text_into_chapters(full_text)

    doc.close()
    return {
        "id": f"doc-{os.path.basename(file_path).replace(' ', '-').lower()}",
        "title": title,
        "author": author,
        "format": "PDF",
        "chapters": chapters
    }


def parse_epub(file_path: str) -> Dict[str, Any]:
    with zipfile.ZipFile(file_path, 'r') as z:
        # Step 1: Find container.xml
        container_data = z.read("META-INF/container.xml").decode("utf-8", errors="ignore")
        match = re.search(r'full-path=["\']([^"\']+)["\']', container_data)
        if not match:
            raise ValueError("Invalid EPUB: META-INF/container.xml missing rootfile")
        opf_path = match.group(1)
        opf_dir = os.path.dirname(opf_path)

        # Step 2: Read OPF
        opf_content = z.read(opf_path).decode("utf-8", errors="ignore")
        
        # Metadata
        title_m = re.search(r'<dc:title[^>]*>([^<]+)</dc:title>', opf_content, re.IGNORECASE)
        title = clean_text(title_m.group(1)) if title_m else os.path.splitext(os.path.basename(file_path))[0]
        
        author_m = re.search(r'<dc:creator[^>]*>([^<]+)</dc:creator>', opf_content, re.IGNORECASE)
        author = clean_text(author_m.group(1)) if author_m else "Unknown Author"

        # Manifest
        manifest = {}
        for m in re.finditer(r'<item\s+[^>]*id=["\']([^"\']+)["\'][^>]*href=["\']([^"\']+)["\']', opf_content, re.IGNORECASE):
            manifest[m.group(1)] = m.group(2)
        # In case attributes are in reverse order
        for m in re.finditer(r'<item\s+[^>]*href=["\']([^"\']+)["\'][^>]*id=["\']([^"\']+)["\']', opf_content, re.IGNORECASE):
            manifest[m.group(2)] = m.group(1)

        # Spine
        spine = []
        for m in re.finditer(r'<itemref\s+[^>]*idref=["\']([^"\']+)["\']', opf_content, re.IGNORECASE):
            spine.append(m.group(1))

        # Read TOC (toc.ncx) if present for chapter titles
        toc_titles = {}
        ncx_id = next((k for k in manifest if 'ncx' in k.lower() or 'toc' in k.lower()), None)
        if ncx_id and ncx_id in manifest:
            ncx_path = os.path.normpath(os.path.join(opf_dir, manifest[ncx_id])).replace('\\', '/')
            try:
                ncx_data = z.read(ncx_path).decode("utf-8", errors="ignore")
                for nav_match in re.finditer(r'<navPoint[^>]*>.*?<text>([^<]+)</text>.*?<content\s+src=["\']([^"\']+)["\']', ncx_data, re.DOTALL | re.IGNORECASE):
                    t = clean_text(nav_match.group(1))
                    src = nav_match.group(2).split('#')[0]
                    toc_titles[os.path.basename(src)] = t
            except Exception:
                pass

        chapters = []
        for item_id in spine:
            if item_id not in manifest:
                continue
            href = manifest[item_id]
            file_rel = os.path.normpath(os.path.join(opf_dir, href)).replace('\\', '/')
            try:
                html_data = z.read(file_rel).decode("utf-8", errors="ignore")
            except KeyError:
                continue

            parser = HTMLTextExtractor()
            parser.feed(html_data)
            raw_text = parser.get_text()
            if len(raw_text.strip()) < 50:
                continue

            # Determine title
            filename = os.path.basename(href)
            chapter_title = toc_titles.get(filename)
            if not chapter_title:
                h_match = re.search(r'<h[1-3][^>]*>(.*?)</h[1-3]>', html_data, re.DOTALL | re.IGNORECASE)
                if h_match:
                    h_parser = HTMLTextExtractor()
                    h_parser.feed(h_match.group(1))
                    h_t = h_parser.get_text().strip()
                    if h_t and len(h_t) <= 80:
                        chapter_title = h_t
            if not chapter_title:
                chapter_title = f"Chapter {len(chapters) + 1}"

            chapters.append({
                "id": f"c{len(chapters) + 1}",
                "title": chapter_title,
                "text": raw_text
            })

    if not chapters:
        chapters = [{
            "id": "c1",
            "title": "Section 1",
            "text": "Could not extract chapters from EPUB content."
        }]

    return {
        "id": f"doc-{os.path.basename(file_path).replace(' ', '-').lower()}",
        "title": title,
        "author": author,
        "format": "EPUB",
        "chapters": chapters
    }


def split_text_into_chapters(text: str) -> List[Dict[str, str]]:
    """Splits plain text into chapters using regex heuristic detection."""
    # Pattern matching Chapter 1, CHAPTER I, Part 1, Act 1, Book 1, etc.
    pattern = re.compile(
        r'(?:^|(?:\r?\n){2,})(?:#+\s*)?((?:chapter|part|book|section|act)\s+[0-9ivxlcdm]+[^\n]*|[A-Z0-9\s]{4,45})(?:\r?\n)+',
        re.IGNORECASE
    )

    matches = list(pattern.finditer(text))
    if len(matches) >= 2:
        chapters = []
        for i, m in enumerate(matches):
            ch_title = clean_text(m.group(1))
            start_pos = m.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            ch_text = clean_text(text[start_pos:end_pos])
            if len(ch_text) >= 30:
                chapters.append({
                    "id": f"c{len(chapters) + 1}",
                    "title": ch_title,
                    "text": ch_text
                })
        if chapters:
            return chapters

    # Fallback: Split by ~1,200 words into manageable sections
    words = text.split()
    chunk_size = 1200
    chapters = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chapters.append({
            "id": f"c{len(chapters) + 1}",
            "title": f"Section {len(chapters) + 1}",
            "text": chunk
        })
    return chapters if chapters else [{
        "id": "c1",
        "title": "Section 1",
        "text": text
    }]


def parse_text_file(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    title = os.path.splitext(os.path.basename(file_path))[0].replace("-", " ").title()
    chapters = split_text_into_chapters(clean_text(content))

    return {
        "id": f"doc-{os.path.basename(file_path).replace(' ', '-').lower()}",
        "title": title,
        "author": "Imported Text",
        "format": "TXT",
        "chapters": chapters
    }


def parse_book(file_path: str) -> Dict[str, Any]:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return parse_pdf(file_path)
    elif ext == ".epub":
        return parse_epub(file_path)
    elif ext in (".txt", ".md", ".text"):
        return parse_text_file(file_path)
    else:
        raise ValueError(f"Unsupported format: {ext}. Please provide .pdf, .epub, or .txt")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_book.py <book_file.pdf|.epub|.txt> [output.json]")
        sys.exit(1)

    input_file = sys.argv[1]
    result = parse_book(input_file)
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    if output_path:
        with open(output_path, "w", encoding="utf-8") as out:
            json.dump(result, out, indent=2, ensure_ascii=False)
        print(f"Saved {len(result['chapters'])} chapters to {output_path}")
    else:
        print(json.dumps({
            "title": result["title"],
            "author": result["author"],
            "chapters_count": len(result["chapters"]),
            "chapters": [{"title": c["title"], "word_count": len(c["text"].split())} for c in result["chapters"]]
        }, indent=2))
