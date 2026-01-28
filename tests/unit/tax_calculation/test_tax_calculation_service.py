"""
Tests for TaxCalculationService.
This is the core business logic - tests must be comprehensive.
"""

import pytest

from src.shared.domain.constants.isr_tables import get_isr_table
from src.tax_calculation.domain.services.tax_calculation_service import (
    TaxCalculationService,
)
from src.tax_calculation.domain.value_objects.tax_data import (
    DeductionData,
    IncomeData,
)


class TestTaxCalculationServiceBasic:
    """Basic calculation tests"""

    def test_service_initialization(self, isr_table_2024):
        """Service initializes correctly with ISR table"""
        service = TaxCalculationService(isr_table_2024)
        assert service._isr_table == isr_table_2024

    def test_basic_calculation_returns_tax_calculation(
        self, tax_service_2024, income_medium, deductions_none
    ):
        """Basic calculation returns TaxCalculation entity"""
        result = tax_service_2024.calculate_tax(income_medium, deductions_none)

        assert result is not None
        assert result.gross_annual_income > 0
        assert result.determined_tax >= 0

    def test_zero_income_returns_zero_tax(self, tax_service_2024, income_zero):
        """Zero income should result in zero tax"""
        deductions = DeductionData(
            general_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
        )
        result = tax_service_2024.calculate_tax(income_zero, deductions)

        assert result.gross_annual_income == 0.0
        assert result.determined_tax == 0.0
        assert result.withheld_tax == 0.0
        assert result.balance_in_favor == 0.0
        assert result.balance_to_pay == 0.0


class TestBonusExemptions:
    """Tests for aguinaldo (bonus) exemption calculations"""

    def test_bonus_fully_exempt_when_under_30_umas(self, tax_service_2024):
        """Bonus under 30 UMAs should be fully exempt"""
        # 2024: UMA daily = 108.57, 30 UMAs = 3257.10
        income = IncomeData(
            monthly_gross_income=30000.0,  # daily = 1000
            bonus_days=3,  # bonus = 3000 (under 3257.10)
            vacation_days=0,
            vacation_premium_percentage=0.0,
        )
        deductions = DeductionData(
            general_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
        )

        result = tax_service_2024.calculate_tax(income, deductions)

        # Bonus of 3000 is fully exempt (under 30 UMAs = 3257.10)
        assert result.taxable_bonus == 0.0

    def test_bonus_partially_taxable_when_over_30_umas(self, tax_service_2024):
        """Bonus over 30 UMAs should be partially taxable"""
        # 2024: UMA daily = 108.57, 30 UMAs = 3257.10
        income = IncomeData(
            monthly_gross_income=30000.0,  # daily = 1000
            bonus_days=15,  # bonus = 15000
            vacation_days=0,
            vacation_premium_percentage=0.0,
        )
        deductions = DeductionData(
            general_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
        )

        result = tax_service_2024.calculate_tax(income, deductions)

        # Taxable = 15000 - 3257.10 = 11742.90
        expected_taxable = 15000 - (108.57 * 30)
        assert result.taxable_bonus == pytest.approx(expected_taxable, rel=1e-2)

    def test_bonus_exemption_uses_correct_uma_for_year(self):
        """Bonus exemption should use UMA value for the fiscal year"""
        income = IncomeData(
            monthly_gross_income=30000.0,  # daily = 1000
            bonus_days=15,  # bonus = 15000
            vacation_days=0,
            vacation_premium_percentage=0.0,
        )
        deductions = DeductionData(
            general_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
        )

        # 2024 UMA = 108.57
        service_2024 = TaxCalculationService(get_isr_table(2024))
        result_2024 = service_2024.calculate_tax(income, deductions)

        # 2026 UMA = 117.31
        service_2026 = TaxCalculationService(get_isr_table(2026))
        result_2026 = service_2026.calculate_tax(income, deductions)

        # Higher UMA = more exempt = less taxable
        assert result_2026.taxable_bonus < result_2024.taxable_bonus


