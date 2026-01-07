from dataclasses import dataclass


@dataclass(frozen=True)
class TaxpayerInfo:
    """
    Value object representing taxpayer information.
    Immutable by design (frozen=True).
    """

    name: str
    fiscal_year: int

    def __post_init__(self):
        if self.fiscal_year < 2024 or self.fiscal_year > 2025:
            raise ValueError(f"Fiscal year must be between 2024 and 2025, got {self.fiscal_year}")

        if not self.name or not self.name.strip():
            object.__setattr__(self, "name", "Contribuyente")


@dataclass(frozen=True)
class IncomeData:
    """
    Value object representing income information.
    Immutable by design.
    """

    monthly_gross_income: float
    bonus_days: int
    vacation_days: int
    vacation_premium_percentage: float

    def __post_init__(self):
        if self.monthly_gross_income < 0:
            raise ValueError("Monthly gross income cannot be negative")
        if self.bonus_days < 0 or self.bonus_days > 365:
            raise ValueError("Bonus days must be between 0 and 365")
        if self.vacation_days < 0 or self.vacation_days > 365:
            raise ValueError("Vacation days must be between 0 and 365")
        if self.vacation_premium_percentage < 0 or self.vacation_premium_percentage > 1:
            raise ValueError("Vacation premium percentage must be between 0 and 1")

    @property
    def daily_salary(self) -> float:
        """Calculate daily salary from monthly income"""
        return self.monthly_gross_income / 30

    @property
    def annual_gross_income(self) -> float:
        """Calculate annual gross income (without bonuses)"""
        return self.monthly_gross_income * 12

    @property
    def gross_bonus(self) -> float:
        """Calculate gross bonus amount"""
        return self.daily_salary * self.bonus_days

    @property
    def gross_vacation_premium(self) -> float:
        """Calculate gross vacation premium"""
        return self.daily_salary * self.vacation_days * self.vacation_premium_percentage


@dataclass(frozen=True)
class DeductionData:
    """
    Value object representing deduction information.
    Immutable by design.
    """

    general_deductions: float
    ppr_deductions: float
    education_deductions: float

    def __post_init__(self):
        if self.general_deductions < 0:
            raise ValueError("General deductions cannot be negative")
        if self.ppr_deductions < 0:
            raise ValueError("PPR deductions cannot be negative")
        if self.education_deductions < 0:
            raise ValueError("Education deductions cannot be negative")

    @property
    def total_uncapped(self) -> float:
        """Calculate total deductions before applying caps"""
        return self.general_deductions + self.ppr_deductions + self.education_deductions
