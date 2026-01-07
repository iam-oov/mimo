"""
DeepSeek recommendation provider adapter.
"""

from typing import Generator, Any, Dict
import logging

from src.domain.ports.ai_providers import RecommendationProvider
from src.infrastructure.config.settings import get_settings
from src.infrastructure.ai_providers.recommendations._shared import (
    build_recommendation_prompt,
)

logger = logging.getLogger(__name__)


class DeepSeekRecommendationAdapter(RecommendationProvider):
    """
    Adapter for DeepSeek AI provider using OpenAI-compatible API.
    """

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.deepseek_api_key
        self.model = settings.deepseek_model
        self.base_url = settings.deepseek_base_url
        self.temperature = settings.deepseek_temperature

    def generate_recommendations_stream(
        self, calculation_result: Any, user_data: Dict[str, Any], fiscal_year: int
    ) -> Generator[str, None, None]:
        """
        Generate recommendations using DeepSeek with streaming.
        """
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            prompt = build_recommendation_prompt(calculation_result, user_data, fiscal_year)

            stream = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"DeepSeek generation error: {e}")
            raise

    def is_available(self) -> bool:
        """Check if DeepSeek provider is available"""
        settings = get_settings()
        return settings.has_deepseek_configured()

    def get_provider_name(self) -> str:
        """Get provider name for logging"""
        return "DeepSeek"
