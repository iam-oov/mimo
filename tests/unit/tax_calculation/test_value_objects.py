"""
Tests for tax calculation value objects.
Validates IncomeData, DeductionData, and TaxpayerInfo.
"""

import pytest

from src.tax_calculation.domain.value_objects.tax_data import (
    DeductionData,
    IncomeData,
    TaxpayerInfo,
)


class TestTaxpayerInfo:
    """Tests for TaxpayerInfo value object"""

    def test_valid_taxpayer_info(self):
        """Valid taxpayer info is created successfully"""
        info = TaxpayerInfo(name="Juan Pérez", fiscal_year=2024)
        assert info.name == "Juan Pérez"
        assert info.fiscal_year == 2024

    def test_empty_name_defaults_to_contribuyente(self):
        """Empty name defaults to 'Contribuyente'"""
        info = TaxpayerInfo(name="", fiscal_year=2024)
        assert info.name == "Contribuyente"

    def test_whitespace_name_defaults_to_contribuyente(self):
        """Whitespace-only name defaults to 'Contribuyente'"""
        info = TaxpayerInfo(name="   ", fiscal_year=2024)
        assert info.name == "Contribuyente"

    def test_taxpayer_info_is_immutable(self):
        """TaxpayerInfo should be immutable (frozen)"""
        info = TaxpayerInfo(name="Test", fiscal_year=2024)
        with pytest.raises(AttributeError):
            info.name = "Changed"


