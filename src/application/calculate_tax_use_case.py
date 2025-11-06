from dataclasses import dataclass
from src.domain.entities.tax_calculation import TaxCalculation
from src.domain.value_objects.tax_data import TaxpayerInfo, IncomeData, DeductionData
from src.domain.services.tax_calculation_service import TaxCalculationService
from tabla_isr_constants import get_tabla_isr


@dataclass
class CalculateTaxRequest:
    """Request DTO for tax calculation use case"""

    taxpayer_name: str
    fiscal_year: int
    monthly_gross_income: float
    bonus_days: int
    vacation_days: int
    vacation_premium_percentage: float
    general_deductions: float
    ppr_deductions: float
    education_deductions: float


@dataclass
class CalculateTaxResponse:
    """Response DTO for tax calculation use case"""

    calculation: TaxCalculation
    taxpayer_info: TaxpayerInfo


class CalculateTaxUseCase:
    """
    Use case for calculating tax balance.
    Orchestrates domain services to fulfill the business requirement.
    """

    def execute(self, request: CalculateTaxRequest) -> CalculateTaxResponse:
        """
        Execute tax calculation use case.

        Args:
            request: Tax calculation request with user data

        Returns:
            Tax calculation response with results

        Raises:
            ValueError: If fiscal year is invalid or data validation fails
        """
        # Create value objects from request
        taxpayer_info = TaxpayerInfo(
            name=request.taxpayer_name, fiscal_year=request.fiscal_year
        )

        income_data = IncomeData(
            monthly_gross_income=request.monthly_gross_income,
            bonus_days=request.bonus_days,
            vacation_days=request.vacation_days,
            vacation_premium_percentage=request.vacation_premium_percentage,
        )

        deduction_data = DeductionData(
            general_deductions=request.general_deductions,
            ppr_deductions=request.ppr_deductions,
            education_deductions=request.education_deductions,
        )

        # Get ISR table for fiscal year
        isr_table = get_tabla_isr(request.fiscal_year)

        # Execute domain service
        tax_service = TaxCalculationService(isr_table)
        calculation = tax_service.calculate_tax(income_data, deduction_data)

        return CalculateTaxResponse(
            calculation=calculation, taxpayer_info=taxpayer_info
        )
