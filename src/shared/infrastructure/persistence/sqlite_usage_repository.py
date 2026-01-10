import sqlite3
import threading
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Generator

from src.shared.domain.ports.repositories import UsageRepository


class SqliteUsageRepository(UsageRepository):
    """
    SQLite implementation of UsageRepository.
    Handles recommendation usage tracking in SQLite database.

    Thread-safe implementation using connection locking and atomic UPSERT operations.
    """

    def __init__(self, db_path: str = "recommendations.db"):
        self._db_path = Path(db_path)
        self._lock = threading.Lock()
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Create usage table if it doesn't exist"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recommendation_usage (
                    user_id TEXT,
                    date TEXT,
                    count INTEGER,
                    PRIMARY KEY (user_id, date)
                )
            """)
            conn.commit()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get thread-safe database connection with locking"""
        with self._lock:
            conn = sqlite3.connect(self._db_path, timeout=30.0)
            try:
                yield conn
            finally:
                conn.close()

    def get_usage_count(self, user_id: str, usage_date: date) -> int:
        """Get usage count for user on specific date"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT count FROM recommendation_usage WHERE user_id = ? AND date = ?",
                (user_id, usage_date.isoformat()),
            )
            result = cursor.fetchone()
            return result[0] if result else 0

    def increment_usage(self, user_id: str, usage_date: date) -> None:
        """
        Increment usage count for user on specific date.

        Uses atomic UPSERT to prevent race conditions:
        - INSERT OR IGNORE creates record if not exists
        - UPDATE always increments (works whether record existed or was just created)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            date_str = usage_date.isoformat()

            # Atomic UPSERT using INSERT ... ON CONFLICT
            cursor.execute(
                """
                INSERT INTO recommendation_usage (user_id, date, count) 
                VALUES (?, ?, 1)
                ON CONFLICT(user_id, date) 
                DO UPDATE SET count = count + 1
                """,
                (user_id, date_str),
            )
            conn.commit()

    def reset_usage(self, user_id: str, usage_date: date) -> None:
        """Reset usage count for user on specific date"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM recommendation_usage WHERE user_id = ? AND date = ?",
                (user_id, usage_date.isoformat()),
            )
            conn.commit()

    def get_remaining_usage(
        self, user_id: str, usage_date: date, daily_limit: int
    ) -> int:
        """Calculate remaining usage for user"""
        current_usage = self.get_usage_count(user_id, usage_date)
        return max(0, daily_limit - current_usage)
