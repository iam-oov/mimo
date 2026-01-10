"""
Tests for ISR tables and constants.
Validates that tax brackets and UMA values are correctly defined.
"""

import pytest

from src.shared.domain.constants.isr_tables import (
    ISR_TABLE_2024,
    ISR_TABLE_2025,
    ISR_TABLE_2026,
    ISR_TABLES,
    get_isr_table,
)


class TestISRTableStructure:
    """Tests for ISR table structure and completeness"""

    def test_all_fiscal_years_are_available(self):
        """Verify all expected fiscal years have tables"""
        expected_years = {2024, 2025, 2026}
        assert set(ISR_TABLES.keys()) == expected_years

    @pytest.mark.parametrize("fiscal_year", [2024, 2025, 2026])
    def test_get_isr_table_returns_correct_year(self, fiscal_year: int):
        """get_isr_table returns table for requested year"""
        table = get_isr_table(fiscal_year)
        assert table.fiscal_year == fiscal_year

    def test_get_isr_table_unknown_year_returns_latest(self):
        """Unknown fiscal year returns the latest available table"""
        table = get_isr_table(2030)
        assert table.fiscal_year == max(ISR_TABLES.keys())

    def test_get_isr_table_past_year_returns_latest(self):
        """Past year not in tables returns latest available"""
        table = get_isr_table(2020)
        assert table.fiscal_year == max(ISR_TABLES.keys())


class TestISRConstants:
    """Tests for ISR constants values"""

    @pytest.mark.parametrize(
        "fiscal_year,expected_daily_uma",
        [
            (2024, 108.57),
            (2025, 108.57),
            (2026, 117.31),
        ],
    )
    def test_daily_uma_values(self, fiscal_year: int, expected_daily_uma: float):
        """Verify daily UMA values are correct"""
        table = get_isr_table(fiscal_year)
        assert table.constants.daily_uma_value == expected_daily_uma

    @pytest.mark.parametrize("fiscal_year", [2024, 2025, 2026])
    def test_annual_uma_is_reasonable_multiple_of_daily(self, fiscal_year: int):
        """Annual UMA should be within expected range of daily * ~365"""
        table = get_isr_table(fiscal_year)
        daily = table.constants.daily_uma_value
        annual = table.constants.annual_uma_value
        # SAT uses official published values, not simple daily * 365
        # Annual should be between 360-366 days worth
        ratio = annual / daily
        assert 360 <= ratio <= 366, f"Annual/daily ratio {ratio} out of expected range"

    @pytest.mark.parametrize("fiscal_year", [2024, 2025, 2026])
    def test_bonus_exemption_is_30_umas(self, fiscal_year: int):
        """Bonus exemption should always be 30 daily UMAs"""
        table = get_isr_table(fiscal_year)
        assert table.constants.bonus_exemption_umas == 30

    @pytest.mark.parametrize("fiscal_year", [2024, 2025, 2026])
    def test_vacation_premium_exemption_is_15_umas(self, fiscal_year: int):
        """Vacation premium exemption should always be 15 daily UMAs"""
        table = get_isr_table(fiscal_year)
        assert table.constants.vacation_premium_exemption_umas == 15

    @pytest.mark.parametrize("fiscal_year", [2024, 2025, 2026])
    def test_deduction_caps_are_5_umas(self, fiscal_year: int):
        """General and PPR deduction caps should be 5 annual UMAs"""
        table = get_isr_table(fiscal_year)
        assert table.constants.general_deduction_cap_umas == 5.0
        assert table.constants.ppr_deduction_cap_umas == 5.0


class TestTuitionLimits:
    """Tests for tuition deductibility limits"""

    @pytest.mark.parametrize("fiscal_year", [2024, 2025, 2026])
    def test_tuition_limits_are_positive(self, fiscal_year: int):
        """All tuition limits should be positive"""
        table = get_isr_table(fiscal_year)
        limits = table.tuition_limits

        assert limits.preschool > 0
        assert limits.elementary > 0
        assert limits.middle_school > 0
        assert limits.technical_professional > 0
        assert limits.high_school > 0

    @pytest.mark.parametrize("fiscal_year", [2024, 2025, 2026])
    def test_high_school_has_highest_limit(self, fiscal_year: int):
        """High school should have the highest tuition limit"""
        table = get_isr_table(fiscal_year)
        limits = table.tuition_limits

        all_limits = [
            limits.preschool,
            limits.elementary,
            limits.middle_school,
            limits.technical_professional,
            limits.high_school,
        ]
        assert limits.high_school == max(all_limits)

    def test_tuition_limits_2024_values(self):
        """Verify exact tuition limits for 2024"""
        table = get_isr_table(2024)
        limits = table.tuition_limits

        assert limits.preschool == 14200.0
        assert limits.elementary == 12900.0
        assert limits.middle_school == 19900.0
        assert limits.technical_professional == 17100.0
        assert limits.high_school == 24500.0