class TestVacationPremiumExemptions:
    """Tests for vacation premium exemption calculations"""

    def test_vacation_premium_fully_exempt_when_under_15_umas(self, tax_service_2024):
        """Vacation premium under 15 UMAs should be fully exempt"""
        # 2024: UMA daily = 108.57, 15 UMAs = 1628.55
        income = IncomeData(
            monthly_gross_income=30000.0,  # daily = 1000
            bonus_days=0,
            vacation_days=6,  # premium = 1000 * 6 * 0.25 = 1500 (under 1628.55)
            vacation_premium_percentage=0.25,
        )
        deductions = DeductionData(
            general_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
        )

        result = tax_service_2024.calculate_tax(income, deductions)

        assert result.taxable_vacation_premium == 0.0

    def test_vacation_premium_partially_taxable_when_over_15_umas(
        self, tax_service_2024
    ):
        """Vacation premium over 15 UMAs should be partially taxable"""
        # 2024: UMA daily = 108.57, 15 UMAs = 1628.55
        income = IncomeData(
            monthly_gross_income=30000.0,  # daily = 1000
            bonus_days=0,
            vacation_days=20,  # premium = 1000 * 20 * 0.25 = 5000
            vacation_premium_percentage=0.25,
        )
        deductions = DeductionData(
            general_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
        )

        result = tax_service_2024.calculate_tax(income, deductions)

        # Taxable = 5000 - 1628.55 = 3371.45
        expected_taxable = 5000 - (108.57 * 15)
        assert result.taxable_vacation_premium == pytest.approx(
            expected_taxable, rel=1e-2
        )


class TestDeductionCaps:
    """Tests for deduction cap calculations"""

    def test_deductions_under_cap_are_fully_applied(self, tax_service_2024):
        """Deductions under global cap should be fully applied"""
        income = IncomeData(
            monthly_gross_income=100000.0,  # Annual = 1.2M
            bonus_days=0,
            vacation_days=0,
            vacation_premium_percentage=0.0,
        )
        # Small deductions that won't hit any cap
        deductions = DeductionData(
            general_deductions=10000.0,
            ppr_deductions=5000.0,
            education_deductions=3000.0,
        )

        result = tax_service_2024.calculate_tax(income, deductions)

        # Total deductions = 18000, well under 5 UMAs (~198k) and 15% (~180k)
        assert result.authorized_deductions == pytest.approx(18000.0, rel=1e-2)

    def test_deductions_capped_at_5_umas_when_lower(self, tax_service_2024):
        """Deductions should be capped at 5 UMAs when it's lower than 15%"""
        # 2024: 5 UMAs annual = 39606.36 * 5 = 198031.80
        income = IncomeData(
            monthly_gross_income=200000.0,  # Annual = 2.4M, 15% = 360k
            bonus_days=0,
            vacation_days=0,
            vacation_premium_percentage=0.0,
        )
        # Deductions exceeding 5 UMAs
        deductions = DeductionData(
            general_deductions=300000.0,
            ppr_deductions=200000.0,
            education_deductions=50000.0,
        )

        result = tax_service_2024.calculate_tax(income, deductions)

        # Should be capped at 5 UMAs = 198031.80
        uma_annual = 39606.36
        expected_cap = uma_annual * 5
        assert result.authorized_deductions == pytest.approx(expected_cap, rel=1e-2)

    def test_deductions_capped_at_15_percent_when_lower(self, tax_service_2024):
        """Deductions should be capped at 15% of income when it's lower than 5 UMAs"""
        # Low income where 15% < 5 UMAs
        income = IncomeData(
            monthly_gross_income=20000.0,  # Annual = 240k, 15% = 36k
            bonus_days=0,
            vacation_days=0,
            vacation_premium_percentage=0.0,
        )
        # Deductions exceeding 15% of income
        deductions = DeductionData(
            general_deductions=50000.0,
            ppr_deductions=30000.0,
            education_deductions=10000.0,
        )

        result = tax_service_2024.calculate_tax(income, deductions)

        # Should be capped at 15% = 36000
        expected_cap = 240000.0 * 0.15
        assert result.authorized_deductions == pytest.approx(expected_cap, rel=1e-2)

    def test_individual_deduction_caps_applied(self, tax_service_2024):
        """Individual deduction types should respect their own caps"""
        # 2024: General cap = 5 UMAs annual = 198031.80
        # Education cap = max tuition limit = 24500 (high school)
        income = IncomeData(
            monthly_gross_income=300000.0,  # Very high income
            bonus_days=0,
            vacation_days=0,
            vacation_premium_percentage=0.0,
        )
        deductions = DeductionData(
            general_deductions=500000.0,  # Way over cap
            ppr_deductions=500000.0,  # Way over cap
            education_deductions=100000.0,  # Way over cap
        )

        result = tax_service_2024.calculate_tax(income, deductions)

        # The global cap (5 UMAs or 15%) will limit total anyway
        uma_annual = 39606.36
        expected_global_cap = uma_annual * 5
        assert result.authorized_deductions == pytest.approx(
            expected_global_cap, rel=1e-2
        )


