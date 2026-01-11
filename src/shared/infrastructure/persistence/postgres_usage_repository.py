"""
PostgreSQL implementation of UsageRepository.
Handles recommendation usage tracking in PostgreSQL database.
"""

import threading
from contextlib import contextmanager
from datetime import date
from typing import Generator

from src.shared.domain.ports.repositories import UsageRepository


class PostgresUsageRepository(UsageRepository):
    """
    PostgreSQL implementation of UsageRepository.
    Thread-safe implementation using connection pooling and atomic UPSERT operations.
    """

    def __init__(self, database_url: str):
        """
        Initialize PostgreSQL repository.

        Args:
            database_url: PostgreSQL connection URL (e.g., postgresql://user:pass@host:port/dbname)
        """
        # Lazy import psycopg2 only when PostgreSQL is actually used
        try:
            import psycopg2
            import psycopg2.extras

            self._psycopg2 = psycopg2
        except ImportError as e:
            raise ImportError(
                "psycopg2-binary is required for PostgreSQL support. "
                "Install it with: uv add psycopg2-binary"
            ) from e

        self._database_url = database_url
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
            # Create index for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_usage_user_date 
                ON recommendation_usage(user_id, date)
            """)
            conn.commit()

    @contextmanager
    def _get_connection(self) -> Generator:
        """Get thread-safe database connection with locking"""
        with self._lock:
            conn = self._psycopg2.connect(self._database_url)
            try:
                yield conn
            finally:
                conn.close()

    def get_usage_count(self, user_id: str, usage_date: date) -> int:
        """Get usage count for user on specific date"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT count FROM recommendation_usage WHERE user_id = %s AND date = %s",
                (user_id, usage_date.isoformat()),
            )
            result = cursor.fetchone()
            return result[0] if result else 0

    def increment_usage(self, user_id: str, usage_date: date) -> int:
        """
        Increment usage count for user on specific date.
        Uses atomic UPSERT (INSERT ... ON CONFLICT) for thread safety.

        Returns:
            New usage count after increment
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Atomic UPSERT using INSERT ... ON CONFLICT
            cursor.execute(
                """
                INSERT INTO recommendation_usage (user_id, date, count)
                VALUES (%s, %s, 1)
                ON CONFLICT (user_id, date)
                DO UPDATE SET count = recommendation_usage.count + 1
                RETURNING count
                """,
                (user_id, usage_date.isoformat()),
            )

            new_count = cursor.fetchone()[0]
            conn.commit()
            return new_count

    def reset_usage(self, user_id: str, usage_date: date) -> None:
        """Reset usage count for user on specific date"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM recommendation_usage WHERE user_id = %s AND date = %s",
                (user_id, usage_date.isoformat()),
            )
            conn.commit()

    def get_total_usage_count(self) -> int:
        """Get total usage count across all users and dates"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM recommendation_usage")
            result = cursor.fetchone()
            return result[0] if result else 0
