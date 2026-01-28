"""
Tests for TaxCalculation entity.
Validates entity creation, properties, and methods.
"""

import pytest

from src.tax_calculation.domain.entities.tax_calculation import TaxCalculation


class TestTaxCalculationCreation:
    """Tests for TaxCalculation entity creation"""

    def test_valid_tax_calculation_creation(self):
        """Valid tax calculation entity is created successfully"""
        calc = TaxCalculation(
            gross_annual_income=300000.0,
            taxable_bonus=10000.0,
            taxable_vacation_premium=2000.0,
            total_taxable_income=312000.0,
            authorized_deductions=50000.0,
            personal_deductions=30000.0,
            ppr_deductions=15000.0,
            education_deductions=5000.0,
            taxable_base=262000.0,
            determined_tax=45000.0,
            withheld_tax=50000.0,
            balance_in_favor=5000.0,
            balance_to_pay=0.0,
        )

        assert calc.gross_annual_income == 300000.0
        assert calc.taxable_bonus == 10000.0
        assert calc.balance_in_favor == 5000.0

    def test_zero_values_are_valid(self):
        """Zero values should be valid"""
        calc = TaxCalculation(
            gross_annual_income=0.0,
            taxable_bonus=0.0,
            taxable_vacation_premium=0.0,
            total_taxable_income=0.0,
            authorized_deductions=0.0,
            personal_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
            taxable_base=0.0,
            determined_tax=0.0,
            withheld_tax=0.0,
            balance_in_favor=0.0,
            balance_to_pay=0.0,
        )

        assert calc.gross_annual_income == 0.0
        assert calc.determined_tax == 0.0

    def test_negative_gross_income_raises_error(self):
        """Negative gross income should raise ValueError"""
        with pytest.raises(ValueError, match="gross_annual_income cannot be negative"):
            TaxCalculation(
                gross_annual_income=-100.0,
                taxable_bonus=0.0,
                taxable_vacation_premium=0.0,
                total_taxable_income=0.0,
                authorized_deductions=0.0,
                personal_deductions=0.0,
                ppr_deductions=0.0,
                education_deductions=0.0,
                taxable_base=0.0,
                determined_tax=0.0,
                withheld_tax=0.0,
                balance_in_favor=0.0,
                balance_to_pay=0.0,
            )

    def test_negative_taxable_bonus_raises_error(self):
        """Negative taxable bonus should raise ValueError"""
        with pytest.raises(ValueError, match="taxable_bonus cannot be negative"):
            TaxCalculation(
                gross_annual_income=100000.0,
                taxable_bonus=-500.0,
                taxable_vacation_premium=0.0,
                total_taxable_income=100000.0,
                authorized_deductions=0.0,
                personal_deductions=0.0,
                ppr_deductions=0.0,
                education_deductions=0.0,
                taxable_base=100000.0,
                determined_tax=10000.0,
                withheld_tax=10000.0,
                balance_in_favor=0.0,
                balance_to_pay=0.0,
            )

    def test_negative_determined_tax_raises_error(self):
        """Negative determined tax should raise ValueError"""
        with pytest.raises(ValueError, match="determined_tax cannot be negative"):
            TaxCalculation(
                gross_annual_income=100000.0,
                taxable_bonus=0.0,
                taxable_vacation_premium=0.0,
                total_taxable_income=100000.0,
                authorized_deductions=0.0,
                personal_deductions=0.0,
                ppr_deductions=0.0,
                education_deductions=0.0,
                taxable_base=100000.0,
                determined_tax=-1000.0,
                withheld_tax=10000.0,
                balance_in_favor=0.0,
                balance_to_pay=0.0,
            )

    def test_negative_balance_in_favor_raises_error(self):
        """Negative balance in favor should raise ValueError"""
        with pytest.raises(ValueError, match="balance_in_favor cannot be negative"):
            TaxCalculation(
                gross_annual_income=100000.0,
                taxable_bonus=0.0,
                taxable_vacation_premium=0.0,
                total_taxable_income=100000.0,
                authorized_deductions=0.0,
                personal_deductions=0.0,
                ppr_deductions=0.0,
                education_deductions=0.0,
                taxable_base=100000.0,
                determined_tax=10000.0,
                withheld_tax=10000.0,
                balance_in_favor=-100.0,
                balance_to_pay=0.0,
            )


