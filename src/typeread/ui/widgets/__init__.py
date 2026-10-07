"""
TypeRead UI Widgets Package
"""

from src.typeread.ui.widgets.theme_manager import ThemeManager
from src.typeread.ui.widgets.reader_widget import DocumentReaderWidget
from src.typeread.ui.widgets.typing_widget import TypingEngineWidget, TypingWidget
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

__all__ = [
    "ThemeManager",
    "DocumentReaderWidget",
    "TypingEngineWidget",
    "TypingWidget",
    "NavTreeWidget",
    "AnalyticsView",
    "SettingsDialog",
    "ImportPreviewDialog",
    "SearchDialog",
    "CrashRecoveryDialog",
    "CompletionDialog",
    "BookmarksNotesDialog",
    "HelpShortcutsDialog",
]
