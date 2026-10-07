"""
TypeRead PySide6 Desktop Application Main Window
Primary user interface shell integrating Home, Library, Dual Reader/Typing, Analytics, and Settings.
Fulfills PRD.md specifications, keyboard shortcuts, and crash recovery.
"""

from __future__ import annotations
import os
import sys
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QLabel,
    QPushButton,
    QFrame,
    QSplitter,
    QFileDialog,
    QMessageBox,
    QScrollArea,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
)
from PySide6.QtGui import QKeySequence, QShortcut, QFont
from PySide6.QtCore import Qt, QTimer

from src.contracts.types import ThemeId
from src.typeread.ui.client import UiApiClient
from src.typeread.ui.widgets.theme_manager import ThemeManager
from src.typeread.ui.widgets.reader_widget import DocumentReaderWidget
from src.typeread.ui.widgets.typing_widget import TypingEngineWidget
from src.typeread.ui.widgets.nav_tree import NavTreeWidget
from src.typeread.ui.widgets.analytics_view import AnalyticsView
from src.typeread.ui.widgets.settings_dialog import SettingsDialog
from src.typeread.ui.widgets.import_dialog import ImportPreviewDialog
from src.typeread.ui.widgets.search_dialog import SearchDialog
from src.typeread.ui.widgets.dialogs import (
    CrashRecoveryDialog,
    CompletionDialog,
    BookmarksNotesDialog,
    HelpShortcutsDialog,
)


