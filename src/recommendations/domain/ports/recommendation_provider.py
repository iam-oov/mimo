from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Any


class RecommendationProvider(ABC):
    """
    Port (interface) for AI recommendation providers.
    Infrastructure will provide concrete implementations (DeepSeek, Gemini, etc.)
    """

    @abstractmethod
    def generate_recommendations_stream(
        self, calculation_result: Any, user_data: dict[str, Any], fiscal_year: int
    ) -> Generator[str, None, None]:
        """
        Generate fiscal recommendations as a streaming response.

        Args:
            calculation_result: Tax calculation results
            user_data: User's tax information
            fiscal_year: Fiscal year for the calculation

        Yields:
            Chunks of recommendation text
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this provider is available (configured with API keys, etc.)

        Returns:
            True if provider can be used, False otherwise
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of this provider for logging/debugging.

        Returns:
            Provider name (e.g., "DeepSeek", "Gemini")
        """
        pass
