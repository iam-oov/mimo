from collections.abc import Generator
from dataclasses import dataclass
from datetime import date
from typing import Any

from src.domain.entities.tax_calculation import TaxCalculation
from src.domain.ports.ai_providers import RecommendationProvider
from src.domain.ports.repositories import UsageRepository
from src.infrastructure.logging.structured_logger import get_logger

logger = get_logger(__name__)


@dataclass
class GenerateRecommendationsRequest:
    """Request DTO for recommendations generation use case"""

    user_id: str
    calculation: TaxCalculation
    user_data: dict[str, Any]
    fiscal_year: int


class GenerateRecommendationsUseCase:
    """
    Use case for generating fiscal recommendations.
    Handles rate limiting, provider selection, and usage tracking.
    """

    def __init__(
        self,
        providers: list[RecommendationProvider],
        usage_repository: UsageRepository,
        daily_limit: int = 3,
    ):
        self._providers = providers
        self._usage_repository = usage_repository
        self._daily_limit = daily_limit

    def can_generate(self, user_id: str) -> bool:
        """
        Check if user can generate recommendations (not rate limited).

        Args:
            user_id: Unique identifier for the user

        Returns:
            True if user has remaining usage, False otherwise
        """
        today = date.today()
        remaining = self._usage_repository.get_remaining_usage(user_id, today, self._daily_limit)
        return remaining > 0

    def get_usage_info(self, user_id: str) -> dict[str, int]:
        """
        Get usage information for a user.

        Args:
            user_id: Unique identifier for the user

        Returns:
            Dictionary with usage_count and remaining_usage
        """
        today = date.today()
        usage_count = self._usage_repository.get_usage_count(user_id, today)
        remaining = self._daily_limit - usage_count

        return {
            "usage_count": usage_count,
            "remaining_usage": max(0, remaining),
            "daily_limit": self._daily_limit,
        }

    def execute_stream(self, request: GenerateRecommendationsRequest) -> Generator[str, None, None]:
        """
        Execute recommendations generation with streaming response.

        Args:
            request: Recommendations generation request

        Yields:
            Chunks of recommendation text

        Raises:
            PermissionError: If user has exceeded daily limit
            RuntimeError: If no AI provider is available
        """
        logger.info(
            "Starting recommendation generation",
            user_id=request.user_id,
            fiscal_year=request.fiscal_year,
        )

        # Check rate limiting
        if not self.can_generate(request.user_id):
            logger.warning(
                "User exceeded daily limit", user_id=request.user_id, daily_limit=self._daily_limit
            )
            raise PermissionError("Daily recommendation limit exceeded")

        # Find available provider
        provider = self._get_available_provider()
        if not provider:
            logger.error("No AI provider available", providers_count=len(self._providers))
            raise RuntimeError("No AI provider available")

        # Generate recommendations
        try:
            logger.debug(
                "Using provider", provider=provider.get_provider_name(), user_id=request.user_id
            )

            for chunk in provider.generate_recommendations_stream(
                request.calculation, request.user_data, request.fiscal_year
            ):
                yield chunk

            # Increment usage AFTER successful generation
            today = date.today()
            self._usage_repository.increment_usage(request.user_id, today)

            logger.info(
                "Recommendation generation completed",
                provider=provider.get_provider_name(),
                user_id=request.user_id,
            )

        except Exception as e:
            logger.error(
                "Failed to generate recommendations",
                error=str(e),
                error_type=type(e).__name__,
                provider=provider.get_provider_name(),
                user_id=request.user_id,
            )
            raise RuntimeError(f"Failed to generate recommendations: {str(e)}")

    def _get_available_provider(self) -> RecommendationProvider | None:
        """
        Get first available provider from priority list.

        Returns:
            First available provider or None if none available
        """
        for provider in self._providers:
            if provider.is_available():
                return provider
        return None