class TestTaxBracketCalculations:
    """Tests for ISR tax bracket calculations"""

    def test_low_income_uses_low_bracket(self, tax_service_2024):
        """Low income should use lower tax brackets"""
        income = IncomeData(
            monthly_gross_income=8000.0,  # Low income
            bonus_days=0,
            vacation_days=0,
            vacation_premium_percentage=0.0,
        )
        deductions = DeductionData(
            general_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
        )

        result = tax_service_2024.calculate_tax(income, deductions)

        # Effective rate should be low for low income
        assert result.effective_tax_rate < 15.0

    def test_high_income_uses_high_bracket(self, tax_service_2024):
        """High income should use higher tax brackets"""
        income = IncomeData(
            monthly_gross_income=150000.0,  # High income
            bonus_days=0,
            vacation_days=0,
            vacation_premium_percentage=0.0,
        )
        deductions = DeductionData(
            general_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
        )

        result = tax_service_2024.calculate_tax(income, deductions)

        # Effective rate should be higher for high income
        assert result.effective_tax_rate > 25.0

    def test_tax_is_progressive(self, tax_service_2024):
        """Higher income should result in higher effective tax rate"""
        deductions = DeductionData(
            general_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
        )

        income_low = IncomeData(
            monthly_gross_income=15000.0,
            bonus_days=0,
            vacation_days=0,
            vacation_premium_percentage=0.0,
        )
        income_high = IncomeData(
            monthly_gross_income=100000.0,
            bonus_days=0,
            vacation_days=0,
            vacation_premium_percentage=0.0,
        )

        result_low = tax_service_2024.calculate_tax(income_low, deductions)
        result_high = tax_service_2024.calculate_tax(income_high, deductions)

        assert result_high.effective_tax_rate > result_low.effective_tax_rate


class TestWithheldTaxAndBalance:
    """Tests for withheld tax and balance calculations"""

    def test_withheld_tax_calculated_correctly(
        self, tax_service_2024, income_medium, deductions_none
    ):
        """Withheld tax should be calculated on taxable income without deductions"""
        result = tax_service_2024.calculate_tax(income_medium, deductions_none)

        # Withheld tax should be positive for non-zero income
        assert result.withheld_tax > 0

    def test_deductions_create_refund(self, tax_service_2024, income_medium):
        """Deductions should create a tax refund (saldo a favor)"""
        deductions_high = DeductionData(
            general_deductions=50000.0,
            ppr_deductions=30000.0,
            education_deductions=10000.0,
        )

        result = tax_service_2024.calculate_tax(income_medium, deductions_high)

        # With deductions, determined tax < withheld tax → refund
        assert result.determined_tax < result.withheld_tax
        assert result.balance_in_favor > 0
        assert result.balance_to_pay == 0

    def test_no_deductions_may_result_in_balance_to_pay(self, tax_service_2024):
        """No deductions with bonus may result in tax owed"""
        income_with_bonus = IncomeData(
            monthly_gross_income=50000.0,
            bonus_days=30,  # Large bonus
            vacation_days=20,
            vacation_premium_percentage=0.25,
        )
        deductions = DeductionData(
            general_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
        )

        result = tax_service_2024.calculate_tax(income_with_bonus, deductions)

        # Either refund or owed, but both can't be positive
        assert not (result.balance_in_favor > 0 and result.balance_to_pay > 0)

    def test_balance_is_difference_of_withheld_and_determined(
        self, tax_service_2024, income_medium, deductions_small
    ):
        """Balance should be the difference between withheld and determined tax"""
        result = tax_service_2024.calculate_tax(income_medium, deductions_small)

        difference = result.withheld_tax - result.determined_tax
        if difference >= 0:
            assert result.balance_in_favor == pytest.approx(difference, rel=1e-5)
            assert result.balance_to_pay == 0
        else:
            assert result.balance_to_pay == pytest.approx(-difference, rel=1e-5)
            assert result.balance_in_favor == 0


