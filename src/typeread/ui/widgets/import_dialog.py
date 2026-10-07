"""
TypeRead Document Ingestion & Structure Preview Dialog
Renders before/after cleaning diffs, heuristic confidence flags, and chapter hierarchy review tree.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFileDialog,
    QCheckBox,
    QTreeWidget,
    QTreeWidgetItem,
    QFrame,
    QSplitter,
    QTextEdit,
    QGroupBox,
)
from PySide6.QtCore import Qt, Signal

from src.typeread.ui.widgets.theme_manager import ThemeManager


class ImportPreviewDialog(QDialog):
    """
    Dialog for previewing imported documents, inspecting detected structure,
    verifying cleanup quality, and committing to the library.
    """

    commit_confirmed = Signal(str, dict)  # (document_id, update_request)

    def __init__(self, preview_data: Dict[str, Any], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Import Document Preview & Structure Review")
        self.resize(880, 640)
        self.preview = preview_data
        self.doc_id = preview_data.get("document_id", "")

        self._init_ui()
        self._populate_preview()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 1. Metadata Header Box
        meta_box = QGroupBox("Document Metadata", self)
        meta_layout = QHBoxLayout(meta_box)

        meta_layout.addWidget(QLabel("Title:", self))
        self.title_input = QLineEdit(self.preview.get("detected_title", "Untitled Document"), self)
        meta_layout.addWidget(self.title_input)

        meta_layout.addWidget(QLabel("Author:", self))
        self.author_input = QLineEdit(self.preview.get("detected_author", "Unknown"), self)
        meta_layout.addWidget(self.author_input)

        layout.addWidget(meta_box)

        # 2. Splitter: Left = Structure Tree, Right = Before/After Cleanup Diff
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Left: Structure Tree
        left_widget = QWidget(splitter)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("Detected Chapters & Structure:", left_widget))

        self.tree = QTreeWidget(left_widget)
        self.tree.setHeaderLabels(["Title", "Confidence", "Include"])
        left_layout.addWidget(self.tree)
        splitter.addWidget(left_widget)

        # Right: Cleanup Diffs
        right_widget = QWidget(splitter)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(QLabel("Before / After Text Cleanup Preview:", right_widget))

        self.diff_display = QTextEdit(right_widget)
        self.diff_display.setReadOnly(True)
        right_layout.addWidget(self.diff_display)
        splitter.addWidget(right_widget)

        layout.addWidget(splitter, stretch=1)

        # 3. Actions
        btn_box = QHBoxLayout()
        stats = self.preview.get("statistics", {})
        words = stats.get("total_words", 0)
        pages = stats.get("total_pages", 1)
        self.stats_lbl = QLabel(f"Detected: {pages} pages, {words:,} words", self)
        self.stats_lbl.setObjectName("textMuted")
        btn_box.addWidget(self.stats_lbl)
        btn_box.addStretch()

        self.cancel_btn = QPushButton("Cancel", self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(self.cancel_btn)

        self.commit_btn = QPushButton("Commit to Library", self)
        self.commit_btn.setObjectName("primaryBtn")
        self.commit_btn.clicked.connect(self._on_commit)
        btn_box.addWidget(self.commit_btn)

        layout.addLayout(btn_box)

    def _populate_preview(self) -> None:
        # Populate Structure Tree
        structure = self.preview.get("structure_tree", [])
        for chap in structure:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, chap.get("title", "Chapter"))
            score = chap.get("confidence_score", 1.0)
            score_txt = f"{int(score * 100)}%" if score < 0.8 else "High"
            item.setText(1, score_txt)
            item.setText(2, "✓ Included")
            item.setData(0, Qt.ItemDataRole.UserRole, chap)

            for sec in chap.get("sub_sections", []):
                sec_item = QTreeWidgetItem(item)
                sec_item.setText(0, sec.get("title", "Section"))
                sec_item.setText(1, "-")
                sec_item.setText(2, "✓ Included")
                sec_item.setData(0, Qt.ItemDataRole.UserRole, sec)

            item.setExpanded(True)

        # Populate Diff Preview
        samples = self.preview.get("sample_cleanups", [])
        if samples:
            diff_text = ""
            for s in samples:
                diff_text += f"=== {s.get('title', 'Cleanup Sample').upper()} ===\n"
                diff_text += f"[BEFORE]:\n{s.get('before_text', '')}\n\n"
                diff_text += f"[AFTER CLEANUP]:\n{s.get('after_text', '')}\n\n"
                diff_text += "-" * 40 + "\n\n"
            self.diff_display.setPlainText(diff_text)
        else:
            self.diff_display.setPlainText("Text extracted cleanly. No artifacts required repair.")

    def _on_commit(self) -> None:
        # Build structure update request
        chapters_upd = []
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            c_item = root.child(i)
            c_data = c_item.data(0, Qt.ItemDataRole.UserRole) or {}
            c_id = c_data.get("id", f"c_{i}")

            sections_upd = []
            for j in range(c_item.childCount()):
                s_item = c_item.child(j)
                s_data = s_item.data(0, Qt.ItemDataRole.UserRole) or {}
                sections_upd.append({
                    "id": s_data.get("id", f"s_{i}_{j}"),
                    "title": s_item.text(0),
                    "order_index": j,
                    "included_in_practice": True,
                })

            chapters_upd.append({
                "id": c_id,
                "title": c_item.text(0),
                "order_index": i,
                "included_in_practice": True,
                "sections": sections_upd,
            })

        req = {
            "title": self.title_input.text(),
            "author": self.author_input.text(),
            "chapters": chapters_upd,
        }
        self.commit_confirmed.emit(self.doc_id, req)
        self.accept()
