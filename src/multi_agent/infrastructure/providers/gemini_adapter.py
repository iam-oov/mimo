"""
Gemini multi-agent provider adapter.
"""

import logging
from collections.abc import Generator

from google import genai

from src.multi_agent.domain.ports.multi_agent_provider import MultiAgentProvider
from src.shared.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)


class GeminiMultiAgentAdapter(MultiAgentProvider):
    """Adapter for Gemini multi-agent provider."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = settings.gemini_api_key
        self.client = genai.Client(api_key=self.api_key)

    def generate_stream(self, prompt: str) -> Generator[str, None, None]:
        """Generate streaming response from Gemini."""
        try:
            # Use new API with streaming
            response = self.client.models.generate_content_stream(
                model="gemini-1.5-flash",
                contents=prompt,
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Gemini multi-agent generation error: {e}")
            raise

    def is_available(self) -> bool:
        """Check if Gemini is configured and available."""
        return self.settings.has_gemini_configured()

    def get_model_name(self) -> str:
        """Return the model name for Gemini."""
        return "gemini-1.5-flash"