class TestEffectiveTaxRate:
    """Tests for effective_tax_rate property"""

    def test_effective_tax_rate_calculation(self):
        """Effective tax rate should be (determined_tax / total_taxable_income) * 100"""
        calc = TaxCalculation(
            gross_annual_income=300000.0,
            taxable_bonus=0.0,
            taxable_vacation_premium=0.0,
            total_taxable_income=300000.0,
            authorized_deductions=0.0,
            personal_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
            taxable_base=300000.0,
            determined_tax=60000.0,  # 20% of 300k
            withheld_tax=60000.0,
            balance_in_favor=0.0,
            balance_to_pay=0.0,
        )

        assert calc.effective_tax_rate == pytest.approx(20.0, rel=1e-5)

    def test_effective_tax_rate_zero_income(self):
        """Effective tax rate should be 0 when income is zero"""
        calc = TaxCalculation(
            gross_annual_income=0.0,
            taxable_bonus=0.0,
            taxable_vacation_premium=0.0,
            total_taxable_income=0.0,
            authorized_deductions=0.0,
            personal_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
            taxable_base=0.0,
            determined_tax=0.0,
            withheld_tax=0.0,
            balance_in_favor=0.0,
            balance_to_pay=0.0,
        )

        assert calc.effective_tax_rate == 0.0

    def test_effective_tax_rate_low_income(self):
        """Low income should have low effective tax rate"""
        calc = TaxCalculation(
            gross_annual_income=100000.0,
            taxable_bonus=0.0,
            taxable_vacation_premium=0.0,
            total_taxable_income=100000.0,
            authorized_deductions=0.0,
            personal_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
            taxable_base=100000.0,
            determined_tax=5000.0,  # 5%
            withheld_tax=5000.0,
            balance_in_favor=0.0,
            balance_to_pay=0.0,
        )

        assert calc.effective_tax_rate == pytest.approx(5.0, rel=1e-5)


class TestDeductionEfficiency:
    """Tests for deduction_efficiency property"""

    def test_deduction_efficiency_calculation(self):
        """Deduction efficiency = (deductions / gross_income) * 100"""
        calc = TaxCalculation(
            gross_annual_income=500000.0,
            taxable_bonus=0.0,
            taxable_vacation_premium=0.0,
            total_taxable_income=500000.0,
            authorized_deductions=50000.0,  # 10% of 500k
            personal_deductions=30000.0,
            ppr_deductions=15000.0,
            education_deductions=5000.0,
            taxable_base=450000.0,
            determined_tax=100000.0,
            withheld_tax=100000.0,
            balance_in_favor=0.0,
            balance_to_pay=0.0,
        )

        assert calc.deduction_efficiency == pytest.approx(10.0, rel=1e-5)

    def test_deduction_efficiency_zero_income(self):
        """Deduction efficiency should be 0 when income is zero"""
        calc = TaxCalculation(
            gross_annual_income=0.0,
            taxable_bonus=0.0,
            taxable_vacation_premium=0.0,
            total_taxable_income=0.0,
            authorized_deductions=0.0,
            personal_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
            taxable_base=0.0,
            determined_tax=0.0,
            withheld_tax=0.0,
            balance_in_favor=0.0,
            balance_to_pay=0.0,
        )

        assert calc.deduction_efficiency == 0.0

    def test_deduction_efficiency_no_deductions(self):
        """No deductions should result in 0% efficiency"""
        calc = TaxCalculation(
            gross_annual_income=300000.0,
            taxable_bonus=0.0,
            taxable_vacation_premium=0.0,
            total_taxable_income=300000.0,
            authorized_deductions=0.0,
            personal_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
            taxable_base=300000.0,
            determined_tax=50000.0,
            withheld_tax=50000.0,
            balance_in_favor=0.0,
            balance_to_pay=0.0,
        )

        assert calc.deduction_efficiency == 0.0


