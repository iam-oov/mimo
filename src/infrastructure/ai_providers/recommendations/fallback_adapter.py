"""
Fallback recommendation provider adapter.
"""

from typing import Generator, Any, Dict
import logging

from src.domain.ports.ai_providers import RecommendationProvider
from src.infrastructure.ai_providers.prompts.recommendation_prompts import (
    build_fallback_recommendations_prompt,
)
from src.domain.constants.isr_tables import get_tabla_isr

logger = logging.getLogger(__name__)


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