class TestMonthlyISRBrackets:
    """Tests for monthly ISR tax brackets"""

    @pytest.mark.parametrize("fiscal_year", [2024, 2025, 2026])
    def test_brackets_start_at_001(self, fiscal_year: int):
        """First bracket should start at 0.01"""
        table = get_isr_table(fiscal_year)
        first_bracket = table.monthly_isr_table[0]
        assert first_bracket.lower_limit == 0.01

    @pytest.mark.parametrize("fiscal_year", [2024, 2025, 2026])
    def test_last_bracket_is_infinity(self, fiscal_year: int):
        """Last bracket upper limit should be infinity"""
        table = get_isr_table(fiscal_year)
        last_bracket = table.monthly_isr_table[-1]
        assert last_bracket.upper_limit == float("inf")

    @pytest.mark.parametrize("fiscal_year", [2024, 2025, 2026])
    def test_brackets_are_contiguous(self, fiscal_year: int):
        """Brackets should be contiguous (no gaps)"""
        table = get_isr_table(fiscal_year)
        brackets = table.monthly_isr_table

        for i in range(len(brackets) - 1):
            current_upper = brackets[i].upper_limit
            next_lower = brackets[i + 1].lower_limit
            # Allow 0.01 tolerance for rounding
            assert abs(next_lower - current_upper) <= 0.02

    @pytest.mark.parametrize("fiscal_year", [2024, 2025, 2026])
    def test_brackets_have_increasing_percentages(self, fiscal_year: int):
        """Tax percentages should generally increase (progressive tax)"""
        table = get_isr_table(fiscal_year)
        brackets = table.monthly_isr_table

        # First bracket has lowest percentage
        assert brackets[0].excess_percentage < brackets[-1].excess_percentage

    @pytest.mark.parametrize("fiscal_year", [2024, 2025, 2026])
    def test_first_bracket_has_zero_fixed_fee(self, fiscal_year: int):
        """First bracket should have 0 fixed fee"""
        table = get_isr_table(fiscal_year)
        first_bracket = table.monthly_isr_table[0]
        assert first_bracket.fixed_fee == 0.0

    @pytest.mark.parametrize("fiscal_year", [2024, 2025, 2026])
    def test_fixed_fees_are_increasing(self, fiscal_year: int):
        """Fixed fees should increase with each bracket"""
        table = get_isr_table(fiscal_year)
        brackets = table.monthly_isr_table

        for i in range(len(brackets) - 1):
            assert brackets[i].fixed_fee <= brackets[i + 1].fixed_fee

    @pytest.mark.parametrize("fiscal_year", [2024, 2025, 2026])
    def test_max_percentage_is_35_percent(self, fiscal_year: int):
        """Maximum tax rate should be 35%"""
        table = get_isr_table(fiscal_year)
        last_bracket = table.monthly_isr_table[-1]
        assert last_bracket.excess_percentage == 0.35

    def test_2024_has_11_brackets(self):
        """2024 should have 11 tax brackets"""
        assert len(ISR_TABLE_2024.monthly_isr_table) == 11

    def test_2025_has_11_brackets(self):
        """2025 should have 11 tax brackets"""
        assert len(ISR_TABLE_2025.monthly_isr_table) == 11

    def test_2026_has_8_brackets(self):
        """2026 should have 8 tax brackets (simplified)"""
        assert len(ISR_TABLE_2026.monthly_isr_table) == 8


class TestTaxBracketCalculations:
    """Tests for specific tax bracket calculation scenarios"""

    def test_minimum_income_uses_first_bracket(self):
        """Income of $500/month should use first bracket (1.92%)"""
        table = get_isr_table(2024)
        first_bracket = table.monthly_isr_table[0]

        monthly_income = 500.0
        assert first_bracket.lower_limit <= monthly_income <= first_bracket.upper_limit
        assert first_bracket.excess_percentage == 0.0192

    def test_median_income_bracket(self):
        """Income of $20,000/month should use appropriate bracket"""
        table = get_isr_table(2024)

        monthly_income = 20000.0
        matching_bracket = None

        for bracket in table.monthly_isr_table:
            if bracket.lower_limit <= monthly_income <= bracket.upper_limit:
                matching_bracket = bracket
                break

        assert matching_bracket is not None
        # $20,000 falls in 21.36% bracket
        assert matching_bracket.excess_percentage == 0.2136

    def test_high_income_bracket(self):
        """Income of $100,000/month should use 32% bracket"""
        table = get_isr_table(2024)

        monthly_income = 100000.0
        matching_bracket = None

        for bracket in table.monthly_isr_table:
            if bracket.lower_limit <= monthly_income <= bracket.upper_limit:
                matching_bracket = bracket
                break

        assert matching_bracket is not None
        assert matching_bracket.excess_percentage == 0.32

    def test_very_high_income_uses_top_bracket(self):
        """Income of $500,000/month should use top 35% bracket"""
        table = get_isr_table(2024)

        monthly_income = 500000.0
        last_bracket = table.monthly_isr_table[-1]

        assert monthly_income >= last_bracket.lower_limit
        assert last_bracket.excess_percentage == 0.35


class TestCrossYearConsistency:
    """Tests to verify consistency across fiscal years"""

    def test_exemption_umas_consistent_across_years(self):
        """Exemption UMAs should be consistent across all years"""
        for year in [2024, 2025, 2026]:
            table = get_isr_table(year)
            assert table.constants.bonus_exemption_umas == 30
            assert table.constants.vacation_premium_exemption_umas == 15

    def test_deduction_caps_consistent_across_years(self):
        """Deduction caps (in UMAs) should be consistent"""
        for year in [2024, 2025, 2026]:
            table = get_isr_table(year)
            assert table.constants.general_deduction_cap_umas == 5.0
            assert table.constants.ppr_deduction_cap_umas == 5.0

    def test_uma_2026_higher_than_2024(self):
        """UMA value should increase over time"""
        uma_2024 = get_isr_table(2024).constants.daily_uma_value
        uma_2026 = get_isr_table(2026).constants.daily_uma_value
        assert uma_2026 > uma_2024
