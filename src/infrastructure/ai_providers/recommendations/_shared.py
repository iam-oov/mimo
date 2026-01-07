"""
Shared utilities for recommendation providers.
"""

import logging
from typing import Any

from src.domain.constants.isr_tables import get_tabla_isr
from src.infrastructure.ai_providers.prompts.recommendation_prompts import (
    build_fiscal_recommendation_prompt,
)

logger = logging.getLogger(__name__)


def build_recommendation_prompt(
    calculation_result: Any, user_data: dict[str, Any], fiscal_year: int
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
    effective_deduction_limit = min(general_deduction_limit, total_deduction_limit_15_percent)

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
