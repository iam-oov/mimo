from typing import Any

from pydantic import BaseModel, Field

from src.api.v1.schemas.tax_schemas import TaxCalculationRequest


class RecommendationRequest(TaxCalculationRequest):
    """
    API schema for recommendations request.
    Inherits all fields from TaxCalculationRequest to accept form data directly.
    """

    # Optional fields for backward compatibility with old API format
    calculation_result: dict[str, Any] | None = None
    user_data: dict[str, Any] | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "calculation_result": {
                    "gross_annual_income": 158760.00,
                    "taxable_bonus": 3150.00,
                    "taxable_vacation_premium": 787.50,
                    "total_taxable_income": 162697.50,
                    "authorized_deductions": 71000.00,
                    "personal_deductions": 58000.00,
                    "ppr_deductions": 8000.00,
                    "education_deductions": 5000.00,
                    "taxable_base": 91697.50,
                    "determined_tax": 14250.25,
                    "withheld_tax": 17500.00,
                    "balance_in_favor": 3249.75,
                    "balance_to_pay": 0.00,
                },
                "user_data": {
                    "contribuyente": {"nombre_o_referencia": "Juan Pérez"},
                    "ingresos": {
                        "ingreso_bruto_mensual_ordinario": 12600.00,
                        "dias_aguinaldo": 15,
                        "dias_vacaciones_anuales": 12,
                    },
                },
                "fiscal_year": 2025,
            }
        }
    }


class UsageInfoResponse(BaseModel):
    """API schema for usage information response"""

    usage_count: int = Field(description="Number of recommendations generated today")
    remaining_usage: int = Field(description="Remaining recommendations available today")
    daily_limit: int = Field(description="Daily limit for recommendations")

    model_config = {
        "json_schema_extra": {"example": {"usage_count": 1, "remaining_usage": 2, "daily_limit": 3}}
    }
