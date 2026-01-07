from typing import Any

from fastapi import APIRouter, HTTPException

from src.shared.infrastructure.api.schemas.tax_schemas import (
    TaxCalculationRequest,
    TaxCalculationResponse,
)
from src.tax_calculation.application.calculate_tax_use_case import (
    CalculateTaxRequest as UseCaseRequest,
)
from src.tax_calculation.application.calculate_tax_use_case import (
    CalculateTaxUseCase,
)

router = APIRouter(prefix="/api", tags=["tax"])


@router.post("/calculate", response_model=TaxCalculationResponse)
def calculate_tax(request: TaxCalculationRequest) -> dict[str, Any]:
    """
    Calculate annual tax balance (saldo a favor/a pagar) for Mexican individuals.

    Implements Mexican ISR (Impuesto Sobre la Renta) rules including:
    - Gross/taxable income calculation with UMA-based exemptions:
      * Aguinaldo (bonus): Exempt up to 30 UMAs daily
      * Prima vacacional (vacation premium): Exempt up to 15 UMAs daily
    - Authorized deductions with caps:
      * Personal/Medical/Funeral: Capped at 5 UMAs annually OR 15% gross income (whichever is lower)
      * PPR (Retirement contributions): Applied proportionally within cap
      * Education: By level (preschool to university), applied proportionally within cap
    - Monthly ISR calculation using progressive tax brackets
    - Final balance: Determined tax - Withheld tax = Refund (saldo a favor) or Amount to Pay

    Args:
        request: Tax calculation request with taxpayer info, income, and deductions

    Returns:
        TaxCalculationResponse with complete breakdown:
        - gross_annual_income
        - taxable_income
        - authorized_deductions
        - determined_tax
        - withheld_tax
        - final_balance (negative = refund, positive = amount to pay)
        - effective_tax_rate

    Raises:
        HTTPException 400: Invalid fiscal year or data validation error
        HTTPException 500: Internal calculation error

    Example:
        ```json
        {
          "taxpayer_name": "Juan Pérez",
          "fiscal_year": 2024,
          "monthly_gross_income": 15000.0,
          "bonus_days": 30,
          "vacation_days": 12,
          "vacation_premium_percentage": 25.0,
          "general_deductions": 50000.0,
          "total_ppr": 30000.0,
          "total_tuition": 20000.0
        }
        ```
    """
    try:
        # Map API request to use case request
        use_case_request = UseCaseRequest(
            taxpayer_name=request.taxpayer_name,
            fiscal_year=request.fiscal_year,
            monthly_gross_income=request.monthly_gross_income,
            bonus_days=request.bonus_days,
            vacation_days=request.vacation_days,
            vacation_premium_percentage=request.vacation_premium_percentage,
            general_deductions=request.general_deductions,
            ppr_deductions=request.total_ppr,
            education_deductions=request.total_tuition,
        )

        # Execute use case
        use_case = CalculateTaxUseCase()
        response = use_case.execute(use_case_request)

        # Map domain entity to API response
        return response.calculation.to_dict()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