class TestTotalTaxableIncome:
    """Tests for total taxable income calculations"""

    def test_total_taxable_includes_salary_bonus_and_premium(self, tax_service_2024):
        """Total taxable income should include salary, taxable bonus, and taxable premium"""
        income = IncomeData(
            monthly_gross_income=30000.0,  # Annual = 360k
            bonus_days=15,  # Bonus = 15k, taxable = ~11.7k
            vacation_days=12,
            vacation_premium_percentage=0.25,  # Premium = 3k
        )
        deductions = DeductionData(
            general_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
        )

        result = tax_service_2024.calculate_tax(income, deductions)

        # Total taxable = annual salary + taxable bonus + taxable premium
        expected_total = (
            income.annual_gross_income
            + result.taxable_bonus
            + result.taxable_vacation_premium
        )
        assert result.total_taxable_income == pytest.approx(expected_total, rel=1e-5)

    def test_taxable_base_is_income_minus_deductions(
        self, tax_service_2024, income_medium
    ):
        """Taxable base should be total taxable income minus authorized deductions"""
        deductions = DeductionData(
            general_deductions=20000.0,
            ppr_deductions=10000.0,
            education_deductions=5000.0,
        )

        result = tax_service_2024.calculate_tax(income_medium, deductions)

        expected_base = result.total_taxable_income - result.authorized_deductions
        assert result.taxable_base == pytest.approx(max(0, expected_base), rel=1e-5)

    def test_taxable_base_never_negative(self, tax_service_2024):
        """Taxable base should never be negative"""
        income = IncomeData(
            monthly_gross_income=5000.0,  # Low income
            bonus_days=0,
            vacation_days=0,
            vacation_premium_percentage=0.0,
        )
        # Large deductions (won't be fully applied due to caps anyway)
        deductions = DeductionData(
            general_deductions=100000.0,
            ppr_deductions=50000.0,
            education_deductions=20000.0,
        )

        result = tax_service_2024.calculate_tax(income, deductions)

        assert result.taxable_base >= 0


class TestProportionalReduction:
    """Tests for proportional reduction of deductions when exceeding global cap"""

    def test_deductions_reduced_proportionally(self, tax_service_2024):
        """When total exceeds cap, all deductions should be reduced proportionally"""
        income = IncomeData(
            monthly_gross_income=50000.0,  # Annual = 600k, 15% = 90k
            bonus_days=0,
            vacation_days=0,
            vacation_premium_percentage=0.0,
        )
        # Total deductions = 100k, but cap is 90k (15%)
        deductions = DeductionData(
            general_deductions=50000.0,  # 50%
            ppr_deductions=30000.0,  # 30%
            education_deductions=20000.0,  # 20%
        )

        result = tax_service_2024.calculate_tax(income, deductions)

        # Total should be capped at 90k
        assert result.authorized_deductions == pytest.approx(90000.0, rel=1e-2)

        # Each type should be proportionally reduced
        total_original = 100000.0
        factor = 90000.0 / total_original

        # Note: Individual caps may apply first, so this is approximate
        assert result.personal_deductions <= 50000.0 * factor + 1
        assert result.ppr_deductions <= 30000.0 * factor + 1


