from dataclasses import dataclass
from typing import Any


@dataclass
class TaxCalculation:
    """
    Pure domain entity representing a tax calculation result.
    Contains no business logic, only data and simple computed properties.
    """

    gross_annual_income: float
    taxable_bonus: float
    taxable_vacation_premium: float
    total_taxable_income: float

    authorized_deductions: float
    personal_deductions: float
    ppr_deductions: float
    education_deductions: float

    taxable_base: float
    determined_tax: float
    withheld_tax: float

    balance_in_favor: float
    balance_to_pay: float

    def __post_init__(self):
        """Validate that all amounts are non-negative"""
        for field_name, value in self.__dict__.items():
            if value < 0:
                raise ValueError(f"{field_name} cannot be negative: {value}")

    @property
    def effective_tax_rate(self) -> float:
        """Calculates the effective tax rate as a percentage"""
        if self.total_taxable_income > 0:
            return (self.determined_tax / self.total_taxable_income) * 100
        return 0.0

    @property
    def deduction_efficiency(self) -> float:
        """Calculates deduction efficiency as a percentage of gross income"""
        if self.gross_annual_income > 0:
            return (self.authorized_deductions / self.gross_annual_income) * 100
        return 0.0

    @property
    def is_refund_due(self) -> bool:
        """Checks if the taxpayer is due a refund"""
        return self.balance_in_favor > 0

    @property
    def net_tax_impact(self) -> float:
        """Gets the net tax impact (positive = owe, negative = refund)"""
        return self.balance_to_pay - self.balance_in_favor

    def to_dict(self) -> dict[str, Any]:
        """Converts entity to dictionary representation"""
        return {
            "gross_annual_income": self.gross_annual_income,
            "taxable_bonus": self.taxable_bonus,
            "taxable_vacation_premium": self.taxable_vacation_premium,
            "total_taxable_income": self.total_taxable_income,
            "authorized_deductions": self.authorized_deductions,
            "personal_deductions": self.personal_deductions,
            "ppr_deductions": self.ppr_deductions,
            "education_deductions": self.education_deductions,
            "taxable_base": self.taxable_base,
            "determined_tax": self.determined_tax,
            "withheld_tax": self.withheld_tax,
            "balance_in_favor": self.balance_in_favor,
            "balance_to_pay": self.balance_to_pay,
        }

    def get_summary(self) -> dict[str, Any]:
        """Returns a comprehensive summary of the tax calculation"""
        return {
            "income_summary": {
                "gross_annual": self.gross_annual_income,
                "total_taxable": self.total_taxable_income,
                "effective_tax_rate": f"{self.effective_tax_rate:.2f}%",
            },
            "deduction_summary": {
                "total_deductions": self.authorized_deductions,
                "deduction_efficiency": f"{self.deduction_efficiency:.2f}%",
                "breakdown": {
                    "personal": self.personal_deductions,
                    "ppr": self.ppr_deductions,
                    "education": self.education_deductions,
                },
            },
            "tax_summary": {
                "taxable_base": self.taxable_base,
                "determined_tax": self.determined_tax,
                "withheld_tax": self.withheld_tax,
                "net_impact": self.net_tax_impact,
                "refund_due": self.is_refund_due,
            },
        }
