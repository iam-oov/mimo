"""
Gemini recommendation provider adapter.
"""

from typing import Generator, Any, Dict
import logging

from src.domain.ports.ai_providers import RecommendationProvider
from src.infrastructure.config.settings import get_settings
from src.infrastructure.ai_providers.recommendations._shared import (
    build_recommendation_prompt,
)

logger = logging.getLogger(__name__)


class GeminiRecommendationAdapter(RecommendationProvider):
    """
    Adapter for Google Gemini AI provider.
    """

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.gemini_api_key

    def generate_recommendations_stream(
        self, calculation_result: Any, user_data: Dict[str, Any], fiscal_year: int
    ) -> Generator[str, None, None]:
        """
        Generate recommendations using Gemini with streaming.
        """
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel("gemini-pro")
            prompt = build_recommendation_prompt(calculation_result, user_data, fiscal_year)

            response = model.generate_content(prompt, stream=True)

            for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise

    def is_available(self) -> bool:
        """Check if Gemini provider is available"""
        settings = get_settings()
        return settings.has_gemini_configured()

    def get_provider_name(self) -> str:
        """Get provider name for logging"""
        return "Gemini"