class MainWindow(QMainWindow):
    """
    Main application window hosting the stacked navigation shell:
    - View 0: Home / Continue View
    - View 1: Library View (with empty state)
    - View 2: Dual Reader + Typing Practice View
    - View 3: Analytics Dashboard View
    """

    def __init__(self, api_client: Optional[UiApiClient] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("TypeRead — Deliberate Typing & Retention")
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)

        self.api = api_client or UiApiClient()
        self.current_theme = "dark"
        self.settings_data: Dict[str, Any] = {}

        # Active session state
        self.active_doc_id: Optional[str] = None
        self.active_doc_title: str = "No Document Loaded"
        self.active_chap_id: Optional[str] = None
        self.active_sec_id: Optional[str] = None
        self.active_para_id: Optional[str] = None
        self.active_session_id: Optional[str] = None

        # Mode toggles
        self.focus_mode = False
        self.zen_mode = False

        self._init_ui()
        self._setup_shortcuts()
        self._load_initial_settings()
        self._check_crash_recovery()

    def _init_ui(self) -> None:
        self.central_widget = QWidget(self)
        self.central_widget.setObjectName("centralWidget")
        self.setCentralWidget(self.central_widget)

        self.root_layout = QVBoxLayout(self.central_widget)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        # 1. Top Navigation & Header Bar
        self.header_bar = QFrame(self.central_widget)
        self.header_bar.setObjectName("headerBar")
        h_layout = QHBoxLayout(self.header_bar)
        h_layout.setContentsMargins(16, 8, 16, 8)
        h_layout.setSpacing(12)

        # App Logo & Branding
        self.logo_lbl = QLabel("TypeRead", self.header_bar)
        f_logo = self.logo_lbl.font()
        f_logo.setPointSize(14)
        f_logo.setBold(True)
        self.logo_lbl.setFont(f_logo)
        h_layout.addWidget(self.logo_lbl)

        # Active Document Title
        self.title_banner_lbl = QLabel("—  No document loaded", self.header_bar)
        self.title_banner_lbl.setObjectName("textMuted")
        h_layout.addWidget(self.title_banner_lbl)
        h_layout.addStretch()

        # View Switcher Buttons
        self.home_btn = QPushButton("Home", self.header_bar)
        self.home_btn.clicked.connect(lambda: self.switch_view(0))
        h_layout.addWidget(self.home_btn)

        self.library_btn = QPushButton("Library", self.header_bar)
        self.library_btn.clicked.connect(lambda: self.switch_view(1))
        h_layout.addWidget(self.library_btn)

        self.practice_btn = QPushButton("Practice", self.header_bar)
        self.practice_btn.clicked.connect(lambda: self.switch_view(2))
        h_layout.addWidget(self.practice_btn)

        self.stats_btn = QPushButton("Stats", self.header_bar)
        self.stats_btn.clicked.connect(lambda: self.switch_view(3))
        h_layout.addWidget(self.stats_btn)

        # Search & Action Buttons
        self.search_btn = QPushButton("🔍 Search", self.header_bar)
        self.search_btn.clicked.connect(self.open_search)
        h_layout.addWidget(self.search_btn)

        self.bookmark_btn = QPushButton("🔖 Bookmark", self.header_bar)
        self.bookmark_btn.clicked.connect(self.open_bookmarks)
        h_layout.addWidget(self.bookmark_btn)

        self.settings_btn = QPushButton("⚙ Settings", self.header_bar)
        self.settings_btn.clicked.connect(self.open_settings)
        h_layout.addWidget(self.settings_btn)

        self.root_layout.addWidget(self.header_bar)

        # 2. Main Stacked Widget
        self.stack = QStackedWidget(self.central_widget)
        self.root_layout.addWidget(self.stack, stretch=1)

        # Build Views
        self._build_home_view()
        self._build_library_view()
        self._build_practice_view()
        self._build_analytics_view()

        # Default to Home View (0)
        self.switch_view(0)

    def _setup_shortcuts(self) -> None:
        """Global keyboard shortcuts specified in PRD Section 46."""
        QShortcut(QKeySequence("Ctrl+O"), self, self.import_document_flow)
        QShortcut(QKeySequence("Ctrl+B"), self, self.open_bookmarks)
        QShortcut(QKeySequence("Ctrl+F"), self, self.open_search)
        QShortcut(QKeySequence("Ctrl+K"), self, self.open_search)
        QShortcut(QKeySequence("Ctrl+Shift+F"), self, self.toggle_focus_mode)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self, self.toggle_zen_mode)
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_progress)
        QShortcut(QKeySequence("F1"), self, self.open_help)

    def _load_initial_settings(self) -> None:
        try:
            self.settings_data = self.api.get_settings()
            app_set = self.settings_data.get("appearance", {})
            self.current_theme = app_set.get("theme", "dark")
            self.apply_theme(self.current_theme)

            # Apply font preferences
            f_fam = app_set.get("font_family", "JetBrains Mono")
            f_size = app_set.get("font_size_pt", 14)
            self.reader_widget.set_font_preferences(f_fam, f_size, app_set.get("line_height_em", 1.6))
            self.typing_widget.set_font_preferences(f_fam, f_size)
            self.typing_widget.set_caret_style(app_set.get("caret_style", "block"))
        except Exception:
            self.apply_theme("dark")

    def apply_theme(self, theme: str) -> None:
        self.current_theme = theme
        qss = ThemeManager.generate_stylesheet(theme)
        self.setStyleSheet(qss)
        self.reader_widget.set_theme(theme)
        self.typing_widget.set_theme(theme)
        self.nav_tree.set_theme(theme)
        self.analytics_view.set_theme(theme)

    # =========================================================================
    # VIEW 0: HOME SCREEN (PRD Section 88)
    # =========================================================================
    def _build_home_view(self) -> None:
        self.home_view = QWidget(self.stack)
        layout = QVBoxLayout(self.home_view)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)

        greeting_lbl = QLabel("Good day. Ready to practice?", self.home_view)
        f_g = greeting_lbl.font()
        f_g.setPointSize(20)
        f_g.setBold(True)
        greeting_lbl.setFont(f_g)
        layout.addWidget(greeting_lbl)

        # Continue Card
        self.continue_frame = QFrame(self.home_view)
        self.continue_frame.setObjectName("cardFrame")
        c_layout = QVBoxLayout(self.continue_frame)
        c_layout.setSpacing(12)

        c_header = QLabel("CONTINUE PRACTICE", self.continue_frame)
        c_header.setObjectName("textMuted")
        c_layout.addWidget(c_header)

        self.continue_title_lbl = QLabel("No active session", self.continue_frame)
        f_t = self.continue_title_lbl.font()
        f_t.setPointSize(16)
        f_t.setBold(True)
        self.continue_title_lbl.setFont(f_t)
        c_layout.addWidget(self.continue_title_lbl)

        self.continue_meta_lbl = QLabel("Select or import a document to begin.", self.continue_frame)
        self.continue_meta_lbl.setObjectName("textMuted")
        c_layout.addWidget(self.continue_meta_lbl)

        self.continue_action_btn = QPushButton("Open Library", self.continue_frame)
        self.continue_action_btn.setObjectName("primaryBtn")
        self.continue_action_btn.clicked.connect(lambda: self.switch_view(1))
        c_layout.addWidget(self.continue_action_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(self.continue_frame)

        # Recent Documents
        layout.addWidget(QLabel("Recent Documents in Library:", self.home_view))
        self.recent_list = QListWidget(self.home_view)
        self.recent_list.setMaximumHeight(200)
        self.recent_list.itemClicked.connect(self._on_recent_doc_selected)
        layout.addWidget(self.recent_list)

        layout.addStretch()
        self.stack.addWidget(self.home_view)

    def _refresh_home_view(self) -> None:
        try:
            docs = self.api.list_documents(limit=5)
            self.recent_list.clear()
            if docs:
                for d in docs:
                    item = QListWidgetItem(self.recent_list)
                    item.setText(f"📖 {d.get('title', 'Untitled')} — {d.get('author', 'Unknown')} ({d.get('word_count', 0):,} words)")
                    item.setData(Qt.ItemDataRole.UserRole, d)

                # Set continue card
                latest = docs[0]
                self.continue_title_lbl.setText(latest.get("title", "Untitled"))
                self.continue_meta_lbl.setText(f"{latest.get('word_count', 0):,} words • Status: Ready to read and type")
                self.continue_action_btn.setText("Continue Practice")
                self.continue_action_btn.clicked.disconnect()
                self.continue_action_btn.clicked.connect(lambda: self.load_document(latest.get("id")))
            else:
                self.continue_title_lbl.setText("Your Library is Empty")
                self.continue_meta_lbl.setText("Import a book or document to start your first session.")
                self.continue_action_btn.setText("Import Document")
                self.continue_action_btn.clicked.disconnect()
                self.continue_action_btn.clicked.connect(self.import_document_flow)
        except Exception:
            pass

    # =========================================================================
    # VIEW 1: LIBRARY SCREEN (PRD Section 28 & 125)
    # =========================================================================
    def _build_library_view(self) -> None:
        self.library_view = QWidget(self.stack)
        layout = QVBoxLayout(self.library_view)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Top Action Bar
        top_bar = QHBoxLayout()
        lib_title = QLabel("DOCUMENT LIBRARY", self.library_view)
        f = lib_title.font()
        f.setPointSize(18)
        f.setBold(True)
        lib_title.setFont(f)
        top_bar.addWidget(lib_title)
        top_bar.addStretch()

        self.add_doc_btn = QPushButton("+ Import Document (Ctrl+O)", self.library_view)
        self.add_doc_btn.setObjectName("primaryBtn")
        self.add_doc_btn.clicked.connect(self.import_document_flow)
        top_bar.addWidget(self.add_doc_btn)
        layout.addLayout(top_bar)

        # Empty State Frame (PRD Section 125)
        self.empty_state_frame = QFrame(self.library_view)
        self.empty_state_frame.setObjectName("cardFrame")
        es_layout = QVBoxLayout(self.empty_state_frame)
        es_layout.setContentsMargins(40, 60, 40, 60)
        es_layout.setSpacing(16)
        es_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        es_title = QLabel("Your library is empty.", self.empty_state_frame)
        f_et = es_title.font()
        f_et.setPointSize(16)
        f_et.setBold(True)
        es_title.setFont(f_et)
        es_layout.addWidget(es_title, alignment=Qt.AlignmentFlag.AlignCenter)

        es_desc = QLabel(
            "Import a book, study PDF, or document\nto begin your first read-and-type session.",
            self.empty_state_frame,
        )
        es_desc.setObjectName("textMuted")
        es_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        es_layout.addWidget(es_desc, alignment=Qt.AlignmentFlag.AlignCenter)

        es_btn = QPushButton("Add Document", self.empty_state_frame)
        es_btn.setObjectName("primaryBtn")
        es_btn.clicked.connect(self.import_document_flow)
        es_layout.addWidget(es_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.empty_state_frame)

        # Documents List Widget (Populated State)
        self.docs_list = QListWidget(self.library_view)
        self.docs_list.itemDoubleClicked.connect(self._on_doc_item_double_clicked)
        layout.addWidget(self.docs_list)

        self.stack.addWidget(self.library_view)

    def _refresh_library_view(self) -> None:
        try:
            docs = self.api.list_documents()
            if not docs:
                self.empty_state_frame.setVisible(True)
                self.docs_list.setVisible(False)
            else:
                self.empty_state_frame.setVisible(False)
                self.docs_list.setVisible(True)
                self.docs_list.clear()

                for d in docs:
                    item = QListWidgetItem(self.docs_list)
                    title = d.get("title", "Untitled")
                    author = d.get("author", "Unknown")
                    fmt = d.get("source_format", "txt").upper()
                    words = d.get("word_count", 0)
                    item.setText(f"📘 {title}  —  {author}  [{fmt} | {words:,} words]")
                    item.setData(Qt.ItemDataRole.UserRole, d)
        except Exception as ex:
            self.empty_state_frame.setVisible(True)
            self.docs_list.setVisible(False)

    def _on_doc_item_double_clicked(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self.load_document(data.get("id"))

    def _on_recent_doc_selected(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self.load_document(data.get("id"))

    # =========================================================================
    # VIEW 2: DUAL READER + TYPING PRACTICE (PRD Section 30)
    # =========================================================================
    def _build_practice_view(self) -> None:
        self.practice_view = QWidget(self.stack)
        p_layout = QHBoxLayout(self.practice_view)
        p_layout.setContentsMargins(16, 16, 16, 16)
        p_layout.setSpacing(16)

        # Left: Navigation Tree Sidebar
        self.nav_tree = NavTreeWidget(self.practice_view)
        self.nav_tree.setFixedWidth(280)
        self.nav_tree.section_selected.connect(self._on_section_selected)
        p_layout.addWidget(self.nav_tree)

        # Center Splitter: Top = Reading Panel, Bottom = Typing Panel
        self.center_splitter = QSplitter(Qt.Orientation.Vertical, self.practice_view)

        self.reader_widget = DocumentReaderWidget(self.center_splitter)
        self.center_splitter.addWidget(self.reader_widget)

        self.typing_widget = TypingEngineWidget(self.center_splitter)
        self.typing_widget.keystroke_processed.connect(self._on_keystroke_processed)
        self.typing_widget.session_completed.connect(self._on_session_completed)
        self.center_splitter.addWidget(self.typing_widget)

        # Equal proportion split
        self.center_splitter.setSizes([320, 360])
        p_layout.addWidget(self.center_splitter, stretch=1)

        self.stack.addWidget(self.practice_view)

    # =========================================================================
    # VIEW 3: ANALYTICS DASHBOARD (PRD Section 48)
    # =========================================================================
    def _build_analytics_view(self) -> None:
        self.analytics_view = AnalyticsView(self.stack)
        self.analytics_view.refresh_btn.clicked.connect(self._refresh_analytics_view)
        self.analytics_view.drill_btn.clicked.connect(self._on_generate_drill)
        self.stack.addWidget(self.analytics_view)

    def _refresh_analytics_view(self) -> None:
        try:
            overview = self.api.get_analytics_overview()
            weak_keys = self.api.get_weak_keys(10)
            trends = self.api.get_analytics_trends(30)
            self.analytics_view.display_data(overview, weak_keys, trends)
        except Exception:
            pass

    def _on_generate_drill(self) -> None:
        try:
            drill = self.api.generate_weak_key_drill(word_count=80, document_id=self.active_doc_id)
            passage = drill.get("generated_passage", "")
            if passage:
                self.switch_view(2)  # Switch to practice view
                self.title_banner_lbl.setText("—  Targeted Weak-Key Drill")
                self.reader_widget.load_content(passage)
                self.typing_widget.set_content(passage)
        except Exception as ex:
            QMessageBox.warning(self, "Drill Generator", f"Could not generate drill: {str(ex)}")

    # =========================================================================
    # NAVIGATION & VIEW SWITCHING
    # =========================================================================
    def switch_view(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        if index == 0:
            self._refresh_home_view()
        elif index == 1:
            self._refresh_library_view()
        elif index == 2:
            self.typing_widget.canvas.setFocus()
        elif index == 3:
            self._refresh_analytics_view()

    # =========================================================================
    # DOCUMENT INGESTION FLOW (PRD Section 29, 73, 74)
    # =========================================================================
    def import_document_flow(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Document to Import",
            "",
            "Documents (*.pdf *.epub *.docx *.txt *.md *.html);;All Files (*)",
        )
        if not file_path:
            return

        try:
            preview = self.api.import_document(file_path=file_path)
            dlg = ImportPreviewDialog(preview, self)
            dlg.commit_confirmed.connect(self._commit_document_flow)
            dlg.exec()
        except Exception as ex:
            QMessageBox.critical(self, "Import Error", f"Failed to parse document:\n{str(ex)}")

    def _commit_document_flow(self, doc_id: str, update_req: Dict[str, Any]) -> None:
        try:
            doc = self.api.commit_document(doc_id, update_req)
            self._refresh_library_view()
            self.load_document(doc_id)
        except Exception as ex:
            QMessageBox.critical(self, "Commit Error", f"Failed to commit document:\n{str(ex)}")

    # =========================================================================
    # DOCUMENT LOADING & SESSION MANAGEMENT
    # =========================================================================
    def load_document(self, document_id: str) -> None:
        try:
            doc = self.api.get_document(document_id)
            structure = self.api.get_document_structure(document_id)

            self.active_doc_id = document_id
            self.active_doc_title = doc.get("title", "Document")
            self.title_banner_lbl.setText(f"—  {self.active_doc_title}")

            self.nav_tree.load_structure(structure)

            # Load first section
            chapters = structure.get("chapters", [])
            if chapters and chapters[0].get("sections"):
                chap_id = chapters[0]["id"]
                sec_id = chapters[0]["sections"][0]["id"]
                self.load_section(chap_id, sec_id)

            self.switch_view(2)  # Switch to practice view
        except Exception as ex:
            QMessageBox.critical(self, "Load Document", f"Could not load document:\n{str(ex)}")

    def load_section(self, chapter_id: str, section_id: str, initial_offset: int = 0) -> None:
        if not self.active_doc_id:
            return

        try:
            content = self.api.get_section_content(self.active_doc_id, section_id)
            paragraphs = content.get("paragraphs", [])
            if not paragraphs:
                return

            self.active_chap_id = chapter_id
            self.active_sec_id = section_id
            self.active_para_id = paragraphs[0].get("id")

            # Extract representations (supporting both OpenAPI flattened response and nested dict)
            p0 = paragraphs[0]
            rep = p0.get("representations", {})
            display_text = p0.get("displayText") or p0.get("display_text") or rep.get("display_text") or p0.get("sourceText", "")
            typing_text = p0.get("typingText") or p0.get("typing_text") or rep.get("typing_text") or display_text
            offset_map = p0.get("typingToDisplayIndices") or rep.get("offset_map", {}).get("typing_to_display_indices", [])

            self.reader_widget.load_content(display_text, offset_map)

            # Start or resume session in API
            session = self.api.start_session(
                document_id=self.active_doc_id,
                chapter_id=chapter_id,
                section_id=section_id,
            )
            self.active_session_id = session.get("id")

            # Load into typing widget
            self.typing_widget.set_content(typing_text, initial_offset=initial_offset)
            self.nav_tree.select_section(section_id)

        except Exception as ex:
            QMessageBox.critical(self, "Load Section", f"Could not load section content:\n{str(ex)}")

    def _on_section_selected(self, chapter_id: str, section_id: str) -> None:
        self.save_progress()
        self.load_section(chapter_id, section_id)

    def _on_keystroke_processed(self, current_pos: int, is_correct: bool) -> None:
        # Synchronize reader display highlight
        self.reader_widget.highlight_progress(current_pos)

    def _on_session_completed(self, final_metrics: Any) -> None:
        if self.active_session_id:
            try:
                # Flush pending strokes and complete in API
                strokes = [
                    {
                        "timestamp_ms": s.timestamp_ms,
                        "key": s.key,
                        "expected_char": s.expected_char,
                        "position": s.position,
                        "is_backspace": s.is_backspace,
                    }
                    for s in self.typing_widget.drain_keystrokes()
                ]
                if strokes:
                    self.api.submit_keystrokes(self.active_session_id, strokes)
                self.api.complete_session(self.active_session_id)
            except Exception:
                pass

        dlg = CompletionDialog(
            title=f"{self.active_doc_title}",
            avg_wpm=getattr(final_metrics, "net_wpm", 0.0),
            accuracy_pct=getattr(final_metrics, "accuracy_pct", 100.0),
            total_seconds=getattr(final_metrics, "active_seconds", 0),
            words_typed=getattr(final_metrics, "correct_keystrokes", 0) // 5,
            parent=self,
        )
        dlg.view_stats_requested.connect(lambda: self.switch_view(3))
        dlg.restart_requested.connect(self.typing_widget.restart_session)
        dlg.library_requested.connect(lambda: self.switch_view(1))
        dlg.exec()

    # =========================================================================
    # AUTOSAVE & RESUME
    # =========================================================================
    def save_progress(self) -> None:
        """Autosaves reading position pointer and flushes keystrokes without blocking."""
        if not self.active_doc_id or not self.active_session_id:
            return

        strokes = [
            {
                "timestamp_ms": s.timestamp_ms,
                "key": s.key,
                "expected_char": s.expected_char,
                "position": s.position,
                "is_backspace": s.is_backspace,
            }
            for s in self.typing_widget.drain_keystrokes()
        ]
        try:
            if strokes:
                self.api.submit_keystrokes(self.active_session_id, strokes)

            # Update reading progress pointer
            pointer = {
                "documentId": self.active_doc_id,
                "chapterId": self.active_chap_id or "",
                "sectionId": self.active_sec_id or "",
                "paragraphId": self.active_para_id or "",
                "characterOffset": self.typing_widget.canvas.current_index,
            }
            self.api.update_document_progress(self.active_doc_id, pointer)
        except Exception:
            pass

    def _check_crash_recovery(self) -> None:
        """Checks for unclosed sessions on startup per ARCH_DECISIONS 4.3."""
        try:
            active_sess = self.api.get_active_session()
            if active_sess and not active_sess.get("completed", False):
                doc_id = active_sess.get("document_id")
                doc = self.api.get_document(doc_id)
                prog = self.api.get_document_progress(doc_id)

                dlg = CrashRecoveryDialog(
                    doc_title=doc.get("title", "Document"),
                    chapter_title="Saved Chapter",
                    progress_pct=prog.get("completion_percentage", 0.0),
                    parent=self,
                )
                if dlg.exec():
                    self.load_document(doc_id)
                else:
                    self.api.abort_session(active_sess.get("id"))
        except Exception:
            pass

    # =========================================================================
    # DIALOG ACTIONS & SHORTCUT HANDLERS
    # =========================================================================
    def open_search(self) -> None:
        dlg = SearchDialog(api_client=self.api, current_doc_id=self.active_doc_id, parent=self)
        dlg.result_selected.connect(self._on_search_jump)
        dlg.exec()

    def _on_search_jump(self, doc_id: str, chap_id: str, sec_id: str, offset: int) -> None:
        if self.active_doc_id != doc_id:
            self.load_document(doc_id)
        self.load_section(chap_id, sec_id, initial_offset=offset)
        self.switch_view(2)

    def open_bookmarks(self) -> None:
        dlg = BookmarksNotesDialog(
            api_client=self.api,
            doc_id=self.active_doc_id,
            chap_id=self.active_chap_id,
            sec_id=self.active_sec_id,
            para_id=self.active_para_id,
            offset=self.typing_widget.canvas.current_index,
            parent=self,
        )
        dlg.bookmark_jumped.connect(lambda d, c, s, p, o: self.load_section(c, s, initial_offset=o))
        dlg.exec()

    def open_settings(self) -> None:
        dlg = SettingsDialog(current_settings=self.settings_data, parent=self)
        dlg.settings_saved.connect(self._on_settings_saved)
        dlg.exec()

    def _on_settings_saved(self, updated: Dict[str, Any]) -> None:
        try:
            self.settings_data = self.api.update_settings(updated)
            app = self.settings_data.get("appearance", {})
            self.apply_theme(app.get("theme", "dark"))
            self.reader_widget.set_font_preferences(
                app.get("font_family", "JetBrains Mono"),
                app.get("font_size_pt", 14),
                app.get("line_height_em", 1.6),
            )
            self.typing_widget.set_font_preferences(
                app.get("font_family", "JetBrains Mono"),
                app.get("font_size_pt", 14),
            )
            self.typing_widget.set_caret_style(app.get("caret_style", "block"))
        except Exception as ex:
            QMessageBox.critical(self, "Settings Error", f"Failed to save settings: {str(ex)}")

    def open_help(self) -> None:
        dlg = HelpShortcutsDialog(self)
        dlg.exec()

    def toggle_focus_mode(self) -> None:
        """Hides headers and sidebars for distraction-free reading (Ctrl+Shift+F)."""
        self.focus_mode = not self.focus_mode
        self.header_bar.setVisible(not self.focus_mode)
        self.nav_tree.setVisible(not self.focus_mode)
        if self.focus_mode:
            self.switch_view(2)

    def toggle_zen_mode(self) -> None:
        """Fullscreen minimal typing reader (Ctrl+Shift+Z)."""
        self.zen_mode = not self.zen_mode
        if self.zen_mode:
            self.showFullScreen()
            self.header_bar.setVisible(False)
            self.nav_tree.setVisible(False)
            self.switch_view(2)
        else:
            self.showNormal()
            self.header_bar.setVisible(True)
            self.nav_tree.setVisible(True)


def run_app() -> None:
    """Helper entry point for launching TypeRead PySide6 GUI."""
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
