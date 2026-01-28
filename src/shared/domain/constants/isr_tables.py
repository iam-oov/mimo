from dataclasses import dataclass


@dataclass
class TaxBracket:
    """Represents a tax bracket in the monthly ISR table"""

    lower_limit: float
    upper_limit: float
    fixed_fee: float
    excess_percentage: float


@dataclass
class ISRConstants:
    """Fiscal constants for a specific fiscal year"""

    daily_uma_value: float
    annual_uma_value: float
    bonus_exemption_umas: int
    vacation_premium_exemption_umas: int
    glasses_limit_mxn: float
    general_deduction_cap_umas: float
    ppr_deduction_cap_umas: float


@dataclass
class TuitionLimits:
    """Deductibility limits for tuition by education level"""

    preschool: float
    elementary: float
    middle_school: float
    technical_professional: float
    high_school: float


@dataclass
class ISRTable:
    """Complete ISR table for a fiscal year"""

    fiscal_year: int
    constants: ISRConstants
    tuition_limits: TuitionLimits
    monthly_isr_table: list[TaxBracket]


# =====================================================
# FISCAL YEAR 2024
# =====================================================

ISR_CONSTANTS_2024 = ISRConstants(
    daily_uma_value=108.57,
    annual_uma_value=39606.36,
    bonus_exemption_umas=30,
    vacation_premium_exemption_umas=15,
    glasses_limit_mxn=2500.0,
    general_deduction_cap_umas=5.0,
    ppr_deduction_cap_umas=5.0,
)

TUITION_LIMITS_2024 = TuitionLimits(
    preschool=14200.0,
    elementary=12900.0,
    middle_school=19900.0,
    technical_professional=17100.0,
    high_school=24500.0,
)

MONTHLY_ISR_TABLE_2024 = [
    TaxBracket(0.01, 746.04, 0.0, 0.0192),
    TaxBracket(746.05, 6332.05, 14.32, 0.064),
    TaxBracket(6332.06, 11128.0, 371.83, 0.1088),
    TaxBracket(11128.01, 12935.81, 893.64, 0.16),
    TaxBracket(12935.82, 15487.71, 1182.89, 0.1792),
    TaxBracket(15487.72, 31236.49, 1640.18, 0.2136),
    TaxBracket(31236.50, 49233.01, 4998.95, 0.2352),
    TaxBracket(49233.02, 93993.9, 9235.19, 0.28),
    TaxBracket(93993.91, 125325.2, 21768.14, 0.32),
    TaxBracket(125325.21, 375975.6, 31794.26, 0.34),
    TaxBracket(375975.61, float("inf"), 117020.5, 0.35),
]

ISR_TABLE_2024 = ISRTable(
    fiscal_year=2024,
    constants=ISR_CONSTANTS_2024,
    tuition_limits=TUITION_LIMITS_2024,
    monthly_isr_table=MONTHLY_ISR_TABLE_2024,
)

# =====================================================
# FISCAL YEAR 2025
# =====================================================

ISR_CONSTANTS_2025 = ISRConstants(
    daily_uma_value=108.57,
    annual_uma_value=39606.36,
    bonus_exemption_umas=30,
    vacation_premium_exemption_umas=15,
    glasses_limit_mxn=2500.0,
    general_deduction_cap_umas=5.0,
    ppr_deduction_cap_umas=5.0,
)

TUITION_LIMITS_2025 = TuitionLimits(
    preschool=14200.0,
    elementary=12900.0,
    middle_school=19900.0,
    technical_professional=17100.0,
    high_school=24500.0,
)

MONTHLY_ISR_TABLE_2025 = [
    TaxBracket(0.01, 746.04, 0.0, 0.0192),
    TaxBracket(746.05, 6332.05, 14.32, 0.064),
    TaxBracket(6332.06, 11128.01, 371.83, 0.1088),
    TaxBracket(11128.02, 12935.82, 893.63, 0.16),
    TaxBracket(12935.83, 15487.71, 1182.88, 0.1792),
    TaxBracket(15487.72, 31236.49, 1640.18, 0.2136),
    TaxBracket(31236.50, 49233.01, 4998.95, 0.2352),
    TaxBracket(49233.02, 93993.9, 9235.19, 0.28),
    TaxBracket(93993.91, 125325.2, 21768.14, 0.32),
    TaxBracket(125325.21, 375975.6, 31794.26, 0.34),
    TaxBracket(375975.61, float("inf"), 117020.5, 0.35),
]

ISR_TABLE_2025 = ISRTable(
    fiscal_year=2025,
    constants=ISR_CONSTANTS_2025,
    tuition_limits=TUITION_LIMITS_2025,
    monthly_isr_table=MONTHLY_ISR_TABLE_2025,
)

# =====================================================
# FISCAL YEAR 2026
# =====================================================
ISR_CONSTANTS_2026 = ISRConstants(
    daily_uma_value=117.31,
    annual_uma_value=42714.15,
    bonus_exemption_umas=30,
    vacation_premium_exemption_umas=15,
    glasses_limit_mxn=2500.0,
    general_deduction_cap_umas=5.0,
    ppr_deduction_cap_umas=5.0,
)

TUITION_LIMITS_2026 = TuitionLimits(
    preschool=14200.0,
    elementary=12900.0,
    middle_school=19900.0,
    technical_professional=17100.0,
    high_school=24500.0,
)

MONTHLY_ISR_TABLE_2026 = [
    TaxBracket(0.01, 844.59, 0.0, 0.0192),
    TaxBracket(844.60, 7168.51, 16.22, 0.064),
    TaxBracket(7168.52, 12598.02, 420.95, 0.1088),
    TaxBracket(12598.03, 14644.64, 1011.68, 0.16),
    TaxBracket(14644.65, 17533.64, 1339.14, 0.1792),
    TaxBracket(17533.65, 35362.83, 1856.84, 0.2136),
    TaxBracket(35362.84, 55736.68, 5665.16, 0.2352),
    TaxBracket(55736.69, float("inf"), 10457.09, 0.35),
]

ISR_TABLE_2026 = ISRTable(
    fiscal_year=2026,
    constants=ISR_CONSTANTS_2026,
    tuition_limits=TUITION_LIMITS_2026,
    monthly_isr_table=MONTHLY_ISR_TABLE_2026,
)

# =====================================================
# DICTIONARY FOR ACCESS BY YEAR
# =====================================================

ISR_TABLES: dict[int, ISRTable] = {
    2024: ISR_TABLE_2024,
    2025: ISR_TABLE_2025,
    2026: ISR_TABLE_2026,
}


def get_isr_table(fiscal_year: int) -> ISRTable:
    """
    Get ISR table for the specified fiscal year.

    Args:
        fiscal_year: Year of the fiscal year

    Returns:
        ISRTable corresponding to the fiscal year

    Raises:
        KeyError: If table does not exist for the requested fiscal year
    """
    if fiscal_year not in ISR_TABLES:
        available_fiscal_year = max(ISR_TABLES.keys())
        return ISR_TABLES[available_fiscal_year]
    return ISR_TABLES[fiscal_year]
