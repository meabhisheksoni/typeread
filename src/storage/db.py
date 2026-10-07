"""
TypeRead SQLite Database Connection & Lifecycle Manager
WAL mode, foreign keys enforcement, migration execution, and transaction boundaries.
"""

from __future__ import annotations
import sqlite3
import os
import sys
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Optional

from src.contracts.types import ErrorCode
from src.core.errors import AppErrorException

SCHEMA_SQL_PATH = Path(__file__).resolve().parent.parent.parent / ".orchestrator" / "blackboard" / "contracts" / "schema.sql"


class Database:
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=30.0,
            isolation_level=None,  # Autocommit mode by default, explicit BEGIN for transactions
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        if self.db_path != ":memory:":
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA temp_store = MEMORY;")
        return conn

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Cursor, None, None]:
        conn = self.get_connection()
        conn.execute("BEGIN IMMEDIATE;")
        cursor = conn.cursor()
        try:
            yield cursor
            conn.execute("COMMIT;")
        except Exception as e:
            conn.execute("ROLLBACK;")
            if isinstance(e, AppErrorException):
                raise
            raise AppErrorException.server_error(
                code=ErrorCode.DATABASE_ERROR,
                message=f"Database transaction error: {str(e)}",
            )
        finally:
            conn.close()

    @contextmanager
    def cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Executes schema.sql and ensures default user exists."""
        # Portable schema resolution
        candidate_paths = [
            Path(__file__).resolve().parent / "schema.sql",
            SCHEMA_SQL_PATH,
            getattr(sys, "_MEIPASS", "") and Path(getattr(sys, "_MEIPASS", "")) / "schema.sql",
            getattr(sys, "_MEIPASS", "") and Path(getattr(sys, "_MEIPASS", "")) / "src" / "storage" / "schema.sql",
            Path.cwd() / "src" / "storage" / "schema.sql",
            Path.cwd() / ".orchestrator" / "blackboard" / "contracts" / "schema.sql",
            Path("/home/munnartirupatitrip2/.orchestrator/blackboard/contracts/schema.sql"),
        ]
        schema_file = next((p for p in candidate_paths if p and Path(p).exists()), None)
        if not schema_file:
            raise FileNotFoundError("Could not find schema.sql in any standard package location")

        with open(schema_file, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        conn = self.get_connection()
        try:
            conn.executescript(schema_sql)
            # Ensure default user and settings exist
            default_user_id = "default_user"
            conn.execute(
                """
                INSERT OR IGNORE INTO users (id, display_name)
                VALUES (?, ?);
                """,
                (default_user_id, "Default User"),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO user_settings (user_id)
                VALUES (?);
                """,
                (default_user_id,),
            )
        finally:
            conn.close()
