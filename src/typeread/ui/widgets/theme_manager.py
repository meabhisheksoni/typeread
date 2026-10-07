"""
TypeRead Theme Manager & Styling Engine
Provides high-fidelity QSS stylesheets for Light, Dark, Sepia, Paper, High Contrast, and Midnight.
Strictly matches ThemeId and AppearanceSettings.
"""

from __future__ import annotations
from typing import Dict, Any

from src.contracts.types import ThemeId


THEME_PALETTES = {
    ThemeId.DARK.value: {
        "bg_primary": "#121417",
        "bg_secondary": "#1a1d24",
        "bg_elevated": "#232731",
        "bg_active": "#2b303c",
        "text_primary": "#e6edf3",
        "text_secondary": "#8b949e",
        "text_muted": "#6e7681",
        "accent": "#58a6ff",
        "accent_hover": "#79b8ff",
        "border": "#30363d",
        "correct": "#3fb950",
        "incorrect": "#f85149",
        "cursor": "#58a6ff",
        "highlight": "rgba(88, 166, 255, 0.2)",
    },
    ThemeId.LIGHT.value: {
        "bg_primary": "#ffffff",
        "bg_secondary": "#f6f8fa",
        "bg_elevated": "#eaedf1",
        "bg_active": "#d0d7de",
        "text_primary": "#1f2328",
        "text_secondary": "#57606a",
        "text_muted": "#8c959f",
        "accent": "#0969da",
        "accent_hover": "#218bff",
        "border": "#d0d7de",
        "correct": "#1a7f37",
        "incorrect": "#cf222e",
        "cursor": "#0969da",
        "highlight": "rgba(9, 105, 218, 0.15)",
    },
    ThemeId.SEPIA.value: {
        "bg_primary": "#fbf0d9",
        "bg_secondary": "#f4e4c1",
        "bg_elevated": "#ecd6a8",
        "bg_active": "#e2c790",
        "text_primary": "#433422",
        "text_secondary": "#705d47",
        "text_muted": "#96836c",
        "accent": "#9f5f22",
        "accent_hover": "#b8702c",
        "border": "#ddc79f",
        "correct": "#2d7a3d",
        "incorrect": "#a83232",
        "cursor": "#9f5f22",
        "highlight": "rgba(159, 95, 34, 0.18)",
    },
    ThemeId.PAPER.value: {
        "bg_primary": "#f7f7f5",
        "bg_secondary": "#ecece8",
        "bg_elevated": "#deded8",
        "bg_active": "#cecec6",
        "text_primary": "#2b2b2b",
        "text_secondary": "#636363",
        "text_muted": "#8f8f8f",
        "accent": "#3a6073",
        "accent_hover": "#4a778e",
        "border": "#d5d5ce",
        "correct": "#2b7c4a",
        "incorrect": "#a8332a",
        "cursor": "#3a6073",
        "highlight": "rgba(58, 96, 115, 0.15)",
    },
    ThemeId.HIGH_CONTRAST.value: {
        "bg_primary": "#000000",
        "bg_secondary": "#101010",
        "bg_elevated": "#202020",
        "bg_active": "#353535",
        "text_primary": "#ffffff",
        "text_secondary": "#ffff00",
        "text_muted": "#cccccc",
        "accent": "#00ffff",
        "accent_hover": "#80ffff",
        "border": "#ffffff",
        "correct": "#00ff00",
        "incorrect": "#ff0000",
        "cursor": "#00ffff",
        "highlight": "rgba(0, 255, 255, 0.3)",
    },
    ThemeId.MIDNIGHT.value: {
        "bg_primary": "#070b19",
        "bg_secondary": "#0d152d",
        "bg_elevated": "#142042",
        "bg_active": "#1d2e5e",
        "text_primary": "#dce5ff",
        "text_secondary": "#8c9dc3",
        "text_muted": "#5a6e9a",
        "accent": "#738aff",
        "accent_hover": "#98a9ff",
        "border": "#213261",
        "correct": "#38d39f",
        "incorrect": "#ff5c77",
        "cursor": "#738aff",
        "highlight": "rgba(115, 138, 255, 0.25)",
    },
}


