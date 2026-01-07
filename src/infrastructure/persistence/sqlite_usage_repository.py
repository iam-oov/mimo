import sqlite3
from datetime import date
from pathlib import Path

from src.domain.ports.repositories import UsageRepository


class SqliteUsageRepository(UsageRepository):
    """
    SQLite implementation of UsageRepository.
    Handles recommendation usage tracking in SQLite database.
    """

    def __init__(self, db_path: str = "recommendations.db"):
        self._db_path = Path(db_path)
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Create usage table if it doesn't exist"""
        conn = sqlite3.connect(self._db_path)
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
        conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        return sqlite3.connect(self._db_path)

    def get_usage_count(self, user_id: str, usage_date: date) -> int:
        """Get usage count for user on specific date"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT count FROM recommendation_usage WHERE user_id = ? AND date = ?",
            (user_id, usage_date.isoformat()),
        )

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else 0

    def increment_usage(self, user_id: str, usage_date: date) -> None:
        """Increment usage count for user on specific date"""
        conn = self._get_connection()
        cursor = conn.cursor()

        date_str = usage_date.isoformat()
        current_count = self.get_usage_count(user_id, usage_date)

        if current_count > 0:
            cursor.execute(
                "UPDATE recommendation_usage SET count = count + 1 WHERE user_id = ? AND date = ?",
                (user_id, date_str),
            )
        else:
            cursor.execute(
                "INSERT INTO recommendation_usage (user_id, date, count) VALUES (?, ?, 1)",
                (user_id, date_str),
            )

        conn.commit()
        conn.close()

    def reset_usage(self, user_id: str, usage_date: date) -> None:
        """Reset usage count for user on specific date"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM recommendation_usage WHERE user_id = ? AND date = ?",
            (user_id, usage_date.isoformat()),
        )

        conn.commit()
        conn.close()

    def get_remaining_usage(self, user_id: str, usage_date: date, daily_limit: int) -> int:
        """Calculate remaining usage for user"""
        current_usage = self.get_usage_count(user_id, usage_date)
        return max(0, daily_limit - current_usage)
