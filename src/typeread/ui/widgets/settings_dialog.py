"""
TypeRead Settings Panel & Configuration View
Covers General, Typing, Appearance, Documents, and Privacy categories matching UserSettings.
"""

from __future__ import annotations
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QFrame,
)
from PySide6.QtCore import Qt, Signal

from src.contracts.types import ThemeId, CaretStyle, TypingMode, ErrorHandlingMode


class SettingsDialog(QDialog):
    """
    Settings dialog allowing users to configure application preferences.
    """

    settings_saved = Signal(dict)

    def __init__(self, current_settings: Dict[str, Any], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("TypeRead Preferences & Settings")
        self.resize(600, 480)
        self.settings = current_settings

        self._init_ui()
        self._populate_fields()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        self.tabs = QTabWidget(self)

        # 1. Appearance Tab
        app_tab = QWidget()
        app_form = QFormLayout(app_tab)
        app_form.setSpacing(12)

        self.theme_combo = QComboBox()
        for t in ThemeId:
            self.theme_combo.addItem(t.value.replace("_", " ").title(), t.value)
        app_form.addRow("Color Theme:", self.theme_combo)

        self.font_combo = QComboBox()
        self.font_combo.addItems(["JetBrains Mono", "Fira Code", "Courier New", "Consolas", "Monospace"])
        app_form.addRow("Font Family:", self.font_combo)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 32)
        app_form.addRow("Font Size (pt):", self.font_size_spin)

        self.line_height_spin = QDoubleSpinBox()
        self.line_height_spin.setRange(1.0, 3.0)
        self.line_height_spin.setSingleStep(0.1)
        app_form.addRow("Line Height (em):", self.line_height_spin)

        self.caret_combo = QComboBox()
        for c in CaretStyle:
            self.caret_combo.addItem(c.value.replace("_", " ").title(), c.value)
        app_form.addRow("Caret Style:", self.caret_combo)

        self.tabs.addTab(app_tab, "Appearance")

        # 2. Typing Tab
        typ_tab = QWidget()
        typ_form = QFormLayout(typ_tab)
        typ_form.setSpacing(12)

        self.mode_combo = QComboBox()
        for m in TypingMode:
            self.mode_combo.addItem(m.value.replace("_", " ").title(), m.value)
        typ_form.addRow("Default Typing Mode:", self.mode_combo)

        self.err_combo = QComboBox()
        for e in ErrorHandlingMode:
            self.err_combo.addItem(e.value.replace("_", " ").title(), e.value)
        typ_form.addRow("Error Handling:", self.err_combo)

        self.sound_key_cb = QCheckBox("Sound on keypress")
        typ_form.addRow("Key Audio:", self.sound_key_cb)

        self.sound_err_cb = QCheckBox("Sound on error")
        typ_form.addRow("Error Audio:", self.sound_err_cb)

        self.sound_complete_cb = QCheckBox("Sound on section completion")
        typ_form.addRow("Complete Audio:", self.sound_complete_cb)

        self.adaptive_diff_cb = QCheckBox("Enable adaptive difficulty")
        typ_form.addRow("Adaptive Practice:", self.adaptive_diff_cb)

        self.tabs.addTab(typ_tab, "Typing")

        # 3. General Tab
        gen_tab = QWidget()
        gen_form = QFormLayout(gen_tab)
        gen_form.setSpacing(12)

        self.startup_combo = QComboBox()
        self.startup_combo.addItem("Resume last document", "resume_last")
        self.startup_combo.addItem("Open document library", "open_library")
        gen_form.addRow("Startup Behavior:", self.startup_combo)

        self.autosave_spin = QSpinBox()
        self.autosave_spin.setRange(2, 60)
        gen_form.addRow("Autosave Interval (sec):", self.autosave_spin)

        self.confirm_del_cb = QCheckBox("Confirm before deleting document")
        gen_form.addRow("Confirmations:", self.confirm_del_cb)

        self.tabs.addTab(gen_tab, "General")

        # 4. Privacy & System Tab
        priv_tab = QWidget()
        priv_form = QFormLayout(priv_tab)
        priv_form.setSpacing(12)

        self.telemetry_cb = QCheckBox("Enable local telemetry logs")
        priv_form.addRow("Telemetry:", self.telemetry_cb)

        self.err_log_cb = QCheckBox("Detailed error logging")
        priv_form.addRow("Diagnostic Logs:", self.err_log_cb)

        self.tabs.addTab(priv_tab, "Privacy")

        layout.addWidget(self.tabs)

        # Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.cancel_btn = QPushButton("Cancel", self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save Settings", self)
        self.save_btn.setObjectName("primaryBtn")
        self.save_btn.clicked.connect(self._on_save)
        btn_box.addWidget(self.save_btn)

        layout.addLayout(btn_box)

    def _populate_fields(self) -> None:
        app = self.settings.get("appearance", {})
        idx = self.theme_combo.findData(app.get("theme", "dark"))
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)

        f_idx = self.font_combo.findText(app.get("font_family", "JetBrains Mono"))
        if f_idx >= 0:
            self.font_combo.setCurrentIndex(f_idx)

        self.font_size_spin.setValue(app.get("font_size_pt", 14))
        self.line_height_spin.setValue(app.get("line_height_em", 1.6))

        c_idx = self.caret_combo.findData(app.get("caret_style", "block"))
        if c_idx >= 0:
            self.caret_combo.setCurrentIndex(c_idx)

        # Typing
        typ = self.settings.get("typing", {})
        m_idx = self.mode_combo.findData(typ.get("default_mode", "standard"))
        if m_idx >= 0:
            self.mode_combo.setCurrentIndex(m_idx)

        e_idx = self.err_combo.findData(typ.get("error_handling", "allow_with_backspace"))
        if e_idx >= 0:
            self.err_combo.setCurrentIndex(e_idx)

        self.sound_key_cb.setChecked(typ.get("sound_keypress", False))
        self.sound_err_cb.setChecked(typ.get("sound_error", False))
        self.sound_complete_cb.setChecked(typ.get("sound_complete", True))
        self.adaptive_diff_cb.setChecked(typ.get("adaptive_difficulty_enabled", False))

        # General
        gen = self.settings.get("general", {})
        s_idx = self.startup_combo.findData(gen.get("startup_behavior", "resume_last"))
        if s_idx >= 0:
            self.startup_combo.setCurrentIndex(s_idx)
        self.autosave_spin.setValue(gen.get("autosave_interval_seconds", 10))
        self.confirm_del_cb.setChecked(gen.get("confirm_before_delete", True))

        # Privacy
        priv = self.settings.get("privacy", {})
        self.telemetry_cb.setChecked(priv.get("local_telemetry_enabled", False))
        self.err_log_cb.setChecked(priv.get("detailed_error_logging", True))

    def _on_save(self) -> None:
        updated = {
            "general": {
                "startup_behavior": self.startup_combo.currentData(),
                "autosave_interval_seconds": self.autosave_spin.value(),
                "confirm_before_delete": self.confirm_del_cb.isChecked(),
                "backup_storage_directory": "",
            },
            "appearance": {
                "theme": self.theme_combo.currentData(),
                "font_family": self.font_combo.currentText(),
                "font_size_pt": self.font_size_spin.value(),
                "line_height_em": self.line_height_spin.value(),
                "content_width_px": 840,
                "caret_style": self.caret_combo.currentData(),
                "smooth_caret_animation": True,
            },
            "typing": {
                "default_mode": self.mode_combo.currentData(),
                "error_handling": self.err_combo.currentData(),
                "sound_keypress": self.sound_key_cb.isChecked(),
                "sound_error": self.sound_err_cb.isChecked(),
                "sound_complete": self.sound_complete_cb.isChecked(),
                "adaptive_difficulty_enabled": self.adaptive_diff_cb.isChecked(),
            },
            "documents": {
                "default_processing_profile": {
                    "remove_headers": True,
                    "remove_footers": True,
                    "remove_page_numbers": True,
                    "repair_hyphenation": True,
                    "merge_wrapped_lines": True,
                    "normalize_unicode": True,
                    "normalize_whitespace": True,
                    "exclude_references": True,
                    "exclude_acknowledgments": True,
                    "exclude_preface": False,
                    "min_heading_confidence": 0.65,
                    "enable_local_ocr_fallback": False,
                },
                "auto_run_ocr_if_low_confidence": False,
            },
            "privacy": {
                "local_telemetry_enabled": self.telemetry_cb.isChecked(),
                "detailed_error_logging": self.err_log_cb.isChecked(),
            },
        }
        self.settings_saved.emit(updated)
        self.accept()
