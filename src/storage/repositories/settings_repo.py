"""
TypeRead User Settings Repository
Persists application preferences, typography, themes, and typing modes.
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any

from src.contracts.types import (
    UserSettings,
    GeneralSettings,
    AppearanceSettings,
    TypingSettings,
    DocumentSettings,
    PrivacySettings,
    ProcessingProfile,
    ThemeId,
    CaretStyle,
    TypingMode,
    ErrorHandlingMode,
    UserId,
)
from src.storage.db import Database


class SettingsRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_user_settings(self, user_id: str = "default_user") -> UserSettings:
        with self.db.cursor() as cur:
            cur.execute("SELECT * FROM user_settings WHERE user_id = ?;", (user_id,))
            row = cur.fetchone()
            if not row:
                # Default settings
                now_iso = datetime.now(timezone.utc).isoformat()
                return UserSettings(
                    user_id=UserId(user_id),
                    general=GeneralSettings(),
                    appearance=AppearanceSettings(),
                    typing=TypingSettings(),
                    documents=DocumentSettings(),
                    privacy=PrivacySettings(),
                    updated_at=now_iso,
                )
            return self._row_to_user_settings(row)

    def update_user_settings(self, settings: UserSettings) -> UserSettings:
        now_iso = datetime.now(timezone.utc).isoformat()
        g = settings.general
        a = settings.appearance
        t = settings.typing
        d = settings.documents
        p = settings.privacy

        profile_json = json.dumps(d.default_processing_profile.__dict__)

        with self.db.transaction() as cur:
            cur.execute(
                """
                INSERT OR REPLACE INTO user_settings (
                    user_id,
                    startup_behavior, autosave_interval_seconds, confirm_before_delete, backup_storage_directory,
                    theme, font_family, font_size_pt, line_height_em, content_width_px, caret_style, smooth_caret_animation,
                    default_typing_mode, error_handling_mode, sound_keypress, sound_error, sound_complete, adaptive_difficulty_enabled,
                    default_processing_profile_json, auto_run_ocr_if_low_confidence,
                    local_telemetry_enabled, detailed_error_logging, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    settings.user_id,
                    g.startup_behavior,
                    g.autosave_interval_seconds,
                    1 if g.confirm_before_delete else 0,
                    g.backup_storage_directory,
                    a.theme.value,
                    a.font_family,
                    a.font_size_pt,
                    a.line_height_em,
                    a.content_width_px,
                    a.caret_style.value,
                    1 if a.smooth_caret_animation else 0,
                    t.default_mode.value,
                    t.error_handling.value,
                    1 if t.sound_keypress else 0,
                    1 if t.sound_error else 0,
                    1 if t.sound_complete else 0,
                    1 if t.adaptive_difficulty_enabled else 0,
                    profile_json,
                    1 if d.auto_run_ocr_if_low_confidence else 0,
                    1 if p.local_telemetry_enabled else 0,
                    1 if p.detailed_error_logging else 0,
                    now_iso,
                ),
            )

        return self.get_user_settings(str(settings.user_id))

    @staticmethod
    def _row_to_user_settings(r: Any) -> UserSettings:
        general = GeneralSettings(
            startup_behavior=r["startup_behavior"],
            autosave_interval_seconds=r["autosave_interval_seconds"],
            confirm_before_delete=bool(r["confirm_before_delete"]),
            backup_storage_directory=r["backup_storage_directory"],
        )
        appearance = AppearanceSettings(
            theme=ThemeId(r["theme"]),
            font_family=r["font_family"],
            font_size_pt=r["font_size_pt"],
            line_height_em=r["line_height_em"],
            content_width_px=r["content_width_px"],
            caret_style=CaretStyle(r["caret_style"]),
            smooth_caret_animation=bool(r["smooth_caret_animation"]),
        )
        typing_s = TypingSettings(
            default_mode=TypingMode(r["default_typing_mode"]),
            error_handling=ErrorHandlingMode(r["error_handling_mode"]),
            sound_keypress=bool(r["sound_keypress"]),
            sound_error=bool(r["sound_error"]),
            sound_complete=bool(r["sound_complete"]),
            adaptive_difficulty_enabled=bool(r["adaptive_difficulty_enabled"]),
        )
        prof_dict = json.loads(r["default_processing_profile_json"])
        documents_s = DocumentSettings(
            default_processing_profile=ProcessingProfile.from_dict(prof_dict),
            auto_run_ocr_if_low_confidence=bool(r["auto_run_ocr_if_low_confidence"]),
        )
        privacy = PrivacySettings(
            local_telemetry_enabled=bool(r["local_telemetry_enabled"]),
            detailed_error_logging=bool(r["detailed_error_logging"]),
        )
        return UserSettings(
            user_id=UserId(r["user_id"]),
            general=general,
            appearance=appearance,
            typing=typing_s,
            documents=documents_s,
            privacy=privacy,
            updated_at=r["updated_at"],
        )
