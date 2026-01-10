import pytest

from src.tax_calculation.domain.services.tax_calculation_service import (
    TaxCalculationService,
)
from src.tax_calculation.domain.value_objects.tax_data import (
    DeductionData,
    IncomeData,
)
from src.shared.domain.constants.isr_tables import (
    ISR_TABLE_2024,
    ISR_TABLE_2025,
    ISR_TABLE_2026,
    ISRTable,
    get_isr_table,
)


# =============================================================================
# ISR TABLE FIXTURES
# =============================================================================


@pytest.fixture
def isr_table_2024() -> ISRTable:
    """ISR table for fiscal year 2024"""
    return ISR_TABLE_2024


@pytest.fixture
def isr_table_2025() -> ISRTable:
    """ISR table for fiscal year 2025"""
    return ISR_TABLE_2025


@pytest.fixture
def isr_table_2026() -> ISRTable:
    """ISR table for fiscal year 2026"""
    return ISR_TABLE_2026


@pytest.fixture(params=[2024, 2025, 2026])
def isr_table_all_years(request) -> ISRTable:
    """Parametrized fixture for all fiscal years"""
    return get_isr_table(request.param)


# =============================================================================
# TAX CALCULATION SERVICE FIXTURES
# =============================================================================


@pytest.fixture
def tax_service_2024(isr_table_2024: ISRTable) -> TaxCalculationService:
    """Tax calculation service for 2024"""
    return TaxCalculationService(isr_table_2024)


@pytest.fixture
def tax_service_2025(isr_table_2025: ISRTable) -> TaxCalculationService:
    """Tax calculation service for 2025"""
    return TaxCalculationService(isr_table_2025)


@pytest.fixture
def tax_service_2026(isr_table_2026: ISRTable) -> TaxCalculationService:
    """Tax calculation service for 2026"""
    return TaxCalculationService(isr_table_2026)


# =============================================================================
# INCOME DATA FIXTURES
# =============================================================================


@pytest.fixture
def income_low() -> IncomeData:
    """Low income: ~$10,000/month"""
    return IncomeData(
        monthly_gross_income=10000.0,
        bonus_days=15,
        vacation_days=6,
        vacation_premium_percentage=0.25,
    )


@pytest.fixture
def income_medium() -> IncomeData:
    """Medium income: ~$25,000/month"""
    return IncomeData(
        monthly_gross_income=25000.0,
        bonus_days=15,
        vacation_days=12,
        vacation_premium_percentage=0.25,
    )


@pytest.fixture
def income_high() -> IncomeData:
    """High income: ~$80,000/month"""
    return IncomeData(
        monthly_gross_income=80000.0,
        bonus_days=30,
        vacation_days=20,
        vacation_premium_percentage=0.25,
    )


@pytest.fixture
def income_very_high() -> IncomeData:
    """Very high income: ~$150,000/month (top bracket)"""
    return IncomeData(
        monthly_gross_income=150000.0,
        bonus_days=30,
        vacation_days=20,
        vacation_premium_percentage=0.25,
    )


@pytest.fixture
def income_zero() -> IncomeData:
    """Zero income edge case"""
    return IncomeData(
        monthly_gross_income=0.0,
        bonus_days=0,
        vacation_days=0,
        vacation_premium_percentage=0.0,
    )


@pytest.fixture
def income_minimum_wage() -> IncomeData:
    """Minimum wage: ~$7,500/month (2024)"""
    return IncomeData(
        monthly_gross_income=7500.0,
        bonus_days=15,
        vacation_days=12,
        vacation_premium_percentage=0.25,
    )


# =============================================================================
# DEDUCTION DATA FIXTURES
# =============================================================================


@pytest.fixture
def deductions_none() -> DeductionData:
    """No deductions"""
    return DeductionData(
        general_deductions=0.0,
        ppr_deductions=0.0,
        education_deductions=0.0,
    )


@pytest.fixture
def deductions_small() -> DeductionData:
    """Small deductions: within all caps"""
    return DeductionData(
        general_deductions=15000.0,
        ppr_deductions=10000.0,
        education_deductions=5000.0,
    )


@pytest.fixture
def deductions_medium() -> DeductionData:
    """Medium deductions: approaching caps"""
    return DeductionData(
        general_deductions=50000.0,
        ppr_deductions=30000.0,
        education_deductions=15000.0,
    )


@pytest.fixture
def deductions_maxed() -> DeductionData:
    """Maxed deductions: exceeding all individual caps"""
    return DeductionData(
        general_deductions=250000.0,
        ppr_deductions=250000.0,
        education_deductions=50000.0,
    )


@pytest.fixture
def deductions_education_only() -> DeductionData:
    """Education deductions only"""
    return DeductionData(
        general_deductions=0.0,
        ppr_deductions=0.0,
        education_deductions=20000.0,
    )


@pytest.fixture
def deductions_ppr_only() -> DeductionData:
    """PPR (retirement) deductions only"""
    return DeductionData(
        general_deductions=0.0,
        ppr_deductions=100000.0,
        education_deductions=0.0,
    )