class TestIncomeData:
    """Tests for IncomeData value object"""

    def test_valid_income_data(self):
        """Valid income data is created successfully"""
        income = IncomeData(
            monthly_gross_income=25000.0,
            bonus_days=15,
            vacation_days=12,
            vacation_premium_percentage=0.25,
        )
        assert income.monthly_gross_income == 25000.0
        assert income.bonus_days == 15
        assert income.vacation_days == 12
        assert income.vacation_premium_percentage == 0.25

    def test_negative_monthly_income_raises_error(self):
        """Negative monthly income should raise ValueError"""
        with pytest.raises(ValueError, match="cannot be negative"):
            IncomeData(
                monthly_gross_income=-1000.0,
                bonus_days=15,
                vacation_days=12,
                vacation_premium_percentage=0.25,
            )

    def test_negative_bonus_days_raises_error(self):
        """Negative bonus days should raise ValueError"""
        with pytest.raises(ValueError, match="between 0 and 365"):
            IncomeData(
                monthly_gross_income=25000.0,
                bonus_days=-1,
                vacation_days=12,
                vacation_premium_percentage=0.25,
            )

    def test_bonus_days_over_365_raises_error(self):
        """Bonus days over 365 should raise ValueError"""
        with pytest.raises(ValueError, match="between 0 and 365"):
            IncomeData(
                monthly_gross_income=25000.0,
                bonus_days=400,
                vacation_days=12,
                vacation_premium_percentage=0.25,
            )

    def test_negative_vacation_days_raises_error(self):
        """Negative vacation days should raise ValueError"""
        with pytest.raises(ValueError, match="between 0 and 365"):
            IncomeData(
                monthly_gross_income=25000.0,
                bonus_days=15,
                vacation_days=-5,
                vacation_premium_percentage=0.25,
            )

    def test_vacation_days_over_365_raises_error(self):
        """Vacation days over 365 should raise ValueError"""
        with pytest.raises(ValueError, match="between 0 and 365"):
            IncomeData(
                monthly_gross_income=25000.0,
                bonus_days=15,
                vacation_days=500,
                vacation_premium_percentage=0.25,
            )

    def test_negative_vacation_premium_percentage_raises_error(self):
        """Negative vacation premium percentage should raise ValueError"""
        with pytest.raises(ValueError, match="between 0 and 1"):
            IncomeData(
                monthly_gross_income=25000.0,
                bonus_days=15,
                vacation_days=12,
                vacation_premium_percentage=-0.1,
            )

    def test_vacation_premium_percentage_over_1_raises_error(self):
        """Vacation premium percentage over 1 should raise ValueError"""
        with pytest.raises(ValueError, match="between 0 and 1"):
            IncomeData(
                monthly_gross_income=25000.0,
                bonus_days=15,
                vacation_days=12,
                vacation_premium_percentage=1.5,
            )

    def test_income_data_is_immutable(self):
        """IncomeData should be immutable (frozen)"""
        income = IncomeData(
            monthly_gross_income=25000.0,
            bonus_days=15,
            vacation_days=12,
            vacation_premium_percentage=0.25,
        )
        with pytest.raises(AttributeError):
            income.monthly_gross_income = 30000.0

    # Property tests
    def test_daily_salary_calculation(self):
        """Daily salary should be monthly / 30"""
        income = IncomeData(
            monthly_gross_income=30000.0,
            bonus_days=15,
            vacation_days=12,
            vacation_premium_percentage=0.25,
        )
        assert income.daily_salary == 1000.0

    def test_annual_gross_income_calculation(self):
        """Annual gross income should be monthly * 12"""
        income = IncomeData(
            monthly_gross_income=25000.0,
            bonus_days=15,
            vacation_days=12,
            vacation_premium_percentage=0.25,
        )
        assert income.annual_gross_income == 300000.0

    def test_gross_bonus_calculation(self):
        """Gross bonus should be daily_salary * bonus_days"""
        income = IncomeData(
            monthly_gross_income=30000.0,  # daily = 1000
            bonus_days=15,
            vacation_days=12,
            vacation_premium_percentage=0.25,
        )
        assert income.gross_bonus == 15000.0

    def test_gross_vacation_premium_calculation(self):
        """Gross vacation premium = daily_salary * vacation_days * percentage"""
        income = IncomeData(
            monthly_gross_income=30000.0,  # daily = 1000
            bonus_days=15,
            vacation_days=12,
            vacation_premium_percentage=0.25,
        )
        # 1000 * 12 * 0.25 = 3000
        assert income.gross_vacation_premium == 3000.0

    def test_zero_income_is_valid(self):
        """Zero income should be valid"""
        income = IncomeData(
            monthly_gross_income=0.0,
            bonus_days=0,
            vacation_days=0,
            vacation_premium_percentage=0.0,
        )
        assert income.daily_salary == 0.0
        assert income.annual_gross_income == 0.0
        assert income.gross_bonus == 0.0
        assert income.gross_vacation_premium == 0.0

    def test_minimum_wage_income(self):
        """Test with minimum wage (~$7,500/month)"""
        income = IncomeData(
            monthly_gross_income=7500.0,
            bonus_days=15,
            vacation_days=12,
            vacation_premium_percentage=0.25,
        )
        assert income.daily_salary == 250.0
        assert income.annual_gross_income == 90000.0
        assert income.gross_bonus == 3750.0
        assert income.gross_vacation_premium == 750.0

    def test_high_income(self):
        """Test with high income"""
        income = IncomeData(
            monthly_gross_income=150000.0,
            bonus_days=30,
            vacation_days=20,
            vacation_premium_percentage=0.25,
        )
        assert income.daily_salary == 5000.0
        assert income.annual_gross_income == 1800000.0
        assert income.gross_bonus == 150000.0
        assert income.gross_vacation_premium == 25000.0