class TestCrossYearCalculations:
    """Tests to verify calculations work across different fiscal years"""

    @pytest.mark.parametrize("fiscal_year", [2024, 2025, 2026])
    def test_calculation_works_for_all_years(self, fiscal_year):
        """Tax calculation should work for all supported fiscal years"""
        service = TaxCalculationService(get_isr_table(fiscal_year))
        income = IncomeData(
            monthly_gross_income=25000.0,
            bonus_days=15,
            vacation_days=12,
            vacation_premium_percentage=0.25,
        )
        deductions = DeductionData(
            general_deductions=20000.0,
            ppr_deductions=10000.0,
            education_deductions=5000.0,
        )

        result = service.calculate_tax(income, deductions)

        assert result.gross_annual_income > 0
        assert result.determined_tax >= 0
        assert result.taxable_base >= 0

    def test_higher_uma_means_more_exemptions(self):
        """Higher UMA (2026 vs 2024) should result in more exemptions"""
        income = IncomeData(
            monthly_gross_income=30000.0,
            bonus_days=15,
            vacation_days=12,
            vacation_premium_percentage=0.25,
        )
        deductions = DeductionData(
            general_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
        )

        service_2024 = TaxCalculationService(get_isr_table(2024))
        service_2026 = TaxCalculationService(get_isr_table(2026))

        result_2024 = service_2024.calculate_tax(income, deductions)
        result_2026 = service_2026.calculate_tax(income, deductions)

        # Higher UMA = more exempt = less taxable bonus
        assert result_2026.taxable_bonus < result_2024.taxable_bonus
        assert (
            result_2026.taxable_vacation_premium < result_2024.taxable_vacation_premium
        )


class TestEdgeCases:
    """Edge case tests"""

    def test_very_small_income(self, tax_service_2024):
        """Very small income should calculate correctly"""
        income = IncomeData(
            monthly_gross_income=100.0,  # Very small
            bonus_days=1,
            vacation_days=1,
            vacation_premium_percentage=0.25,
        )
        deductions = DeductionData(
            general_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
        )

        result = tax_service_2024.calculate_tax(income, deductions)

        assert result.gross_annual_income > 0
        assert result.determined_tax >= 0

    def test_very_large_income(self, tax_service_2024):
        """Very large income should calculate correctly"""
        income = IncomeData(
            monthly_gross_income=10_000_000.0,  # 10 million/month
            bonus_days=30,
            vacation_days=20,
            vacation_premium_percentage=0.25,
        )
        deductions = DeductionData(
            general_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
        )

        result = tax_service_2024.calculate_tax(income, deductions)

        # Should use top bracket (35%)
        assert result.determined_tax > 0
        # Effective rate should be close to max
        assert result.effective_tax_rate > 30.0

    def test_only_bonus_income(self, tax_service_2024):
        """Income with only bonus (no salary) should work"""
        # This is unusual but valid - e.g., someone who worked only Dec
        income = IncomeData(
            monthly_gross_income=0.0,
            bonus_days=15,  # This will be 0 since daily = 0
            vacation_days=0,
            vacation_premium_percentage=0.0,
        )
        deductions = DeductionData(
            general_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
        )

        result = tax_service_2024.calculate_tax(income, deductions)

        assert result.gross_annual_income == 0.0
        assert result.determined_tax == 0.0

    def test_maximum_allowed_deductions(self, tax_service_2024):
        """Maximum possible deductions should be calculated correctly"""
        # Very high income to maximize deduction cap
        income = IncomeData(
            monthly_gross_income=500000.0,  # 6M annual
            bonus_days=0,
            vacation_days=0,
            vacation_premium_percentage=0.0,
        )
        # Maximum deductions in all categories
        deductions = DeductionData(
            general_deductions=1_000_000.0,
            ppr_deductions=1_000_000.0,
            education_deductions=100000.0,
        )

        result = tax_service_2024.calculate_tax(income, deductions)

        # Should be capped at 5 UMAs (since 5 UMAs < 15% for high income)
        uma_annual = 39606.36
        expected_cap = uma_annual * 5
        assert result.authorized_deductions == pytest.approx(expected_cap, rel=1e-2)
