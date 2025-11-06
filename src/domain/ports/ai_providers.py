from abc import ABC, abstractmethod
from typing import Generator, Dict, Any


class RecommendationProvider(ABC):
    """
    Port (interface) for AI recommendation providers.
    Infrastructure will provide concrete implementations (DeepSeek, Gemini, etc.)
    """

    @abstractmethod
    def generate_recommendations_stream(
        self, calculation_result: Any, user_data: Dict[str, Any], fiscal_year: int
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


class MultiAgentProvider(ABC):
    """
    Port (interface) for multi-agent analysis providers.
    Infrastructure will provide concrete implementations.
    """

    @abstractmethod
    def generate_stream(self, prompt: str) -> Generator[str, None, None]:
        """
        Generate AI response as a streaming response.

        Args:
            prompt: The prompt to send to the AI model

        Yields:
            Chunks of response text
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this provider is available.

        Returns:
            True if provider can be used, False otherwise
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the model name for this provider.

        Returns:
            Model name (e.g., "deepseek-chat", "gemini-2.0-flash-exp")
        """
        pass
