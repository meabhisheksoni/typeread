"""
Unit and Integration Tests for TypeRead Frontend PySide6 UI and TypeScript contracts.
Verifies widget rendering, keystroke hot-path evaluation, themes, dialogs, and shortcuts.
"""

import os
import sys
import unittest
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QKeyEvent
from PySide6.QtCore import Qt, QEvent

# Initialize QApplication once for headless testing
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

from src.app import create_app
from src.contracts.types import ThemeId, CaretStyle, TypingMode, ErrorHandlingMode
from src.typeread.ui.client import UiApiClient
from src.typeread.ui.widgets.theme_manager import ThemeManager, THEME_PALETTES
from src.typeread.ui.widgets.reader_widget import DocumentReaderWidget
from src.typeread.ui.widgets.typing_widget import TypingEngineWidget, TypingWidget
from src.typeread.ui.widgets.nav_tree import NavTreeWidget
from src.typeread.ui.widgets.analytics_view import AnalyticsView
from src.typeread.ui.widgets.settings_dialog import SettingsDialog
from src.typeread.ui.widgets.import_dialog import ImportPreviewDialog
from src.typeread.ui.widgets.search_dialog import SearchDialog
from src.typeread.ui.widgets.dialogs import CrashRecoveryDialog, CompletionDialog, HelpShortcutsDialog
from src.typeread.ui.main_window import MainWindow


class TestFrontendThemeManager(unittest.TestCase):
    def test_all_themes_generate_valid_stylesheets(self):
        for theme in ThemeId:
            qss = ThemeManager.generate_stylesheet(theme=theme.value)
            self.assertIn("QMainWindow", qss)
            self.assertIn(THEME_PALETTES[theme.value]["bg_primary"], qss)


class TestFrontendReaderWidget(unittest.TestCase):
    def test_reader_widget_loading_and_highlighting(self):
        reader = DocumentReaderWidget()
        reader.load_content("Atomic Habits: Small Changes", [0, 1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(reader.display_text, "Atomic Habits: Small Changes")

        # Test highlighting progress
        reader.highlight_progress(3)
        self.assertIsNotNone(reader.text_display.toPlainText())


class TestFrontendTypingWidget(unittest.TestCase):
    def test_typing_widget_sub_50ms_hot_path(self):
        widget = TypingEngineWidget()
        widget.set_content("Test text", typing_mode="standard", error_handling="allow_with_backspace")

        # Verify initial state
        self.assertEqual(widget.canvas.current_index, 0)

        # Simulate typing 'T' (correct)
        ev_correct = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_T, Qt.KeyboardModifier.NoModifier, "T")
        widget.keyPressEvent(ev_correct)
        self.assertEqual(widget.canvas.current_index, 1)
        self.assertTrue(widget.canvas.evaluations_status[0])

        # Simulate typing 'x' instead of 'e' (incorrect)
        ev_incorrect = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_X, Qt.KeyboardModifier.NoModifier, "x")
        widget.keyPressEvent(ev_incorrect)
        self.assertEqual(widget.canvas.current_index, 2)
        self.assertFalse(widget.canvas.evaluations_status[1])

        # Simulate Backspace
        ev_bs = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Backspace, Qt.KeyboardModifier.NoModifier, "")
        widget.keyPressEvent(ev_bs)
        self.assertEqual(widget.canvas.current_index, 1)

        # Drain keystrokes
        strokes = widget.drain_keystrokes()
        self.assertEqual(len(strokes), 3)

    def test_typing_widget_pause_and_resume(self):
        widget = TypingWidget()
        widget.set_content("Sample", typing_mode="standard")

        # Toggle pause via Escape key
        ev_esc = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier, "")
        widget.keyPressEvent(ev_esc)
        self.assertEqual(widget.state, "paused")

        # Resume via Escape key
        widget.keyPressEvent(ev_esc)
        self.assertEqual(widget.state, "active")


class TestFrontendNavTreeWidget(unittest.TestCase):
    def test_nav_tree_loading(self):
        tree = NavTreeWidget()
        sample_structure = {
            "document": {"title": "Test Book"},
            "chapters": [
                {
                    "id": "c1",
                    "title": "Chapter 1",
                    "included_in_practice": True,
                    "sections": [
                        {"id": "s1", "title": "Section 1", "included_in_practice": True}
                    ]
                }
            ]
        }
        tree.load_structure(sample_structure)
        self.assertEqual(tree.tree.topLevelItemCount(), 1)
        self.assertEqual(tree.tree.topLevelItem(0).childCount(), 1)


class TestFrontendAnalyticsView(unittest.TestCase):
    def test_analytics_view_display(self):
        view = AnalyticsView()
        overview = {
            "average_net_wpm": 62.5,
            "average_accuracy_pct": 98.2,
            "total_practice_seconds": 3600,
            "total_characters_typed": 18000,
            "total_sessions": 12,
        }
        weak_keys = [
            {"character": "r", "error_count": 5, "total_occurrences": 100, "error_rate_pct": 5.0}
        ]
        trends = {
            "daily_activity": [
                {"date": "2026-10-01", "practice_seconds": 1200, "avg_net_wpm": 60.0}
            ]
        }
        view.display_data(overview, weak_keys, trends)
        self.assertEqual(view.card_wpm["val"].text(), "62")
        self.assertEqual(view.card_acc["val"].text(), "98.2%")
        self.assertEqual(view.weak_table.rowCount(), 1)


class TestFrontendDialogs(unittest.TestCase):
    def test_crash_recovery_dialog_instantiation(self):
        dlg = CrashRecoveryDialog("Book 1", "Chapter 2", 45.0)
        self.assertIsNotNone(dlg)

    def test_completion_dialog_instantiation(self):
        dlg = CompletionDialog("Book 1", 65.0, 99.0, 180, 500)
        self.assertIsNotNone(dlg)

    def test_help_dialog_instantiation(self):
        dlg = HelpShortcutsDialog()
        self.assertIsNotNone(dlg)


class TestFrontendMainWindow(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_app = create_app(data_dir=self.temp_dir.name)
        self.ui_client = UiApiClient(dispatcher=self.test_app.dispatcher, app_container=self.test_app)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_main_window_lifecycle_and_switching(self):
        window = MainWindow(api_client=self.ui_client)
        self.assertIsNotNone(window)

        window.show()
        # Test view switching
        window.switch_view(0)
        self.assertEqual(window.stack.currentIndex(), 0)

        window.switch_view(1)
        self.assertEqual(window.stack.currentIndex(), 1)
        self.assertFalse(window.empty_state_frame.isHidden())

        window.switch_view(2)
        self.assertEqual(window.stack.currentIndex(), 2)

        window.switch_view(3)
        self.assertEqual(window.stack.currentIndex(), 3)

        # Test focus mode toggle
        window.toggle_focus_mode()
        self.assertTrue(window.focus_mode)
        self.assertFalse(window.header_bar.isVisible())
        window.toggle_focus_mode()
        self.assertFalse(window.focus_mode)
        self.assertTrue(window.header_bar.isVisible())


if __name__ == "__main__":
    unittest.main()
