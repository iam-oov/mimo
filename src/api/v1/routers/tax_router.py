from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from src.api.v1.schemas.tax_schemas import TaxCalculationRequest, TaxCalculationResponse
from src.application.calculate_tax_use_case import (
    CalculateTaxUseCase,
    CalculateTaxRequest as UseCaseRequest,
)


router = APIRouter(prefix="/api", tags=["tax"])


@router.post("/calculate", response_model=TaxCalculationResponse)
def calculate_tax(request: TaxCalculationRequest) -> Dict[str, Any]:
    """
    Calculate annual tax balance for a taxpayer.

    This endpoint calculates:
    - Taxable income (with bonus/vacation exemptions)
    - Authorized deductions (applying all caps and limits)
    - Determined tax vs withheld tax
    - Final balance (refund or amount to pay)
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
