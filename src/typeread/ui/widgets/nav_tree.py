"""
TypeRead Document Navigation Tree Widget
Binds to DocumentStructureTree with chapter/section hierarchy, progress badges, and practice exclusion toggles.
"""

from __future__ import annotations
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QLabel,
    QHBoxLayout,
    QPushButton,
)
from PySide6.QtCore import Qt, Signal

from src.typeread.ui.widgets.theme_manager import ThemeManager


class NavTreeWidget(QWidget):
    """
    Left sidebar navigation tree for selecting chapters and sections.
    """

    section_selected = Signal(str, str)  # (chapter_id, section_id)
    exclusion_toggled = Signal(str, str, bool)  # (target_type, target_id, included)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.theme = "dark"
        self.structure_data: Optional[Dict[str, Any]] = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        header_box = QHBoxLayout()
        self.title_lbl = QLabel("TABLE OF CONTENTS", self)
        self.title_lbl.setObjectName("textMuted")
        f = self.title_lbl.font()
        f.setPointSize(10)
        f.setBold(True)
        self.title_lbl.setFont(f)
        header_box.addWidget(self.title_lbl)
        header_box.addStretch()
        layout.addLayout(header_box)

        # Tree Widget
        self.tree = QTreeWidget(self)
        self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree)

    def set_theme(self, theme: str) -> None:
        self.theme = theme

    def load_structure(self, structure: Dict[str, Any]) -> None:
        self.structure_data = structure
        self.tree.clear()

        doc = structure.get("document", {})
        self.title_lbl.setText(doc.get("title", "TABLE OF CONTENTS").upper())

        chapters = structure.get("chapters", [])
        for chap in chapters:
            chap_item = QTreeWidgetItem(self.tree)
            inc_prefix = "✓ " if chap.get("included_in_practice", True) else "✗ "
            chap_item.setText(0, f"{inc_prefix}{chap.get('title', 'Chapter')}")
            chap_item.setData(0, Qt.ItemDataRole.UserRole, {
                "type": "chapter",
                "id": chap.get("id"),
                "included": chap.get("included_in_practice", True),
            })

            sections = chap.get("sections", [])
            for sec in sections:
                sec_item = QTreeWidgetItem(chap_item)
                sec_inc = "✓ " if sec.get("included_in_practice", True) else "✗ "
                sec_item.setText(0, f"{sec_inc}{sec.get('title', 'Section')}")
                sec_item.setData(0, Qt.ItemDataRole.UserRole, {
                    "type": "section",
                    "chapter_id": chap.get("id"),
                    "id": sec.get("id"),
                    "included": sec.get("included_in_practice", True),
                })

            chap_item.setExpanded(True)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        if data.get("type") == "section":
            self.section_selected.emit(data["chapter_id"], data["id"])

    def select_section(self, section_id: str) -> None:
        # Highlight corresponding item in tree
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            chap_item = root.child(i)
            for j in range(chap_item.childCount()):
                sec_item = chap_item.child(j)
                data = sec_item.data(0, Qt.ItemDataRole.UserRole)
                if data and data.get("id") == section_id:
                    self.tree.setCurrentItem(sec_item)
                    return
