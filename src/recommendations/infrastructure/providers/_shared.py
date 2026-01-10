"""
Shared utilities for recommendation providers.
"""

import logging
from typing import Any

from src.recommendations.infrastructure.prompts.recommendation_prompts import (
    build_fiscal_recommendation_prompt,
)
from src.shared.domain.constants.isr_tables import get_isr_table

logger = logging.getLogger(__name__)


def build_recommendation_prompt(
    calculation_result: Any, user_data: dict[str, Any], fiscal_year: int
) -> str:
    """
    Build the prompt for AI recommendation generation.
    Shared across all AI providers for consistency.
    """
    isr_table = get_isr_table(fiscal_year)

    # Calculate limits
    uma_annual = isr_table.constants.annual_uma_value
    general_deduction_limit = 5 * uma_annual
    gross_income = calculation_result.gross_annual_income
    total_deduction_limit_15_percent = gross_income * 0.15
    effective_deduction_limit = min(
        general_deduction_limit, total_deduction_limit_15_percent
    )

    # Prepare education limits
    education_limits = {
        "preschool": isr_table.tuition_limits.preschool,
        "elementary": isr_table.tuition_limits.elementary,
        "middle_school": isr_table.tuition_limits.middle_school,
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
