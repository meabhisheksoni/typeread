"""
TypeRead Core Domain Error Definitions & Exceptions
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from src.contracts.types import AppError, ErrorCode, ErrorDetail


class AppErrorException(Exception):
    """
    Base domain exception adhering strictly to api.json error contract.
    """
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = 400,
        recoverable: bool = False,
        details: Optional[List[ErrorDetail]] = None,
        suggested_action: Optional[str] = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.recoverable = recoverable
        self.details = details or []
        self.suggested_action = suggested_action
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_app_error(self) -> AppError:
        return AppError(
            code=self.code,
            message=self.message,
            timestamp=self.timestamp,
            recoverable=self.recoverable,
            details=self.details,
            suggested_action=self.suggested_action,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code.value if hasattr(self.code, "value") else str(self.code),
            "message": self.message,
            "timestamp": self.timestamp,
            "recoverable": self.recoverable,
            "details": [
                {
                    "message": d.message,
                    "field": d.field,
                    "constraint": d.constraint,
                }
                for d in self.details
            ],
            "suggestedAction": self.suggested_action,
        }

    @classmethod
    def not_found(
        cls,
        code: ErrorCode,
        message: str,
        field: Optional[str] = None,
        suggested_action: Optional[str] = None,
    ) -> AppErrorException:
        details = [ErrorDetail(message=message, field=field)] if field else []
        return cls(
            code=code,
            message=message,
            status_code=404,
            recoverable=False,
            details=details,
            suggested_action=suggested_action,
        )

    @classmethod
    def bad_request(
        cls,
        code: ErrorCode,
        message: str,
        field: Optional[str] = None,
        suggested_action: Optional[str] = None,
    ) -> AppErrorException:
        details = [ErrorDetail(message=message, field=field)] if field else []
        return cls(
            code=code,
            message=message,
            status_code=400,
            recoverable=True,
            details=details,
            suggested_action=suggested_action,
        )

    @classmethod
    def conflict(
        cls,
        code: ErrorCode,
        message: str,
        field: Optional[str] = None,
        suggested_action: Optional[str] = None,
    ) -> AppErrorException:
        details = [ErrorDetail(message=message, field=field)] if field else []
        return cls(
            code=code,
            message=message,
            status_code=409,
            recoverable=True,
            details=details,
            suggested_action=suggested_action,
        )

    @classmethod
    def unprocessable(
        cls,
        code: ErrorCode,
        message: str,
        field: Optional[str] = None,
        suggested_action: Optional[str] = None,
    ) -> AppErrorException:
        details = [ErrorDetail(message=message, field=field)] if field else []
        return cls(
            code=code,
            message=message,
            status_code=422,
            recoverable=True,
            details=details,
            suggested_action=suggested_action,
        )

    @classmethod
    def server_error(
        cls,
        code: ErrorCode,
        message: str,
        suggested_action: Optional[str] = None,
    ) -> AppErrorException:
        return cls(
            code=code,
            message=message,
            status_code=500,
            recoverable=False,
            suggested_action=suggested_action,
        )
