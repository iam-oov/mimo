"""
DeepSeek recommendation provider adapter.
"""

from collections.abc import Generator
from typing import Any

from src.recommendations.domain.ports.recommendation_provider import RecommendationProvider
from src.recommendations.infrastructure.providers._shared import (
    build_recommendation_prompt,
)
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.logging.structured_logger import get_logger

logger = get_logger(__name__)


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
        self, calculation_result: Any, user_data: dict[str, Any], fiscal_year: int
    ) -> Generator[str, None, None]:
        """
        Generate recommendations using DeepSeek with streaming.
        """
        try:
            from openai import OpenAI

            logger.info(
                "Starting DeepSeek recommendation generation",
                model=self.model,
                fiscal_year=fiscal_year,
                temperature=self.temperature,
            )

            client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            prompt = build_recommendation_prompt(calculation_result, user_data, fiscal_year)

            stream = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                stream=True,
            )

            total_chunks = 0
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    total_chunks += 1
                    yield chunk.choices[0].delta.content

            logger.info(
                "DeepSeek recommendation generation completed",
                total_chunks=total_chunks,
                model=self.model,
            )

        except Exception as e:
            logger.error(
                "DeepSeek recommendation generation failed",
                error=str(e),
                error_type=type(e).__name__,
                model=self.model,
            )
            raise

    def is_available(self) -> bool:
        """Check if DeepSeek provider is available"""
        settings = get_settings()
        return settings.has_deepseek_configured()

    def get_provider_name(self) -> str:
        """Get provider name for logging"""
        return "DeepSeek"
