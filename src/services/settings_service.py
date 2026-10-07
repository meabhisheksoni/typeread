"""
TypeRead Settings Service
Manages user preferences and display settings.
"""

from __future__ import annotations

from src.contracts.types import UserSettings
from src.storage.repositories.settings_repo import SettingsRepository


class SettingsService:
    def __init__(self, settings_repo: SettingsRepository):
        self.settings_repo = settings_repo

    def get_settings(self, user_id: str = "default_user") -> UserSettings:
        return self.settings_repo.get_user_settings(user_id=user_id)

    def update_settings(self, settings: UserSettings) -> UserSettings:
        return self.settings_repo.update_user_settings(settings=settings)
