from pydantic import BaseModel, Field


class TaxCalculationRequest(BaseModel):
    """API schema for tax calculation request"""

    taxpayer_name: str = Field(
        default="", description="Full name of the taxpayer", max_length=100
    )
    fiscal_year: int = Field(
        default=2025, description="Tax fiscal year", ge=2024, le=2025
    )
    monthly_gross_income: float = Field(
        default=0.0, description="Monthly gross income", ge=0.0, le=1000000.0
    )
    monthly_net_income: float = Field(
        default=0.0, description="Monthly net income", ge=0.0
    )
    bonus_days: int = Field(
        default=15, description="Number of bonus days (aguinaldo)", ge=0, le=365
    )
    vacation_days: int = Field(
        default=12, description="Number of annual vacation days", ge=0, le=365
    )
    vacation_premium_percentage: float = Field(
        default=0.25,
        description="Vacation premium percentage (e.g., 0.25 for 25%)",
        ge=0.0,
        le=1.0,
    )
    general_deductions: float = Field(
        default=0.0,
        description="🏥 Total general deductions (Medical, Funeral, Donations, Mortgage, etc.)",
        ge=0.0,
        le=10000000.0,
    )
    total_tuition: float = Field(
        default=0.0,
        description="🎓 Total tuition expenses for all education levels",
        ge=0.0,
        le=1000000.0,
    )
    total_ppr: float = Field(
        default=0.0, description="💰 Total PPR contributions", ge=0.0, le=1000000.0
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "taxpayer_name": "Juan Pérez",
                "fiscal_year": 2025,
                "monthly_gross_income": 12600.00,
                "monthly_net_income": 10500.00,
                "bonus_days": 15,
                "vacation_days": 12,
                "vacation_premium_percentage": 0.25,
                "general_deductions": 71000.00,
                "total_tuition": 25000.00,
                "total_ppr": 15000.00,
            }
        }
    }


class TaxCalculationResponse(BaseModel):
    """API schema for tax calculation response"""

    gross_annual_income: float = Field(
        description="Total gross annual income including bonuses and premiums", ge=0.0
    )
    taxable_bonus: float = Field(
        description="Taxable portion of bonus (aguinaldo) after exemptions", ge=0.0
    )
    taxable_vacation_premium: float = Field(
        description="Taxable portion of vacation premium after exemptions", ge=0.0
    )
    total_taxable_income: float = Field(
        description="Total income subject to taxation", ge=0.0
    )
    authorized_deductions: float = Field(
        description="Total authorized deductions after caps and limits", ge=0.0
    )
    personal_deductions: float = Field(
        description="Personal deductions (medical, donations, etc.)", ge=0.0
    )
    ppr_deductions: float = Field(description="PPR (retirement) deductions", ge=0.0)
    education_deductions: float = Field(
        description="Education/tuition deductions", ge=0.0
    )
    taxable_base: float = Field(
        description="Final tax base after all deductions", ge=0.0
    )
    determined_tax: float = Field(
        description="Tax determined based on taxable base", ge=0.0
    )
    withheld_tax: float = Field(description="Tax withheld during the year", ge=0.0)
    balance_in_favor: float = Field(
        description="Amount in favor of taxpayer (refund)", ge=0.0
    )
    balance_to_pay: float = Field(description="Additional tax amount to pay", ge=0.0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "gross_annual_income": 151200.00,
                "taxable_bonus": 3150.00,
                "taxable_vacation_premium": 787.50,
                "total_taxable_income": 155137.50,
                "authorized_deductions": 71000.00,
                "personal_deductions": 58000.00,
                "ppr_deductions": 8000.00,
                "education_deductions": 5000.00,
                "taxable_base": 84137.50,
                "determined_tax": 12500.25,
                "withheld_tax": 15000.00,
                "balance_in_favor": 2499.75,
                "balance_to_pay": 0.00,
            }
        }
    }
