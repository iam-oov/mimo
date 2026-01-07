from abc import ABC, abstractmethod
from datetime import date
from typing import Any


class UsageRepository(ABC):
    """
    Port (interface) for recommendation usage tracking.
    Infrastructure will provide concrete implementation.
    """

    @abstractmethod
    def get_usage_count(self, user_id: str, usage_date: date) -> int:
        """
        Get the number of recommendations used by a user on a specific date.

        Args:
            user_id: Unique identifier for the user
            usage_date: Date to check usage for

        Returns:
            Number of recommendations used
        """
        pass

    @abstractmethod
    def increment_usage(self, user_id: str, usage_date: date) -> None:
        """
        Increment usage count for a user on a specific date.

        Args:
            user_id: Unique identifier for the user
            usage_date: Date to increment usage for
        """
        pass

    @abstractmethod
    def reset_usage(self, user_id: str, usage_date: date) -> None:
        """
        Reset usage count for a user on a specific date.
        Useful for testing or administrative purposes.

        Args:
            user_id: Unique identifier for the user
            usage_date: Date to reset usage for
        """
        pass

    @abstractmethod
    def get_remaining_usage(self, user_id: str, usage_date: date, daily_limit: int) -> int:
        """
        Calculate remaining usage for a user.

        Args:
            user_id: Unique identifier for the user
            usage_date: Date to check usage for
            daily_limit: Maximum allowed usage per day

        Returns:
            Number of remaining recommendations available
        """
        pass


class TaxCalculationRepository(ABC):
    """
    Port (interface) for tax calculation persistence.
    Currently not implemented but defined for future expansion.
    """

    @abstractmethod
    def save(self, user_id: str, calculation_data: dict[str, Any]) -> str | None:
        """
        Save a tax calculation for future reference.

        Args:
            user_id: Unique identifier for the user
            calculation_data: Dictionary containing calculation results

        Returns:
            Unique identifier for the saved calculation
        """
        pass

    @abstractmethod
    def get_by_id(self, calculation_id: str) -> dict[str, Any] | None:
        """
        Retrieve a saved tax calculation by ID.

        Args:
            calculation_id: Unique identifier for the calculation

        Returns:
            Calculation data or None if not found
        """
        pass

    @abstractmethod
    def get_user_calculations(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get recent calculations for a user.

        Args:
            user_id: Unique identifier for the user
            limit: Maximum number of calculations to return

        Returns:
            List of calculation data dictionaries
        """
        pass
