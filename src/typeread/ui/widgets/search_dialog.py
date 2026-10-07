"""
TypeRead Full-Text Search Dialog Widget
Provides instant indexed SQLite FTS5 search and direct navigation to matched paragraphs.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFrame,
)
from PySide6.QtCore import Qt, Signal

from src.typeread.ui.client import UiApiClient


class SearchDialog(QDialog):
    """
    Search dialog (Ctrl+F / Ctrl+K) allowing quick search across all imported documents.
    """

    result_selected = Signal(str, str, str, int)  # (doc_id, chap_id, sec_id, offset)

    def __init__(self, api_client: UiApiClient, current_doc_id: Optional[str] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Search Documents")
        self.resize(700, 480)
        self.api = api_client
        self.current_doc_id = current_doc_id

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Search Bar
        search_box = QHBoxLayout()
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Type keywords to search across library... (Press Enter)")
        self.search_input.returnPressed.connect(self._execute_search)
        search_box.addWidget(self.search_input)

        self.search_btn = QPushButton("Search", self)
        self.search_btn.clicked.connect(self._execute_search)
        search_box.addWidget(self.search_btn)
        layout.addLayout(search_box)

        # Results Count Label
        self.count_lbl = QLabel("Enter search query above.", self)
        self.count_lbl.setObjectName("textMuted")
        layout.addWidget(self.count_lbl)

        # Results List
        self.results_list = QListWidget(self)
        self.results_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.results_list)

        # Actions
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        self.close_btn = QPushButton("Close", self)
        self.close_btn.clicked.connect(self.reject)
        btn_box.addWidget(self.close_btn)
        layout.addLayout(btn_box)

    def _execute_search(self) -> None:
        query = self.search_input.text().strip()
        if not query:
            return

        self.results_list.clear()
        self.count_lbl.setText("Searching...")

        try:
            res = self.api.search_documents(query=query, document_id=self.current_doc_id)
            items = res.get("items", [])
            total = res.get("total_matches", len(items))

            self.count_lbl.setText(f"Found {total} matches:")

            for item in items:
                list_item = QListWidgetItem(self.results_list)
                doc_title = item.get("document_title", "Document")
                sec_title = item.get("section_title", "Section")
                snippet = item.get("matched_snippet", "").replace("<mark>", "[").replace("</mark>", "]")

                list_item.setText(f"{doc_title} > {sec_title}\n  {snippet}")
                list_item.setData(Qt.ItemDataRole.UserRole, item)

        except Exception as ex:
            self.count_lbl.setText(f"Search failed: {str(ex)}")

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            doc_id = data.get("document_id", "")
            chap_id = data.get("chapter_id", "")
            sec_id = data.get("section_id", "")
            offset = data.get("character_offset", 0)
            self.result_selected.emit(doc_id, chap_id, sec_id, offset)
            self.accept()
