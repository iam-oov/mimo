"""
Tests for recommendation prompt builders.
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from src.recommendations.infrastructure.prompts.recommendation_prompts import (
    build_fallback_recommendations_prompt,
    build_fiscal_recommendation_prompt,
)
from src.tax_calculation.domain.entities.tax_calculation import TaxCalculation


class TestBuildFiscalRecommendationPrompt:
    """Tests for the main AI recommendation prompt builder."""

    @pytest.fixture
    def sample_calculation(self) -> TaxCalculation:
        """Create a sample tax calculation for testing."""
        return TaxCalculation(
            gross_annual_income=200000.0,
            taxable_bonus=5000.0,
            taxable_vacation_premium=2000.0,
            total_taxable_income=207000.0,
            authorized_deductions=30000.0,
            personal_deductions=15000.0,
            ppr_deductions=10000.0,
            education_deductions=5000.0,
            taxable_base=177000.0,
            determined_tax=25000.0,
            withheld_tax=28000.0,
            balance_in_favor=3000.0,
            balance_to_pay=0.0,
        )

    @pytest.fixture
    def sample_user_data(self) -> dict:
        """Create sample user data for testing."""
        return {
            "deduction_data": {
                "general_deductions": 15000.0,
                "ppr_deductions": 10000.0,
                "education_deductions": 5000.0,
            }
        }

    @pytest.fixture
    def education_limits(self) -> dict[str, float]:
        """Sample education limits."""
        return {
            "preescolar": 14200.0,
            "primaria": 12900.0,
            "secundaria": 19900.0,
            "profesional_tecnico": 17100.0,
            "bachillerato": 24500.0,
        }

    def test_prompt_contains_fiscal_year(
        self, sample_calculation, sample_user_data, education_limits
    ):
        """Prompt should include the fiscal year."""
        prompt = build_fiscal_recommendation_prompt(
            calculation_result=sample_calculation,
            user_data=sample_user_data,
            fiscal_year=2024,
            uma_annual=39392.1,
            general_deduction_limit=196960.5,
            effective_deduction_limit=30000.0,
            education_limits=education_limits,
        )

        assert "2024" in prompt

    def test_prompt_contains_income_data(
        self, sample_calculation, sample_user_data, education_limits
    ):
        """Prompt should include income figures."""
        prompt = build_fiscal_recommendation_prompt(
            calculation_result=sample_calculation,
            user_data=sample_user_data,
            fiscal_year=2024,
            uma_annual=39392.1,
            general_deduction_limit=196960.5,
            effective_deduction_limit=30000.0,
            education_limits=education_limits,
        )

        assert "200,000.00" in prompt  # gross_annual_income
        assert "5,000.00" in prompt  # taxable_bonus
        assert "2,000.00" in prompt  # taxable_vacation_premium

    def test_prompt_contains_deduction_data(
        self, sample_calculation, sample_user_data, education_limits
    ):
        """Prompt should include deduction information."""
        prompt = build_fiscal_recommendation_prompt(
            calculation_result=sample_calculation,
            user_data=sample_user_data,
            fiscal_year=2024,
            uma_annual=39392.1,
            general_deduction_limit=196960.5,
            effective_deduction_limit=30000.0,
            education_limits=education_limits,
        )

        assert "15,000.00" in prompt  # general_deductions
        assert "10,000.00" in prompt  # ppr_deductions

    def test_prompt_contains_balance_status_favor(
        self, sample_calculation, sample_user_data, education_limits
    ):
        """Prompt should indicate saldo a favor when positive balance."""
        prompt = build_fiscal_recommendation_prompt(
            calculation_result=sample_calculation,
            user_data=sample_user_data,
            fiscal_year=2024,
            uma_annual=39392.1,
            general_deduction_limit=196960.5,
            effective_deduction_limit=30000.0,
            education_limits=education_limits,
        )

        assert "Saldo a favor" in prompt

    def test_prompt_contains_balance_status_cargo(
        self, sample_user_data, education_limits
    ):
        """Prompt should indicate impuesto a cargo when negative balance."""
        calculation = TaxCalculation(
            gross_annual_income=200000.0,
            taxable_bonus=5000.0,
            taxable_vacation_premium=2000.0,
            total_taxable_income=207000.0,
            authorized_deductions=0.0,
            personal_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
            taxable_base=207000.0,
            determined_tax=35000.0,
            withheld_tax=28000.0,
            balance_in_favor=0.0,
            balance_to_pay=7000.0,
        )

        prompt = build_fiscal_recommendation_prompt(
            calculation_result=calculation,
            user_data=sample_user_data,
            fiscal_year=2024,
            uma_annual=39392.1,
            general_deduction_limit=196960.5,
            effective_deduction_limit=30000.0,
            education_limits=education_limits,
        )

        assert "Impuesto a cargo" in prompt

    def test_prompt_contains_education_limits(
        self, sample_calculation, sample_user_data, education_limits
    ):
        """Prompt should include education level limits."""
        prompt = build_fiscal_recommendation_prompt(
            calculation_result=sample_calculation,
            user_data=sample_user_data,
            fiscal_year=2024,
            uma_annual=39392.1,
            general_deduction_limit=196960.5,
            effective_deduction_limit=30000.0,
            education_limits=education_limits,
        )

        assert "Preescolar" in prompt
        assert "Bachillerato" in prompt
        assert "14,200" in prompt

    def test_prompt_contains_persona_instructions(
        self, sample_calculation, sample_user_data, education_limits
    ):
        """Prompt should include AI persona instructions."""
        prompt = build_fiscal_recommendation_prompt(
            calculation_result=sample_calculation,
            user_data=sample_user_data,
            fiscal_year=2024,
            uma_annual=39392.1,
            general_deduction_limit=196960.5,
            effective_deduction_limit=30000.0,
            education_limits=education_limits,
        )

        assert "Asesor Fiscal Digital" in prompt
        assert "profesional" in prompt.lower()

    @patch("src.recommendations.infrastructure.prompts.recommendation_prompts.datetime")
    def test_prompt_greeting_morning(
        self, mock_datetime, sample_calculation, sample_user_data, education_limits
    ):
        """Prompt should have morning greeting in morning hours."""
        mock_datetime.now.return_value.hour = 9

        prompt = build_fiscal_recommendation_prompt(
            calculation_result=sample_calculation,
            user_data=sample_user_data,
            fiscal_year=2024,
            uma_annual=39392.1,
            general_deduction_limit=196960.5,
            effective_deduction_limit=30000.0,
            education_limits=education_limits,
        )

        assert "Buenos días" in prompt

    @patch("src.recommendations.infrastructure.prompts.recommendation_prompts.datetime")
    def test_prompt_greeting_afternoon(
        self, mock_datetime, sample_calculation, sample_user_data, education_limits
    ):
        """Prompt should have afternoon greeting in afternoon hours."""
        mock_datetime.now.return_value.hour = 15

        prompt = build_fiscal_recommendation_prompt(
            calculation_result=sample_calculation,
            user_data=sample_user_data,
            fiscal_year=2024,
            uma_annual=39392.1,
            general_deduction_limit=196960.5,
            effective_deduction_limit=30000.0,
            education_limits=education_limits,
        )

        assert "Buenas tardes" in prompt

    @patch("src.recommendations.infrastructure.prompts.recommendation_prompts.datetime")
    def test_prompt_greeting_evening(
        self, mock_datetime, sample_calculation, sample_user_data, education_limits
    ):
        """Prompt should have evening greeting in evening hours."""
        mock_datetime.now.return_value.hour = 21

        prompt = build_fiscal_recommendation_prompt(
            calculation_result=sample_calculation,
            user_data=sample_user_data,
            fiscal_year=2024,
            uma_annual=39392.1,
            general_deduction_limit=196960.5,
            effective_deduction_limit=30000.0,
            education_limits=education_limits,
        )

        assert "Buenas noches" in prompt

    def test_prompt_contains_deduction_limits(
        self, sample_calculation, sample_user_data, education_limits
    ):
        """Prompt should include deduction limit information."""
        prompt = build_fiscal_recommendation_prompt(
            calculation_result=sample_calculation,
            user_data=sample_user_data,
            fiscal_year=2024,
            uma_annual=39392.1,
            general_deduction_limit=196960.5,
            effective_deduction_limit=30000.0,
            education_limits=education_limits,
        )

        assert "196,960.50" in prompt  # general_deduction_limit
        assert "30,000.00" in prompt  # effective_deduction_limit
        assert "LÍMITE EFECTIVO" in prompt

    def test_prompt_handles_empty_deductions(
        self, sample_calculation, education_limits
    ):
        """Prompt should handle user data with no deductions."""
        user_data = {"deduction_data": {}}

        prompt = build_fiscal_recommendation_prompt(
            calculation_result=sample_calculation,
            user_data=user_data,
            fiscal_year=2024,
            uma_annual=39392.1,
            general_deduction_limit=196960.5,
            effective_deduction_limit=196960.5,
            education_limits=education_limits,
        )

        assert "Total Deducido Actual: $0.00" in prompt

    def test_prompt_handles_empty_education_limits(
        self, sample_calculation, sample_user_data
    ):
        """Prompt should handle empty education limits."""
        prompt = build_fiscal_recommendation_prompt(
            calculation_result=sample_calculation,
            user_data=sample_user_data,
            fiscal_year=2024,
            uma_annual=39392.1,
            general_deduction_limit=196960.5,
            effective_deduction_limit=30000.0,
            education_limits={},
        )

        assert "No se proporcionaron límites de educación" in prompt

    def test_prompt_calculates_remaining_space(
        self, sample_calculation, sample_user_data, education_limits
    ):
        """Prompt should calculate remaining deduction space."""
        # effective_limit=30000, total_deductions=30000, remaining=0
        prompt = build_fiscal_recommendation_prompt(
            calculation_result=sample_calculation,
            user_data=sample_user_data,
            fiscal_year=2024,
            uma_annual=39392.1,
            general_deduction_limit=196960.5,
            effective_deduction_limit=30000.0,
            education_limits=education_limits,
        )

        assert "ESPACIO DISPONIBLE" in prompt

    def test_prompt_is_not_empty(
        self, sample_calculation, sample_user_data, education_limits
    ):
        """Prompt should never be empty."""
        prompt = build_fiscal_recommendation_prompt(
            calculation_result=sample_calculation,
            user_data=sample_user_data,
            fiscal_year=2024,
            uma_annual=39392.1,
            general_deduction_limit=196960.5,
            effective_deduction_limit=30000.0,
            education_limits=education_limits,
        )

        assert len(prompt) > 1000  # Should be a substantial prompt


class TestBuildFallbackRecommendationsPrompt:
    """Tests for fallback recommendations when AI is unavailable."""

    def test_fallback_contains_fiscal_year(self):
        """Fallback should include the fiscal year."""
        result = build_fallback_recommendations_prompt(
            fiscal_year=2024,
            general_limit=196960.5,
        )

        assert "2024" in result

    def test_fallback_contains_general_limit(self):
        """Fallback should include the general deduction limit."""
        result = build_fallback_recommendations_prompt(
            fiscal_year=2024,
            general_limit=196960.5,
        )

        assert "196,960.50" in result

    def test_fallback_contains_health_deductions(self):
        """Fallback should mention health-related deductions."""
        result = build_fallback_recommendations_prompt(
            fiscal_year=2024,
            general_limit=196960.5,
        )

        assert "Salud" in result
        assert "médico" in result.lower()

    def test_fallback_contains_ppr_info(self):
        """Fallback should mention PPR (retirement plan) deductions."""
        result = build_fallback_recommendations_prompt(
            fiscal_year=2024,
            general_limit=196960.5,
        )

        assert "PPR" in result or "Plan Personal de Retiro" in result

    def test_fallback_contains_payment_method_warning(self):
        """Fallback should warn about cash payments not being deductible."""
        result = build_fallback_recommendations_prompt(
            fiscal_year=2024,
            general_limit=196960.5,
        )

        assert "efectivo" in result.lower()
        assert "no" in result.lower() or "válida" in result.lower()

    def test_fallback_contains_factura_tip(self):
        """Fallback should mention the need for CFDI/facturas."""
        result = build_fallback_recommendations_prompt(
            fiscal_year=2024,
            general_limit=196960.5,
        )

        assert "CFDI" in result or "factura" in result.lower()

    def test_fallback_contains_disclaimer(self):
        """Fallback should include a legal disclaimer."""
        result = build_fallback_recommendations_prompt(
            fiscal_year=2024,
            general_limit=196960.5,
        )

        assert "contador" in result.lower() or "advertencia" in result.lower()

    def test_fallback_with_education_limits(self):
        """Fallback should include education limits when provided."""
        education_limits = {
            "preescolar": 14200.0,
            "bachillerato": 24500.0,
        }

        result = build_fallback_recommendations_prompt(
            fiscal_year=2024,
            general_limit=196960.5,
            education_limits=education_limits,
        )

        assert "Preescolar" in result
        assert "Bachillerato" in result
        assert "14,200" in result
        assert "24,500" in result

    def test_fallback_without_education_limits(self):
        """Fallback should work without education limits."""
        result = build_fallback_recommendations_prompt(
            fiscal_year=2024,
            general_limit=196960.5,
            education_limits=None,
        )

        assert "Colegiaturas" in result
        assert len(result) > 500

    def test_fallback_is_markdown_formatted(self):
        """Fallback should be formatted as Markdown."""
        result = build_fallback_recommendations_prompt(
            fiscal_year=2024,
            general_limit=196960.5,
        )

        assert "#" in result  # Headers
        assert "*" in result  # Lists or emphasis

    def test_fallback_mentions_april_deadline(self):
        """Fallback should mention the April declaration deadline."""
        result = build_fallback_recommendations_prompt(
            fiscal_year=2024,
            general_limit=196960.5,
        )

        assert "Abril" in result

    def test_fallback_different_years(self):
        """Fallback should work for different fiscal years."""
        for year in [2024, 2025, 2026]:
            result = build_fallback_recommendations_prompt(
                fiscal_year=year,
                general_limit=196960.5,
            )

            assert str(year) in result

    def test_fallback_is_not_empty(self):
        """Fallback should never return empty string."""
        result = build_fallback_recommendations_prompt(
            fiscal_year=2024,
            general_limit=196960.5,
        )

        assert len(result) > 0
        assert result.strip() != ""
