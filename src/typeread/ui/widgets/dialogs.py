"""
TypeRead Supplementary Dialogs: Crash Recovery, Completion, Bookmarks, and Help.
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
    QFrame,
    QLineEdit,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
)
from PySide6.QtCore import Qt, Signal

from src.typeread.ui.client import UiApiClient


class CrashRecoveryDialog(QDialog):
    """
    Startup modal when unclosed session is detected in SQLite.
    Fulfills PRD Section 70 & ARCH_DECISIONS 4.3.
    """

    def __init__(
        self,
        doc_title: str,
        chapter_title: str,
        progress_pct: float,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Resume Unfinished Session")
        self.resize(460, 200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title_lbl = QLabel("Unfinished Session Found", self)
        f = title_lbl.font()
        f.setPointSize(14)
        f.setBold(True)
        title_lbl.setFont(f)
        layout.addWidget(title_lbl)

        msg_lbl = QLabel(
            f"Unfinished practice session found for:\n\n"
            f"• Document: {doc_title}\n"
            f"• Chapter: {chapter_title}\n"
            f"• Progress: {progress_pct:.1f}%\n\n"
            f"Would you like to resume your practice?",
            self,
        )
        msg_lbl.setWordWrap(True)
        layout.addWidget(msg_lbl)

        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.decline_btn = QPushButton("Start Fresh", self)
        self.decline_btn.clicked.connect(self.reject)
        btn_box.addWidget(self.decline_btn)

        self.resume_btn = QPushButton("Resume Practice", self)
        self.resume_btn.setObjectName("primaryBtn")
        self.resume_btn.clicked.connect(self.accept)
        btn_box.addWidget(self.resume_btn)

        layout.addLayout(btn_box)


class CompletionDialog(QDialog):
    """
    Completion state dialog matching PRD Section 127.
    """

    view_stats_requested = Signal()
    restart_requested = Signal()
    library_requested = Signal()

    def __init__(
        self,
        title: str,
        avg_wpm: float,
        accuracy_pct: float,
        total_seconds: int,
        words_typed: int,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Session Complete")
        self.resize(480, 360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header_lbl = QLabel("Book / Section Complete!", self)
        header_lbl.setObjectName("sectionHeading")
        layout.addWidget(header_lbl)

        title_lbl = QLabel(title, self)
        f = title_lbl.font()
        f.setPointSize(16)
        f.setBold(True)
        title_lbl.setFont(f)
        layout.addWidget(title_lbl)

        # Stats Card
        card = QFrame(self)
        card.setObjectName("cardFrame")
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(10)

        mins = total_seconds // 60
        time_str = f"{mins // 60}h {mins % 60}m" if mins >= 60 else f"{mins}m {total_seconds % 60}s"

        c_layout.addWidget(QLabel(f"Average WPM:       {int(avg_wpm)}", card))
        c_layout.addWidget(QLabel(f"Accuracy:          {accuracy_pct:.1f}%", card))
        c_layout.addWidget(QLabel(f"Practice Time:     {time_str}", card))
        c_layout.addWidget(QLabel(f"Words Typed:       {words_typed:,}", card))
        layout.addWidget(card)

        # Action Buttons
        btn_box = QHBoxLayout()
        self.stats_btn = QPushButton("View Statistics", self)
        self.stats_btn.clicked.connect(self._on_stats)
        btn_box.addWidget(self.stats_btn)

        self.restart_btn = QPushButton("Start Revision", self)
        self.restart_btn.clicked.connect(self._on_restart)
        btn_box.addWidget(self.restart_btn)

        self.lib_btn = QPushButton("Return to Library", self)
        self.lib_btn.setObjectName("primaryBtn")
        self.lib_btn.clicked.connect(self._on_library)
        btn_box.addWidget(self.lib_btn)

        layout.addLayout(btn_box)

    def _on_stats(self) -> None:
        self.view_stats_requested.emit()
        self.accept()

    def _on_restart(self) -> None:
        self.restart_requested.emit()
        self.accept()

    def _on_library(self) -> None:
        self.library_requested.emit()
        self.accept()


class BookmarksNotesDialog(QDialog):
    """
    Bookmark (Ctrl+B) and Notes management dialog.
    """

    bookmark_jumped = Signal(str, str, str, str, int)  # (doc_id, chap_id, sec_id, para_id, offset)

    def __init__(
        self,
        api_client: UiApiClient,
        doc_id: Optional[str] = None,
        chap_id: Optional[str] = None,
        sec_id: Optional[str] = None,
        para_id: Optional[str] = None,
        offset: int = 0,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Bookmarks & Notes")
        self.resize(600, 440)
        self.api = api_client
        self.doc_id = doc_id
        self.chap_id = chap_id
        self.sec_id = sec_id
        self.para_id = para_id
        self.offset = offset

        self._init_ui()
        self._load_data()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.tabs = QTabWidget(self)

        # Tab 1: Bookmarks
        bm_tab = QWidget()
        bm_layout = QVBoxLayout(bm_tab)

        add_bm_box = QHBoxLayout()
        self.bm_title_input = QLineEdit(bm_tab)
        self.bm_title_input.setPlaceholderText("Bookmark title...")
        add_bm_box.addWidget(self.bm_title_input)

        self.add_bm_btn = QPushButton("Add Bookmark Here", bm_tab)
        self.add_bm_btn.setObjectName("primaryBtn")
        self.add_bm_btn.clicked.connect(self._add_bookmark)
        add_bm_box.addWidget(self.add_bm_btn)
        bm_layout.addLayout(add_bm_box)

        self.bm_list = QListWidget(bm_tab)
        self.bm_list.itemDoubleClicked.connect(self._on_bm_jump)
        bm_layout.addWidget(self.bm_list)
        self.tabs.addTab(bm_tab, "Bookmarks")

        # Tab 2: Notes
        notes_tab = QWidget()
        notes_layout = QVBoxLayout(notes_tab)

        self.note_content_input = QTextEdit(notes_tab)
        self.note_content_input.setPlaceholderText("Write a study note for this section...")
        self.note_content_input.setMaximumHeight(80)
        notes_layout.addWidget(self.note_content_input)

        self.add_note_btn = QPushButton("Save Note", notes_tab)
        self.add_note_btn.clicked.connect(self._add_note)
        notes_layout.addWidget(self.add_note_btn)

        self.notes_list = QListWidget(notes_tab)
        notes_layout.addWidget(self.notes_list)
        self.tabs.addTab(notes_tab, "Notes")

        layout.addWidget(self.tabs)

        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _load_data(self) -> None:
        self.bm_list.clear()
        self.notes_list.clear()
        try:
            bms = self.api.list_bookmarks(self.doc_id)
            for b in bms:
                item = QListWidgetItem(self.bm_list)
                item.setText(f"🔖 {b.get('title', 'Bookmark')} (Offset: {b.get('character_offset', 0)})")
                item.setData(Qt.ItemDataRole.UserRole, b)

            notes = self.api.list_notes(self.doc_id)
            for n in notes:
                item = QListWidgetItem(self.notes_list)
                item.setText(f"📝 {n.get('content', '')}")
                item.setData(Qt.ItemDataRole.UserRole, n)
        except Exception:
            pass

    def _add_bookmark(self) -> None:
        title = self.bm_title_input.text().strip() or "Bookmark"
        if not self.doc_id or not self.chap_id or not self.sec_id:
            return
        try:
            self.api.create_bookmark(
                document_id=self.doc_id,
                chapter_id=self.chap_id,
                section_id=self.sec_id,
                paragraph_id=self.para_id or "",
                character_offset=self.offset,
                title=title,
            )
            self.bm_title_input.clear()
            self._load_data()
        except Exception:
            pass

    def _add_note(self) -> None:
        content = self.note_content_input.toPlainText().strip()
        if not content or not self.doc_id or not self.chap_id or not self.sec_id:
            return
        try:
            self.api.create_note(
                document_id=self.doc_id,
                chapter_id=self.chap_id,
                section_id=self.sec_id,
                paragraph_id=self.para_id or "",
                content=content,
            )
            self.note_content_input.clear()
            self._load_data()
        except Exception:
            pass

    def _on_bm_jump(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self.bookmark_jumped.emit(
                data.get("document_id", ""),
                data.get("chapter_id", ""),
                data.get("section_id", ""),
                data.get("paragraph_id", ""),
                data.get("character_offset", 0),
            )
            self.accept()


class HelpShortcutsDialog(QDialog):
    """
    Keyboard shortcuts and help guide dialog (F1).
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("TypeRead Keyboard Shortcuts & Help")
        self.resize(450, 380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Keyboard Shortcuts", self)
        title.setObjectName("sectionHeading")
        layout.addWidget(title)

        shortcuts = [
            ("Ctrl + O", "Open / Import Document"),
            ("Ctrl + B", "Bookmarks & Notes"),
            ("Ctrl + F / Ctrl + K", "Full-Text Search"),
            ("Ctrl + Shift + F", "Toggle Focus Mode (Hide toolbars)"),
            ("Ctrl + Shift + Z", "Toggle Zen Mode (Fullscreen minimal)"),
            ("Ctrl + S", "Force Autosave Flush"),
            ("Esc", "Pause / Resume Typing"),
            ("F1", "Open this Help Cheat Sheet"),
        ]

        card = QFrame(self)
        card.setObjectName("cardFrame")
        c_layout = QVBoxLayout(card)
        for key, desc in shortcuts:
            row = QHBoxLayout()
            k_lbl = QLabel(key, card)
            k_lbl.setFixedWidth(140)
            k_lbl.setStyleSheet("font-weight: bold; color: #58a6ff;")
            d_lbl = QLabel(desc, card)
            row.addWidget(k_lbl)
            row.addWidget(d_lbl)
            c_layout.addLayout(row)

        layout.addWidget(card)

        close_btn = QPushButton("Got it", self)
        close_btn.setObjectName("primaryBtn")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