class TestIsRefundDue:
    """Tests for is_refund_due property"""

    def test_refund_due_when_balance_in_favor(self):
        """Refund should be due when balance_in_favor > 0"""
        calc = TaxCalculation(
            gross_annual_income=300000.0,
            taxable_bonus=0.0,
            taxable_vacation_premium=0.0,
            total_taxable_income=300000.0,
            authorized_deductions=50000.0,
            personal_deductions=50000.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
            taxable_base=250000.0,
            determined_tax=40000.0,
            withheld_tax=50000.0,
            balance_in_favor=10000.0,
            balance_to_pay=0.0,
        )

        assert calc.is_refund_due is True

    def test_no_refund_when_balance_to_pay(self):
        """No refund should be due when balance_to_pay > 0"""
        calc = TaxCalculation(
            gross_annual_income=300000.0,
            taxable_bonus=10000.0,
            taxable_vacation_premium=0.0,
            total_taxable_income=310000.0,
            authorized_deductions=0.0,
            personal_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
            taxable_base=310000.0,
            determined_tax=55000.0,
            withheld_tax=50000.0,
            balance_in_favor=0.0,
            balance_to_pay=5000.0,
        )

        assert calc.is_refund_due is False

    def test_no_refund_when_zero_balance(self):
        """No refund when both balances are zero"""
        calc = TaxCalculation(
            gross_annual_income=300000.0,
            taxable_bonus=0.0,
            taxable_vacation_premium=0.0,
            total_taxable_income=300000.0,
            authorized_deductions=0.0,
            personal_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
            taxable_base=300000.0,
            determined_tax=50000.0,
            withheld_tax=50000.0,
            balance_in_favor=0.0,
            balance_to_pay=0.0,
        )

        assert calc.is_refund_due is False


class TestNetTaxImpact:
    """Tests for net_tax_impact property"""

    def test_negative_impact_means_refund(self):
        """Negative net impact means taxpayer gets a refund"""
        calc = TaxCalculation(
            gross_annual_income=300000.0,
            taxable_bonus=0.0,
            taxable_vacation_premium=0.0,
            total_taxable_income=300000.0,
            authorized_deductions=50000.0,
            personal_deductions=50000.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
            taxable_base=250000.0,
            determined_tax=40000.0,
            withheld_tax=50000.0,
            balance_in_favor=10000.0,
            balance_to_pay=0.0,
        )

        assert calc.net_tax_impact == -10000.0

    def test_positive_impact_means_owe(self):
        """Positive net impact means taxpayer owes money"""
        calc = TaxCalculation(
            gross_annual_income=300000.0,
            taxable_bonus=20000.0,
            taxable_vacation_premium=0.0,
            total_taxable_income=320000.0,
            authorized_deductions=0.0,
            personal_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
            taxable_base=320000.0,
            determined_tax=58000.0,
            withheld_tax=50000.0,
            balance_in_favor=0.0,
            balance_to_pay=8000.0,
        )

        assert calc.net_tax_impact == 8000.0

    def test_zero_impact_means_even(self):
        """Zero net impact means taxpayer is even"""
        calc = TaxCalculation(
            gross_annual_income=300000.0,
            taxable_bonus=0.0,
            taxable_vacation_premium=0.0,
            total_taxable_income=300000.0,
            authorized_deductions=0.0,
            personal_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
            taxable_base=300000.0,
            determined_tax=50000.0,
            withheld_tax=50000.0,
            balance_in_favor=0.0,
            balance_to_pay=0.0,
        )

        assert calc.net_tax_impact == 0.0


class TestToDict:
    """Tests for to_dict method"""

    def test_to_dict_contains_all_fields(self):
        """to_dict should contain all entity fields"""
        calc = TaxCalculation(
            gross_annual_income=300000.0,
            taxable_bonus=10000.0,
            taxable_vacation_premium=2000.0,
            total_taxable_income=312000.0,
            authorized_deductions=50000.0,
            personal_deductions=30000.0,
            ppr_deductions=15000.0,
            education_deductions=5000.0,
            taxable_base=262000.0,
            determined_tax=45000.0,
            withheld_tax=50000.0,
            balance_in_favor=5000.0,
            balance_to_pay=0.0,
        )

        result = calc.to_dict()

        assert result["gross_annual_income"] == 300000.0
        assert result["taxable_bonus"] == 10000.0
        assert result["taxable_vacation_premium"] == 2000.0
        assert result["total_taxable_income"] == 312000.0
        assert result["authorized_deductions"] == 50000.0
        assert result["personal_deductions"] == 30000.0
        assert result["ppr_deductions"] == 15000.0
        assert result["education_deductions"] == 5000.0
        assert result["taxable_base"] == 262000.0
        assert result["determined_tax"] == 45000.0
        assert result["withheld_tax"] == 50000.0
        assert result["balance_in_favor"] == 5000.0
        assert result["balance_to_pay"] == 0.0

    def test_to_dict_has_correct_keys(self):
        """to_dict should have exactly 13 keys"""
        calc = TaxCalculation(
            gross_annual_income=100000.0,
            taxable_bonus=0.0,
            taxable_vacation_premium=0.0,
            total_taxable_income=100000.0,
            authorized_deductions=0.0,
            personal_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
            taxable_base=100000.0,
            determined_tax=10000.0,
            withheld_tax=10000.0,
            balance_in_favor=0.0,
            balance_to_pay=0.0,
        )

        result = calc.to_dict()
        expected_keys = {
            "gross_annual_income",
            "taxable_bonus",
            "taxable_vacation_premium",
            "total_taxable_income",
            "authorized_deductions",
            "personal_deductions",
            "ppr_deductions",
            "education_deductions",
            "taxable_base",
            "determined_tax",
            "withheld_tax",
            "balance_in_favor",
            "balance_to_pay",
        }

        assert set(result.keys()) == expected_keys


