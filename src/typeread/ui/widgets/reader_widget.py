"""
TypeRead Upper Document Reader Display Widget
Displays formatted source text and synchronously highlights the active sentence, word, and character.
"""

from __future__ import annotations
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont
from PySide6.QtCore import Qt

from src.typeread.ui.widgets.theme_manager import ThemeManager


class DocumentReaderWidget(QWidget):
    """
    Upper panel displaying the original source/display text.
    Provides visual reading context while the user practices typing below.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.theme = "dark"
        self.font_family = "JetBrains Mono"
        self.font_size_pt = 14
        self.line_height_em = 1.6

        self.display_text = ""
        self.typing_to_display_indices: List[int] = []

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.header_label = QLabel("SOURCE TEXT / READING VIEW", self)
        self.header_label.setObjectName("textMuted")
        f = self.header_label.font()
        f.setPointSize(10)
        f.setBold(True)
        self.header_label.setFont(f)
        layout.addWidget(self.header_label)

        self.text_display = QTextEdit(self)
        self.text_display.setReadOnly(True)
        self.text_display.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.text_display.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        layout.addWidget(self.text_display)

        self._apply_style()

    def set_theme(self, theme: str) -> None:
        self.theme = theme
        self._apply_style()

    def set_font_preferences(self, family: str, size_pt: int, line_height: float) -> None:
        self.font_family = family
        self.font_size_pt = size_pt
        self.line_height_em = line_height
        self._apply_style()

    def _apply_style(self) -> None:
        palette = ThemeManager.get_palette(self.theme)
        font = QFont(self.font_family, self.font_size_pt)
        self.text_display.setFont(font)
        self.text_display.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: {palette["bg_secondary"]};
                color: {palette["text_primary"]};
                border: 1px solid {palette["border"]};
                border-radius: 8px;
                padding: 18px;
                line-height: {int(self.line_height_em * 100)}%;
            }}
            """
        )

    def load_content(self, display_text: str, offset_map: Optional[List[int]] = None) -> None:
        self.display_text = display_text
        self.typing_to_display_indices = offset_map or list(range(len(display_text)))
        self.text_display.setPlainText(display_text)
        self.highlight_progress(0)

    def highlight_progress(self, typing_offset: int) -> None:
        """
        Highlights text in display_text corresponding to current typing offset.
        - Already read: text_muted or green
        - Current char/word: highlighted with accent
        - Remaining: text_primary
        """
        if not self.display_text:
            return

        disp_index = (
            self.typing_to_display_indices[typing_offset]
            if typing_offset < len(self.typing_to_display_indices)
            else len(self.display_text)
        )

        palette = ThemeManager.get_palette(self.theme)
        cursor = QTextCursor(self.text_display.document())

        # Reset formatting
        cursor.select(QTextCursor.SelectionType.Document)
        default_fmt = QTextCharFormat()
        default_fmt.setForeground(QColor(palette["text_primary"]))
        default_fmt.setBackground(Qt.GlobalColor.transparent)
        cursor.setCharFormat(default_fmt)

        # Highlight completed portion
        if disp_index > 0:
            cursor.setPosition(0)
            cursor.setPosition(disp_index, QTextCursor.MoveMode.KeepAnchor)
            done_fmt = QTextCharFormat()
            done_fmt.setForeground(QColor(palette["text_muted"]))
            cursor.setCharFormat(done_fmt)

        # Highlight active character
        if disp_index < len(self.display_text):
            cursor.setPosition(disp_index)
            cursor.setPosition(disp_index + 1, QTextCursor.MoveMode.KeepAnchor)
            active_fmt = QTextCharFormat()
            active_fmt.setForeground(QColor(palette["text_primary"]))
            active_fmt.setBackground(QColor(palette["accent"]))
            cursor.setCharFormat(active_fmt)

            # Ensure cursor visibility (smooth scroll)
            self.text_display.setTextCursor(cursor)
            self.text_display.ensureCursorVisible()
