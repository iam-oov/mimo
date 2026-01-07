from dataclasses import dataclass

from src.domain.constants.isr_tables import get_tabla_isr
from src.domain.entities.tax_calculation import TaxCalculation
from src.domain.services.tax_calculation_service import TaxCalculationService
from src.domain.value_objects.tax_data import DeductionData, IncomeData, TaxpayerInfo
from src.infrastructure.logging.structured_logger import get_logger

logger = get_logger(__name__)


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
    Use case for calculating Mexican ISR annual tax balance.

    Orchestrates domain services to calculate annual tax balance (saldo a favor/a pagar) for
    individuals (personas físicas) under Mexican tax law. Implements all ISR rules including
    UMA-based exemptions, deduction caps, and progressive tax brackets.

    **Key Calculations:**
    1. **Gross Income**: Annual salary + taxable bonuses/vacation premiums
    2. **Exemptions**: Bonus (30 UMAs daily) + Vacation premium (15 UMAs daily)
    3. **Deductions**: Apply 5 UMAs OR 15% gross income cap (whichever is lower)
    4. **Determined Tax**: Monthly ISR sum using progressive brackets
    5. **Final Balance**: Determined tax - Withheld tax = Refund or Amount to Pay

    **Domain Layer Interaction:**
    - Uses `TaxCalculationService` for business logic
    - Uses `TablaISR` constants for fiscal year-specific data (UMA, tax brackets)
    - Returns `TaxCalculation` entity with all calculation details

    **No external dependencies:** Pure application layer, no AI/database calls.
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
        taxpayer_info = TaxpayerInfo(name=request.taxpayer_name, fiscal_year=request.fiscal_year)

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

        return CalculateTaxResponse(calculation=calculation, taxpayer_info=taxpayer_info)