class TestGetSummary:
    """Tests for get_summary method"""

    def test_get_summary_structure(self):
        """get_summary should return correct structure"""
        calc = TaxCalculation(
            gross_annual_income=300000.0,
            taxable_bonus=10000.0,
            taxable_vacation_premium=2000.0,
            total_taxable_income=312000.0,
            authorized_deductions=50000.0,
            personal_deductions=30000.0,
            ppr_deductions=15000.0,
            education_deductions=5000.0,
            taxable_base=262000.0,
            determined_tax=45000.0,
            withheld_tax=50000.0,
            balance_in_favor=5000.0,
            balance_to_pay=0.0,
        )

        summary = calc.get_summary()

        assert "income_summary" in summary
        assert "deduction_summary" in summary
        assert "tax_summary" in summary

    def test_get_summary_income_section(self):
        """get_summary income section should have correct values"""
        calc = TaxCalculation(
            gross_annual_income=300000.0,
            taxable_bonus=0.0,
            taxable_vacation_premium=0.0,
            total_taxable_income=300000.0,
            authorized_deductions=0.0,
            personal_deductions=0.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
            taxable_base=300000.0,
            determined_tax=60000.0,
            withheld_tax=60000.0,
            balance_in_favor=0.0,
            balance_to_pay=0.0,
        )

        summary = calc.get_summary()
        income = summary["income_summary"]

        assert income["gross_annual"] == 300000.0
        assert income["total_taxable"] == 300000.0
        assert income["effective_tax_rate"] == "20.00%"

    def test_get_summary_deduction_section(self):
        """get_summary deduction section should have correct values"""
        calc = TaxCalculation(
            gross_annual_income=500000.0,
            taxable_bonus=0.0,
            taxable_vacation_premium=0.0,
            total_taxable_income=500000.0,
            authorized_deductions=50000.0,
            personal_deductions=30000.0,
            ppr_deductions=15000.0,
            education_deductions=5000.0,
            taxable_base=450000.0,
            determined_tax=100000.0,
            withheld_tax=100000.0,
            balance_in_favor=0.0,
            balance_to_pay=0.0,
        )

        summary = calc.get_summary()
        deductions = summary["deduction_summary"]

        assert deductions["total_deductions"] == 50000.0
        assert deductions["deduction_efficiency"] == "10.00%"
        assert deductions["breakdown"]["personal"] == 30000.0
        assert deductions["breakdown"]["ppr"] == 15000.0
        assert deductions["breakdown"]["education"] == 5000.0

    def test_get_summary_tax_section(self):
        """get_summary tax section should have correct values"""
        calc = TaxCalculation(
            gross_annual_income=300000.0,
            taxable_bonus=0.0,
            taxable_vacation_premium=0.0,
            total_taxable_income=300000.0,
            authorized_deductions=50000.0,
            personal_deductions=50000.0,
            ppr_deductions=0.0,
            education_deductions=0.0,
            taxable_base=250000.0,
            determined_tax=40000.0,
            withheld_tax=50000.0,
            balance_in_favor=10000.0,
            balance_to_pay=0.0,
        )

        summary = calc.get_summary()
        tax = summary["tax_summary"]

        assert tax["taxable_base"] == 250000.0
        assert tax["determined_tax"] == 40000.0
        assert tax["withheld_tax"] == 50000.0
        assert tax["net_impact"] == -10000.0
        assert tax["refund_due"] is True
