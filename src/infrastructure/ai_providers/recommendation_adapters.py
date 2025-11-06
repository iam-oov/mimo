"""
AI provider adapters implementing RecommendationProvider port.
Direct implementations using DeepSeek, Gemini, and fallback strategies.
"""

from typing import Generator, Dict, Any
import logging

from src.domain.ports.ai_providers import RecommendationProvider
from src.infrastructure.config.settings import get_settings
from src.infrastructure.ai_providers.prompts import (
    build_fiscal_recommendation_prompt,
    build_fallback_recommendations_prompt,
)
from tabla_isr_constants import get_tabla_isr

logger = logging.getLogger(__name__)


def _build_prompt(
    calculation_result: Any, user_data: Dict[str, Any], fiscal_year: int
) -> str:
    """
    Build the prompt for AI recommendation generation.
    Shared across all AI providers for consistency.
    """
    tabla_isr = get_tabla_isr(fiscal_year)

    # Calculate limits
    uma_annual = tabla_isr.constantes.valor_uma_anual
    general_deduction_limit = 5 * uma_annual
    gross_income = calculation_result.gross_annual_income
    total_deduction_limit_15_percent = gross_income * 0.15
    effective_deduction_limit = min(
        general_deduction_limit, total_deduction_limit_15_percent
    )

    # Prepare education limits
    education_limits = {
        "preescolar": tabla_isr.topes_colegiaturas.preescolar,
        "primaria": tabla_isr.topes_colegiaturas.primaria,
        "secundaria": tabla_isr.topes_colegiaturas.secundaria,
    }

    return build_fiscal_recommendation_prompt(
        calculation_result=calculation_result,
        user_data=user_data,
        fiscal_year=fiscal_year,
        uma_annual=uma_annual,
        general_deduction_limit=general_deduction_limit,
        effective_deduction_limit=effective_deduction_limit,
        education_limits=education_limits,
    )


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
            prompt = _build_prompt(calculation_result, user_data, fiscal_year)

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
            prompt = _build_prompt(calculation_result, user_data, fiscal_year)

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


class FallbackRecommendationAdapter(RecommendationProvider):
    """
    Adapter for fallback recommendation provider.
    Always available with static recommendations.
    """

    def __init__(self):
        pass

    def generate_recommendations_stream(
        self, calculation_result: Any, user_data: Dict[str, Any], fiscal_year: int
    ) -> Generator[str, None, None]:
        """
        Generate static fallback recommendations.
        """
        tabla_isr = get_tabla_isr(fiscal_year)
        uma_annual = tabla_isr.constantes.valor_uma_anual
        general_limit = 5 * uma_annual

        recommendations = build_fallback_recommendations_prompt(
            fiscal_year=fiscal_year, general_limit=general_limit
        )

        yield recommendations

    def is_available(self) -> bool:
        """Fallback is always available"""
        return True

    def get_provider_name(self) -> str:
        """Get provider name for logging"""
        return "Fallback"