class TestDeductionData:
    """Tests for DeductionData value object"""

    def test_valid_deduction_data(self):
        """Valid deduction data is created successfully"""
        deductions = DeductionData(
            general_deductions=50000.0,
            ppr_deductions=30000.0,
            education_deductions=15000.0,
        )
        assert deductions.general_deductions == 50000.0
        assert deductions.ppr_deductions == 30000.0
        assert deductions.education_deductions == 15000.0

    def test_negative_general_deductions_raises_error(self):
        """Negative general deductions should raise ValueError"""
        with pytest.raises(ValueError, match="cannot be negative"):
            DeductionData(
                general_deductions=-1000.0,
                ppr_deductions=0.0,
                education_deductions=0.0,
            )

    def test_negative_ppr_deductions_raises_error(self):
        """Negative PPR deductions should raise ValueError"""
        with pytest.raises(ValueError, match="cannot be negative"):
            DeductionData(
                general_deductions=0.0,
                ppr_deductions=-500.0,
                education_deductions=0.0,
            )

    def test_negative_education_deductions_raises_error(self):
        """Negative education deductions should raise ValueError"""
        with pytest.raises(ValueError, match="cannot be negative"):
            DeductionData(
                general_deductions=0.0,
                ppr_deductions=0.0,
                education_deductions=-200.0,
            )

    def test_deduction_data_is_immutable(self):
        """DeductionData should be immutable (frozen)"""
        deductions = DeductionData(
            general_deductions=50000.0,
            ppr_deductions=30000.0,
            education_deductions=15000.0,
        )
        with pytest.raises(AttributeError):
            deductions.general_deductions = 60000.0

    def test_total_uncapped_calculation(self):
        """Total uncapped should be sum of all deductions"""
        deductions = DeductionData(
            general_deductions=50000.0,
            ppr_deductions=30000.0,
            education_deductions=15000.0,
        )
        assert deductions.total_uncapped == 95000.0

    def test_zero_deductions_is_valid(self):
        """Zero deductions should be valid"""
        deductions = DeductionData(
            general_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
        )
        assert deductions.total_uncapped == 0.0

    def test_large_deductions(self):
        """Large deduction values should be valid"""
        deductions = DeductionData(
            general_deductions=500000.0,
            ppr_deductions=300000.0,
            education_deductions=100000.0,
        )
        assert deductions.total_uncapped == 900000.0


class TestIncomeDataEdgeCases:
    """Edge case tests for IncomeData"""

    def test_boundary_bonus_days_zero(self):
        """Zero bonus days should be valid"""
        income = IncomeData(
            monthly_gross_income=25000.0,
            bonus_days=0,
            vacation_days=12,
            vacation_premium_percentage=0.25,
        )
        assert income.gross_bonus == 0.0

    def test_boundary_bonus_days_365(self):
        """365 bonus days should be valid (max)"""
        income = IncomeData(
            monthly_gross_income=30000.0,  # daily = 1000
            bonus_days=365,
            vacation_days=12,
            vacation_premium_percentage=0.25,
        )
        assert income.gross_bonus == 365000.0

    def test_boundary_vacation_percentage_zero(self):
        """Zero vacation premium percentage should be valid"""
        income = IncomeData(
            monthly_gross_income=25000.0,
            bonus_days=15,
            vacation_days=12,
            vacation_premium_percentage=0.0,
        )
        assert income.gross_vacation_premium == 0.0

    def test_boundary_vacation_percentage_one(self):
        """100% vacation premium percentage should be valid"""
        income = IncomeData(
            monthly_gross_income=30000.0,  # daily = 1000
            bonus_days=15,
            vacation_days=12,
            vacation_premium_percentage=1.0,
        )
        assert income.gross_vacation_premium == 12000.0

    def test_very_small_income(self):
        """Very small income values should work"""
        income = IncomeData(
            monthly_gross_income=0.01,
            bonus_days=1,
            vacation_days=1,
            vacation_premium_percentage=0.25,
        )
        assert income.daily_salary == pytest.approx(0.01 / 30, rel=1e-5)

    def test_very_large_income(self):
        """Very large income values should work"""
        income = IncomeData(
            monthly_gross_income=10_000_000.0,  # 10 million/month
            bonus_days=30,
            vacation_days=20,
            vacation_premium_percentage=0.25,
        )
        assert income.annual_gross_income == 120_000_000.0