class ThemeManager:
    @staticmethod
    def get_palette(theme: str = "dark") -> Dict[str, str]:
        return THEME_PALETTES.get(theme, THEME_PALETTES[ThemeId.DARK.value])

    @classmethod
    def generate_stylesheet(
        cls,
        theme: str = "dark",
        font_family: str = "JetBrains Mono",
        font_size_pt: int = 14,
    ) -> str:
        palette = cls.get_palette(theme)

        return f"""
        * {{
            font-family: "{font_family}", "Fira Code", monospace;
            font-size: {font_size_pt}pt;
            color: {palette["text_primary"]};
        }}

        QMainWindow, QDialog, QWidget#centralWidget {{
            background-color: {palette["bg_primary"]};
        }}

        QWidget {{
            background-color: transparent;
        }}

        QFrame#cardFrame {{
            background-color: {palette["bg_secondary"]};
            border: 1px solid {palette["border"]};
            border-radius: 8px;
            padding: 16px;
        }}

        QFrame#headerBar {{
            background-color: {palette["bg_secondary"]};
            border-bottom: 1px solid {palette["border"]};
            padding: 8px 16px;
        }}

        QFrame#statusBar {{
            background-color: {palette["bg_secondary"]};
            border-top: 1px solid {palette["border"]};
            padding: 6px 16px;
        }}

        QPushButton {{
            background-color: {palette["bg_elevated"]};
            color: {palette["text_primary"]};
            border: 1px solid {palette["border"]};
            border-radius: 6px;
            padding: 6px 14px;
            font-weight: 500;
        }}

        QPushButton:hover {{
            background-color: {palette["bg_active"]};
            border-color: {palette["accent"]};
        }}

        QPushButton:pressed {{
            background-color: {palette["accent"]};
            color: #ffffff;
        }}

        QPushButton#primaryBtn {{
            background-color: {palette["accent"]};
            color: #ffffff;
            font-weight: 600;
            border: none;
        }}

        QPushButton#primaryBtn:hover {{
            background-color: {palette["accent_hover"]};
        }}

        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {palette["bg_secondary"]};
            border: 1px solid {palette["border"]};
            border-radius: 6px;
            padding: 8px;
            color: {palette["text_primary"]};
            selection-background-color: {palette["accent"]};
        }}

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 1px solid {palette["accent"]};
        }}

        QTreeView, QListWidget, QTableWidget {{
            background-color: {palette["bg_secondary"]};
            border: 1px solid {palette["border"]};
            border-radius: 6px;
            alternate-background-color: {palette["bg_elevated"]};
            outline: none;
        }}

        QTreeView::item, QListWidget::item {{
            padding: 6px 8px;
            border-radius: 4px;
        }}

        QTreeView::item:hover, QListWidget::item:hover {{
            background-color: {palette["bg_elevated"]};
        }}

        QTreeView::item:selected, QListWidget::item:selected {{
            background-color: {palette["bg_active"]};
            color: {palette["accent"]};
        }}

        QProgressBar {{
            background-color: {palette["bg_elevated"]};
            border: none;
            border-radius: 4px;
            text-align: center;
            font-size: {max(9, font_size_pt - 3)}pt;
            color: {palette["text_secondary"]};
            height: 10px;
        }}

        QProgressBar::chunk {{
            background-color: {palette["accent"]};
            border-radius: 4px;
        }}

        QScrollBar:vertical {{
            background: {palette["bg_secondary"]};
            width: 8px;
            border-radius: 4px;
        }}

        QScrollBar::handle:vertical {{
            background: {palette["border"]};
            min-height: 20px;
            border-radius: 4px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {palette["accent"]};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QLabel#metricValue {{
            font-size: {font_size_pt + 8}pt;
            font-weight: bold;
            color: {palette["accent"]};
        }}

        QLabel#metricLabel {{
            font-size: {max(8, font_size_pt - 4)}pt;
            color: {palette["text_secondary"]};
            text-transform: uppercase;
        }}

        QLabel#sectionHeading {{
            font-size: {font_size_pt + 4}pt;
            font-weight: bold;
            color: {palette["text_primary"]};
        }}

        QLabel#textMuted {{
            color: {palette["text_muted"]};
        }}
        """
