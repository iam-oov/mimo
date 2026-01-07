from abc import ABC, abstractmethod
from collections.abc import Generator


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
