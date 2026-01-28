"""
Tests for rate limiting and usage repository.
Includes tests that expose and validate fixes for race conditions.
"""

import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

import pytest

from src.shared.infrastructure.persistence.sqlite_usage_repository import (
    SqliteUsageRepository,
)


@pytest.fixture
def temp_db_path():
    """Create a temporary database file"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield f.name
    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def usage_repository(temp_db_path: str) -> SqliteUsageRepository:
    """Create a fresh usage repository with temp database"""
    return SqliteUsageRepository(db_path=temp_db_path)


class TestUsageRepositoryBasic:
    """Basic functionality tests for UsageRepository"""

    def test_get_usage_count_returns_zero_for_new_user(
        self, usage_repository: SqliteUsageRepository
    ):
        """New user should have zero usage"""
        count = usage_repository.get_usage_count("new_user", date.today())
        assert count == 0

    def test_increment_usage_creates_record(
        self, usage_repository: SqliteUsageRepository
    ):
        """First increment should create a new record with count 1"""
        usage_repository.increment_usage("user1", date.today())
        count = usage_repository.get_usage_count("user1", date.today())
        assert count == 1

    def test_increment_usage_increases_count(
        self, usage_repository: SqliteUsageRepository
    ):
        """Multiple increments should increase the count"""
        usage_repository.increment_usage("user1", date.today())
        usage_repository.increment_usage("user1", date.today())
        usage_repository.increment_usage("user1", date.today())

        count = usage_repository.get_usage_count("user1", date.today())
        assert count == 3

    def test_different_users_have_separate_counts(
        self, usage_repository: SqliteUsageRepository
    ):
        """Different users should have independent counts"""
        usage_repository.increment_usage("user1", date.today())
        usage_repository.increment_usage("user1", date.today())
        usage_repository.increment_usage("user2", date.today())

        count1 = usage_repository.get_usage_count("user1", date.today())
        count2 = usage_repository.get_usage_count("user2", date.today())

        assert count1 == 2
        assert count2 == 1

    def test_different_dates_have_separate_counts(
        self, usage_repository: SqliteUsageRepository
    ):
        """Different dates should have independent counts"""
        today = date(2024, 1, 15)
        yesterday = date(2024, 1, 14)

        usage_repository.increment_usage("user1", today)
        usage_repository.increment_usage("user1", today)
        usage_repository.increment_usage("user1", yesterday)

        count_today = usage_repository.get_usage_count("user1", today)
        count_yesterday = usage_repository.get_usage_count("user1", yesterday)

        assert count_today == 2
        assert count_yesterday == 1

    def test_reset_usage_removes_record(self, usage_repository: SqliteUsageRepository):
        """Reset should remove the usage record"""
        usage_repository.increment_usage("user1", date.today())
        usage_repository.increment_usage("user1", date.today())

        usage_repository.reset_usage("user1", date.today())

        count = usage_repository.get_usage_count("user1", date.today())
        assert count == 0

    def test_reset_nonexistent_user_does_not_error(
        self, usage_repository: SqliteUsageRepository
    ):
        """Resetting nonexistent user should not raise error"""
        usage_repository.reset_usage("nonexistent_user", date.today())
        # Should not raise

    def test_get_remaining_usage_calculation(
        self, usage_repository: SqliteUsageRepository
    ):
        """Remaining usage should be daily_limit - current_usage"""
        daily_limit = 3

        # Initially full quota available
        remaining = usage_repository.get_remaining_usage(
            "user1", date.today(), daily_limit
        )
        assert remaining == 3

        # After one use
        usage_repository.increment_usage("user1", date.today())
        remaining = usage_repository.get_remaining_usage(
            "user1", date.today(), daily_limit
        )
        assert remaining == 2

        # After all uses
        usage_repository.increment_usage("user1", date.today())
        usage_repository.increment_usage("user1", date.today())
        remaining = usage_repository.get_remaining_usage(
            "user1", date.today(), daily_limit
        )
        assert remaining == 0

    def test_get_remaining_usage_never_negative(
        self, usage_repository: SqliteUsageRepository
    ):
        """Remaining usage should never be negative"""
        daily_limit = 2

        # Use more than limit
        for _ in range(5):
            usage_repository.increment_usage("user1", date.today())

        remaining = usage_repository.get_remaining_usage(
            "user1", date.today(), daily_limit
        )
        assert remaining == 0


class TestUsageRepositoryConcurrency:
    """Concurrency tests to verify race condition fixes"""

    def test_concurrent_increments_are_accurate(
        self, usage_repository: SqliteUsageRepository
    ):
        """
        Multiple concurrent increments should all be counted.
        This test exposes race conditions in non-atomic implementations.
        """
        user_id = "concurrent_user"
        today = date.today()
        num_threads = 10
        increments_per_thread = 5
        expected_total = num_threads * increments_per_thread

        def increment_multiple_times():
            for _ in range(increments_per_thread):
                usage_repository.increment_usage(user_id, today)

        # Run increments concurrently
        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=increment_multiple_times)
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify count is accurate
        final_count = usage_repository.get_usage_count(user_id, today)
        assert final_count == expected_total, (
            f"Expected {expected_total} but got {final_count}. "
            "Race condition detected in increment_usage!"
        )

    def test_concurrent_first_increments_dont_duplicate(
        self, usage_repository: SqliteUsageRepository
    ):
        """
        Multiple threads trying to create first record shouldn't fail or duplicate.
        Tests the INSERT conflict scenario.
        """
        user_id = "first_increment_user"
        today = date.today()
        num_threads = 20

        errors = []

        def first_increment():
            try:
                usage_repository.increment_usage(user_id, today)
            except Exception as e:
                errors.append(str(e))

        # All threads try to be "first"
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(first_increment) for _ in range(num_threads)]
            for f in as_completed(futures):
                pass  # Wait for all

        # Should have no errors
        assert len(errors) == 0, f"Errors during concurrent first increment: {errors}"

        # Count should be exactly num_threads
        final_count = usage_repository.get_usage_count(user_id, today)
        assert final_count == num_threads

    def test_high_contention_scenario(self, usage_repository: SqliteUsageRepository):
        """
        Stress test with high contention - many users, many increments.
        """
        num_users = 5
        num_threads_per_user = 4
        increments_per_thread = 3
        today = date.today()

        def user_increments(user_id: str):
            for _ in range(increments_per_thread):
                usage_repository.increment_usage(user_id, today)
                time.sleep(0.001)  # Small delay to increase interleaving

        # Create threads for multiple users
        threads = []
        for user_num in range(num_users):
            user_id = f"stress_user_{user_num}"
            for _ in range(num_threads_per_user):
                t = threading.Thread(target=user_increments, args=(user_id,))
                threads.append(t)

        # Start all threads
        for t in threads:
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Verify each user has correct count
        expected_per_user = num_threads_per_user * increments_per_thread
        for user_num in range(num_users):
            user_id = f"stress_user_{user_num}"
            count = usage_repository.get_usage_count(user_id, today)
            assert count == expected_per_user, (
                f"User {user_id} has {count} instead of {expected_per_user}"
            )


class TestRateLimitingLogic:
    """Tests for rate limiting business logic"""

    def test_user_within_limit_can_increment(
        self, usage_repository: SqliteUsageRepository
    ):
        """User within daily limit should be able to increment"""
        daily_limit = 3
        user_id = "limited_user"
        today = date.today()

        for i in range(daily_limit):
            remaining = usage_repository.get_remaining_usage(
                user_id, today, daily_limit
            )
            assert remaining == daily_limit - i
            usage_repository.increment_usage(user_id, today)

        # After limit, remaining should be 0
        remaining = usage_repository.get_remaining_usage(user_id, today, daily_limit)
        assert remaining == 0

    def test_user_at_limit_has_zero_remaining(
        self, usage_repository: SqliteUsageRepository
    ):
        """User at daily limit should have zero remaining"""
        daily_limit = 3
        user_id = "at_limit_user"
        today = date.today()

        for _ in range(daily_limit):
            usage_repository.increment_usage(user_id, today)

        remaining = usage_repository.get_remaining_usage(user_id, today, daily_limit)
        assert remaining == 0

    def test_different_days_reset_limit(self, usage_repository: SqliteUsageRepository):
        """New day should have fresh limit"""
        daily_limit = 3
        user_id = "daily_reset_user"
        yesterday = date(2024, 1, 14)
        today = date(2024, 1, 15)

        # Use all yesterday's limit
        for _ in range(daily_limit):
            usage_repository.increment_usage(user_id, yesterday)

        # Today should have full limit
        remaining_today = usage_repository.get_remaining_usage(
            user_id, today, daily_limit
        )
        assert remaining_today == daily_limit

        # Yesterday should still be at limit
        remaining_yesterday = usage_repository.get_remaining_usage(
            user_id, yesterday, daily_limit
        )
        assert remaining_yesterday == 0


class TestDatabasePersistence:
    """Tests for database persistence"""

    def test_data_persists_across_repository_instances(self, temp_db_path: str):
        """Data should persist when creating new repository instance"""
        user_id = "persistent_user"
        today = date.today()

        # First instance - create data
        repo1 = SqliteUsageRepository(db_path=temp_db_path)
        repo1.increment_usage(user_id, today)
        repo1.increment_usage(user_id, today)

        # Second instance - read data
        repo2 = SqliteUsageRepository(db_path=temp_db_path)
        count = repo2.get_usage_count(user_id, today)

        assert count == 2

    def test_table_created_on_initialization(self, temp_db_path: str):
        """Table should be created when repository is initialized"""
        import sqlite3

        # Create repository
        SqliteUsageRepository(db_path=temp_db_path)

        # Check table exists
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='recommendation_usage'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == "recommendation_usage"
