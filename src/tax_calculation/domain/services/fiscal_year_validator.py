"""
Fiscal year validator that dynamically validates against available ISR tables.
Follows Open/Closed Principle - no hardcoded year ranges.
"""

from src.shared.domain.constants.isr_tables import ISR_TABLES


class FiscalYearValidator:
    """
    Validates fiscal year against available ISR tables.
    Automatically updates when new fiscal years are added to ISR_TABLES.
    """

    @staticmethod
    def get_available_years() -> list[int]:
        """Get all available fiscal years from ISR tables"""
        return sorted(ISR_TABLES.keys())

    @staticmethod
    def get_min_year() -> int:
        """Get minimum available fiscal year"""
        return min(ISR_TABLES.keys())

    @staticmethod
    def get_max_year() -> int:
        """Get maximum available fiscal year"""
        return max(ISR_TABLES.keys())

    @staticmethod
    def validate_fiscal_year(fiscal_year: int) -> None:
        """
        Validate that fiscal year is available in ISR tables.

        Args:
            fiscal_year: The year to validate

        Raises:
            ValueError: If fiscal year is not in available ISR tables
        """
        if fiscal_year not in ISR_TABLES:
            available_years = FiscalYearValidator.get_available_years()
            raise ValueError(
                f"Fiscal year {fiscal_year} is not available. "
                f"Supported years: {available_years}"
            )
