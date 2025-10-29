import json
import os
import urllib.parse

from typing import Any, Dict, Optional

import google.oauth2.id_token
import google.auth.transport.requests as google_requests
import requests
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

from fiscal_recommendations import RecommendationFactory
from datetime import date
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def init_db():
    db_path = Path("recommendations.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendation_usage (
            user_id TEXT,
            date TEXT,
            count INTEGER,
            PRIMARY KEY (user_id, date)
        )
    """)

    conn.commit()
    conn.close()


init_db()

app = FastAPI()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "your-google-client-id")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "your-google-client-secret")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback"
)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

templates = Jinja2Templates(directory="templates")


class TaxCalculationResult(BaseModel):
    """
    Tax Calculation Result Model

    This model represents the complete results of tax calculations,
    including income, deductions, tax determinations, and final balance.
    """

    # === INCOME CALCULATIONS ===
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

    # === DEDUCTION CALCULATIONS ===
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

    # === TAX CALCULATIONS ===
    taxable_base: float = Field(
        description="Final tax base after all deductions", ge=0.0
    )
    determined_tax: float = Field(
        description="Tax determined based on taxable base", ge=0.0
    )
    withheld_tax: float = Field(description="Tax withheld during the year", ge=0.0)

    # === FINAL BALANCE ===
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

    def get_effective_tax_rate(self) -> float:
        """Calculate effective tax rate as percentage"""
        if self.total_taxable_income > 0:
            return (self.determined_tax / self.total_taxable_income) * 100
        return 0.0

    def get_deduction_efficiency(self) -> float:
        """Calculate deduction efficiency as percentage of gross income"""
        if self.gross_annual_income > 0:
            return (self.authorized_deductions / self.gross_annual_income) * 100
        return 0.0

    def is_refund_due(self) -> bool:
        """Check if taxpayer is due a refund"""
        return self.balance_in_favor > 0

    def get_net_tax_impact(self) -> float:
        """Get net tax impact (positive = owe, negative = refund)"""
        return self.balance_to_pay - self.balance_in_favor

    def get_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of tax calculation results"""
        return {
            "income_summary": {
                "gross_annual": self.gross_annual_income,
                "total_taxable": self.total_taxable_income,
                "effective_tax_rate": f"{self.get_effective_tax_rate():.2f}%",
            },
            "deduction_summary": {
                "total_deductions": self.authorized_deductions,
                "deduction_efficiency": f"{self.get_deduction_efficiency():.2f}%",
                "breakdown": {
                    "personal": self.personal_deductions,
                    "ppr": self.ppr_deductions,
                    "education": self.education_deductions,
                },
            },
            "tax_summary": {
                "taxable_base": self.taxable_base,
                "determined_tax": self.determined_tax,
                "withheld_tax": self.withheld_tax,
                "net_impact": self.get_net_tax_impact(),
                "refund_due": self.is_refund_due(),
            },
        }


class DataReader:
    def __init__(self, user_data_path: str):
        self.user_data_path = user_data_path

    def get_user_data(self) -> Dict[str, Any]:
        try:
            with open(self.user_data_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"User data file not found: {self.user_data_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Error decoding JSON file: {self.user_data_path}")

    def get_isr_table(self, fiscal_year: int) -> Dict[str, Any]:
        table_path = f"tabla_isr/isr_{fiscal_year}.json"
        try:
            with open(table_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"ISR table not found for fiscal year {fiscal_year}"
            )


class TaxCalculator:
    def __init__(self, user_data: Dict[str, Any], isr_table: Dict[str, Any]):
        self.user_data = user_data
        self.isr_table = isr_table

    def calculate_tax_balance(self) -> TaxCalculationResult:
        gross_annual_income = self.user_data["monthly_gross_income"] * 12

        daily_salary = self.user_data["monthly_gross_income"] / 30
        gross_bonus = daily_salary * self.user_data["bonus_days"]
        gross_vacation_premium = (
            daily_salary
            * self.user_data["vacation_days"]
            * self.user_data["vacation_premium_percentage"]
        )

        total_gross_income = gross_annual_income + gross_bonus + gross_vacation_premium

        taxable_bonus = self._calculate_taxable_bonus()
        taxable_vacation_premium = self._calculate_taxable_vacation_premium()

        total_taxable_income = (
            gross_annual_income + taxable_bonus + taxable_vacation_premium
        )

        total_exemptions = (gross_bonus - taxable_bonus) + (
            gross_vacation_premium - taxable_vacation_premium
        )
        taxable_income_without_deductions = total_gross_income - total_exemptions

        (
            authorized_deductions,
            personal_deductions,
            ppr_deductions,
            education_deductions,
        ) = self._calculate_authorized_deductions(total_gross_income)

        taxable_base = max(0, total_taxable_income - authorized_deductions)
        determined_tax = self._calculate_annual_tax(taxable_base)
        withheld_tax = self._estimate_withheld_tax(taxable_income_without_deductions)

        difference = withheld_tax - determined_tax
        balance_in_favor = max(0, difference)
        balance_to_pay = max(0, -difference)

        return TaxCalculationResult(
            gross_annual_income=total_gross_income,
            taxable_bonus=taxable_bonus,
            taxable_vacation_premium=taxable_vacation_premium,
            total_taxable_income=total_taxable_income,
            authorized_deductions=authorized_deductions,
            personal_deductions=personal_deductions,
            ppr_deductions=ppr_deductions,
            education_deductions=education_deductions,
            taxable_base=taxable_base,
            determined_tax=determined_tax,
            withheld_tax=withheld_tax,
            balance_in_favor=balance_in_favor,
            balance_to_pay=balance_to_pay,
        )

    def _calculate_annual_tax(self, taxable_base: float) -> float:
        monthly_base = taxable_base / 12
        monthly_tax = 0.0

        for bracket in self.isr_table["tabla_isr_mensual"]:
            if bracket["limite_inferior"] <= monthly_base <= bracket["limite_superior"]:
                surplus = monthly_base - bracket["limite_inferior"] + 0.01
                monthly_tax = bracket["cuota_fija"] + (
                    surplus * bracket["porcentaje_excedente"]
                )
                break

        return monthly_tax * 12

    def _calculate_taxable_bonus(self) -> float:
        # Use new TaxInputData structure
        monthly_income = self.user_data["monthly_gross_income"]
        bonus_days = self.user_data["bonus_days"]

        total_bonus = (monthly_income / 30) * bonus_days

        uma_daily = self.isr_table["constantes"]["valor_uma_diario"]
        exemption_umas = self.isr_table["constantes"]["exencion_aguinaldo_umas"]
        bonus_exemption = uma_daily * exemption_umas

        return max(0, total_bonus - bonus_exemption)

    def _calculate_taxable_vacation_premium(self) -> float:
        # Use new TaxInputData structure
        monthly_income = self.user_data["monthly_gross_income"]
        vacation_days = self.user_data["vacation_days"]
        premium_percentage = self.user_data["vacation_premium_percentage"]

        total_premium = (monthly_income / 30) * vacation_days * premium_percentage

        uma_daily = self.isr_table["constantes"]["valor_uma_diario"]
        exemption_umas = self.isr_table["constantes"]["exencion_prima_vacacional_umas"]
        premium_exemption = uma_daily * exemption_umas

        return max(0, total_premium - premium_exemption)

    def _estimate_withheld_tax(
        self,
        taxable_income_without_deductions: float,
    ) -> float:
        return self._calculate_annual_tax(taxable_income_without_deductions)

    def _calculate_authorized_deductions(
        self,
        total_gross_income: float,
    ) -> tuple[float, float, float, float]:
        # Use new TaxInputData structure with unified deduction fields
        total_general_deductions = self.user_data["general_deductions"]
        total_ppr = self.user_data["total_ppr"]
        total_tuition = self.user_data["total_tuition"]

        uma_annual = self.isr_table["constantes"]["valor_uma_anual"]

        # Apply caps to each deduction type
        general_cap = (
            uma_annual * self.isr_table["constantes"]["tope_general_deducciones_umas"]
        )
        limited_general_deductions = min(total_general_deductions, general_cap)

        ppr_cap = uma_annual * self.isr_table["constantes"]["tope_ppr_deducciones_umas"]
        limited_ppr = min(total_ppr, ppr_cap)

        # For education deductions, apply the maximum cap across all levels
        # Get the highest cap from education levels as a simplified approach
        education_caps = self.isr_table["topes_colegiaturas"]
        max_education_cap = max(education_caps.values()) if education_caps else 0
        limited_education_deductions = min(total_tuition, max_education_cap)

        cap_5_umas = uma_annual * 5
        cap_15_percent = total_gross_income * 0.15
        total_legal_cap = min(cap_5_umas, cap_15_percent)

        total_uncapped = (
            limited_general_deductions + limited_ppr + limited_education_deductions
        )
        total_capped = min(total_uncapped, total_legal_cap)

        if total_capped < total_uncapped:
            adjustment_factor = (
                total_capped / total_uncapped if total_uncapped > 0 else 0
            )
            limited_general_deductions *= adjustment_factor
            limited_ppr *= adjustment_factor
            limited_education_deductions *= adjustment_factor

        return (
            total_capped,
            limited_general_deductions,
            limited_ppr,
            limited_education_deductions,
        )


async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    user = request.session.get("user")
    if user:
        return user
    return None


@app.get("/")
async def read_root():
    """Redirect root path to calculator"""
    return RedirectResponse(url="/calculator", status_code=302)


@app.get("/calculator", response_class=HTMLResponse)
async def calculator(
    request: Request, user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    return templates.TemplateResponse(
        "calculator.html", {"request": request, "user": user}
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


class TaxInputData(BaseModel):
    taxpayer_name: str = Field(
        default="", description="Full name of the taxpayer", max_length=100
    )
    fiscal_year: int = Field(
        default=2025, description="Tax fiscal year", ge=2024, le=2025
    )

    monthly_gross_income: float = Field(
        default=0.0, description="Monthly gross income in USD", ge=0.0, le=1000000.0
    )
    monthly_net_income: float = Field(
        default=0.0, description="Monthly net income in USD", ge=0.0
    )
    bonus_days: int = Field(
        default=15, description="Number of bonus days (aguinaldo)", ge=0, le=365
    )
    vacation_days: int = Field(
        default=12, description="Number of annual vacation days", ge=0, le=365
    )
    vacation_premium_percentage: float = Field(
        default=0.25,
        description="Vacation premium percentage (0.25 = 25%)",
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

    def get_total_deductions(self) -> float:
        """Calculate total unified deductions"""
        return self.general_deductions + self.total_tuition + self.total_ppr

    def get_annual_gross_income(self) -> float:
        """Calculate estimated annual gross income"""
        return self.monthly_gross_income * 12

    def is_valid_fiscal_year(self) -> bool:
        """Validate fiscal year is supported"""
        return self.fiscal_year in [2024, 2025]

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the tax input data"""
        return {
            "taxpayer": self.taxpayer_name or "Anonymous",
            "fiscal_year": self.fiscal_year,
            "estimated_annual_income": self.get_annual_gross_income(),
            "total_deductions": self.get_total_deductions(),
            "deduction_breakdown": {
                "general": self.general_deductions,
                "tuition": self.total_tuition,
                "ppr": self.total_ppr,
            },
        }


@app.post("/api/calculate")
def calculate_tax_dynamic(tax_data: TaxInputData) -> Dict[str, Any]:
    # Convert input data to match TaxInputData interface structure
    user_data = {
        "taxpayer_name": tax_data.taxpayer_name,
        "fiscal_year": tax_data.fiscal_year,
        "monthly_gross_income": tax_data.monthly_gross_income,
        "monthly_net_income": tax_data.monthly_net_income,
        "bonus_days": tax_data.bonus_days,
        "vacation_days": tax_data.vacation_days,
        "vacation_premium_percentage": tax_data.vacation_premium_percentage,
        "general_deductions": tax_data.general_deductions,
        "total_tuition": tax_data.total_tuition,
        "total_ppr": tax_data.total_ppr,
    }

    # Load ISR table for the fiscal year
    data_reader = DataReader("")  # Empty path since we're only using get_isr_table
    isr_table = data_reader.get_isr_table(tax_data.fiscal_year)

    # Calculate taxes
    tax_calculator = TaxCalculator(user_data, isr_table)
    calculation_result = tax_calculator.calculate_tax_balance()

    # Return the results
    return {
        "taxpayer_name": tax_data.taxpayer_name,
        "fiscal_year": tax_data.fiscal_year,
        "gross_annual_income": calculation_result.gross_annual_income,
        "taxable_bonus": calculation_result.taxable_bonus,
        "taxable_vacation_premium": calculation_result.taxable_vacation_premium,
        "total_taxable_income": calculation_result.total_taxable_income,
        "authorized_deductions": calculation_result.authorized_deductions,
        "personal_deductions": calculation_result.personal_deductions,
        "ppr_deductions": calculation_result.ppr_deductions,
        "education_deductions": calculation_result.education_deductions,
        "taxable_base": calculation_result.taxable_base,
        "determined_tax": calculation_result.determined_tax,
        "withheld_tax": calculation_result.withheld_tax,
        "balance_in_favor": calculation_result.balance_in_favor,
        "balance_to_pay": calculation_result.balance_to_pay,
    }


# Helper functions for recommendation limits
def get_user_recommendation_usage(user_id: str) -> int:
    """Get today's recommendation usage count for a user"""
    today = date.today().isoformat()

    conn = sqlite3.connect("recommendations.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT count FROM recommendation_usage WHERE user_id = ? AND date = ?",
        (user_id, today),
    )

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else 0


def increment_user_recommendation_usage(user_id: str) -> int:
    """Increment today's recommendation usage count for a user"""
    today = date.today().isoformat()

    conn = sqlite3.connect("recommendations.db")
    cursor = conn.cursor()

    # Try to update existing record
    cursor.execute(
        "UPDATE recommendation_usage SET count = count + 1 WHERE user_id = ? AND date = ?",
        (user_id, today),
    )

    # If no existing record, insert new one
    if cursor.rowcount == 0:
        cursor.execute(
            "INSERT INTO recommendation_usage (user_id, date, count) VALUES (?, ?, 1)",
            (user_id, today),
        )

    # Get the updated count
    cursor.execute(
        "SELECT count FROM recommendation_usage WHERE user_id = ? AND date = ?",
        (user_id, today),
    )

    result = cursor.fetchone()
    count = result[0] if result else 1

    conn.commit()
    conn.close()

    return count


@app.get("/api/recommendations/usage")
async def get_recommendation_usage(
    user: Optional[Dict[str, Any]] = Depends(get_current_user),
):
    """Get current user's recommendation usage for today"""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    user_id = user.get("sub", user.get("email", "unknown"))
    used_today = get_user_recommendation_usage(user_id)
    daily_limit = 20

    return {
        "used_today": used_today,
        "daily_limit": daily_limit,
        "remaining": max(0, daily_limit - used_today),
    }


@app.post("/api/recommendations")
async def generate_recommendations(
    tax_data: TaxInputData, user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Generate fiscal recommendations with daily limit"""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    user_id = user.get("sub", user.get("email", "unknown"))
    used_today = get_user_recommendation_usage(user_id)
    daily_limit = 20

    if used_today >= daily_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Daily recommendation limit reached ({daily_limit}/day). Try again tomorrow!",
        )

    try:
        # Convert TaxInputData to the format expected by fiscal_recommendations
        user_data_for_recommendations = {
            "contribuyente": {
                "nombre_o_referencia": tax_data.taxpayer_name or "Usuario",
                "ejercicio_fiscal": tax_data.fiscal_year,
            },
            "ingresos": {
                "ingreso_bruto_mensual_ordinario": tax_data.monthly_gross_income,
                "dias_aguinaldo": tax_data.bonus_days,
                "dias_vacaciones_anuales": tax_data.vacation_days,
            },
        }

        # Calculate tax results to pass to recommendation system
        user_data_for_calculation = {
            "taxpayer_name": tax_data.taxpayer_name,
            "fiscal_year": tax_data.fiscal_year,
            "monthly_gross_income": tax_data.monthly_gross_income,
            "monthly_net_income": tax_data.monthly_net_income,
            "bonus_days": tax_data.bonus_days,
            "vacation_days": tax_data.vacation_days,
            "vacation_premium_percentage": tax_data.vacation_premium_percentage,
            "general_deductions": tax_data.general_deductions,
            "total_tuition": tax_data.total_tuition,
            "total_ppr": tax_data.total_ppr,
        }

        # Load ISR table and calculate taxes
        data_reader = DataReader("")
        isr_table = data_reader.get_isr_table(tax_data.fiscal_year)
        tax_calculator = TaxCalculator(user_data_for_calculation, isr_table)
        calculation_result = tax_calculator.calculate_tax_balance()

        # Generate recommendations using streaming (collect all chunks)
        recommendation_service = RecommendationFactory.create_service(use_ai=True)

        accumulated_text = ""
        for chunk in recommendation_service.get_recommendations_stream(
            calculation_result, user_data_for_recommendations, tax_data.fiscal_year
        ):
            accumulated_text += chunk

        # Process the response - now returning Markdown content
        if hasattr(recommendation_service.primary_generator, "_process_response"):
            recommendations_markdown = (
                recommendation_service.primary_generator._process_response(
                    accumulated_text
                )
            )
        else:
            # For fallback generator, return as is
            recommendations_markdown = accumulated_text

        new_count = increment_user_recommendation_usage(user_id)

        return {
            "recommendations_markdown": recommendations_markdown,
            "usage_info": {
                "used_today": new_count,
                "daily_limit": daily_limit,
                "remaining": max(0, daily_limit - new_count),
            },
        }

    except Exception as e:
        print(f"Error generating recommendations: {e}")
        # Fallback to simple recommendations if there's an error
        fallback_recommendations = [
            "<li><strong>Maximizar deducciones personales:</strong> Conserva todos los comprobantes fiscales de gastos médicos, dentales, y otros gastos deducibles para optimizar tu declaración.</li>",
            "<li><strong>Planificación fiscal:</strong> Considera abrir una cuenta PPR para obtener beneficios fiscales y ahorrar para tu retiro.</li>",
            "<li><strong>Revisión de retenciones:</strong> Evalúa con tu empleador si las retenciones mensuales están optimizadas para tu situación fiscal.</li>",
            "<li><strong>Documentación organizada:</strong> Mantén un archivo digital de todos tus comprobantes fiscales durante el año para facilitar tu declaración.</li>",
        ]

        new_count = increment_user_recommendation_usage(user_id)

        return {
            "recommendations": fallback_recommendations,
            "usage_info": {
                "used_today": new_count,
                "daily_limit": daily_limit,
                "remaining": max(0, daily_limit - new_count),
            },
        }


@app.post("/api/recommendations/stream")
async def generate_recommendations_stream(
    tax_data: TaxInputData, user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """Generate fiscal recommendations with streaming response"""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    user_id = user.get("sub", user.get("email", "unknown"))
    used_today = get_user_recommendation_usage(user_id)
    daily_limit = 20

    if used_today >= daily_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Daily recommendation limit reached ({daily_limit}/day). Try again tomorrow!",
        )

    async def generate_stream():
        try:
            # Convert TaxInputData to the format expected by fiscal_recommendations
            user_data_for_recommendations = {
                "contribuyente": {
                    "nombre_o_referencia": tax_data.taxpayer_name or "Usuario",
                    "ejercicio_fiscal": tax_data.fiscal_year,
                },
                "ingresos": {
                    "ingreso_bruto_mensual_ordinario": tax_data.monthly_gross_income,
                    "dias_aguinaldo": tax_data.bonus_days,
                    "dias_vacaciones_anuales": tax_data.vacation_days,
                },
            }

            # Calculate tax results
            user_data_for_calculation = {
                "taxpayer_name": tax_data.taxpayer_name,
                "fiscal_year": tax_data.fiscal_year,
                "monthly_gross_income": tax_data.monthly_gross_income,
                "monthly_net_income": tax_data.monthly_net_income,
                "bonus_days": tax_data.bonus_days,
                "vacation_days": tax_data.vacation_days,
                "vacation_premium_percentage": tax_data.vacation_premium_percentage,
                "general_deductions": tax_data.general_deductions,
                "total_tuition": tax_data.total_tuition,
                "total_ppr": tax_data.total_ppr,
            }

            data_reader = DataReader("")
            isr_table = data_reader.get_isr_table(tax_data.fiscal_year)
            tax_calculator = TaxCalculator(user_data_for_calculation, isr_table)
            calculation_result = tax_calculator.calculate_tax_balance()

            # Use streaming recommendations
            recommendation_service = RecommendationFactory.create_service(use_ai=True)

            print("🚀 Starting streaming recommendations...")
            yield 'data: {"type":"start"}\n\n'

            accumulated_text = ""
            for chunk in recommendation_service.get_recommendations_stream(
                calculation_result, user_data_for_recommendations, tax_data.fiscal_year
            ):
                accumulated_text += chunk
                yield f'data: {{"type":"chunk","content":"{chunk.replace('"', '\\"').replace("\n", "\\n")}"}}\n\n'

            # Process the complete response - now handling Markdown
            if hasattr(recommendation_service.primary_generator, "_process_response"):
                processed_markdown = (
                    recommendation_service.primary_generator._process_response(
                        accumulated_text
                    )
                )
                yield f'data: {{"type":"complete","markdown":"{processed_markdown.replace('"', '\\"').replace(chr(10), "\\n").replace(chr(13), "\\r")}"}}\n\n'
            else:
                # For fallback generator, return markdown as is
                fallback_markdown = (
                    accumulated_text
                    if accumulated_text
                    else "**Error:** No se pudieron generar recomendaciones."
                )
                yield f'data: {{"type":"complete","markdown":"{fallback_markdown.replace('"', '\\"').replace(chr(10), "\\n").replace(chr(13), "\\r")}"}}\n\n'

            # Increment usage counter
            increment_user_recommendation_usage(user_id)

        except Exception as e:
            print(f"Error in streaming: {e}")
            error_markdown = "**Error temporal:** Ocurrió un problema generando las recomendaciones. Por favor, intenta nuevamente."
            yield f'data: {{"type":"error","markdown":"{error_markdown}"}}\n\n'

    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        },
    )


@app.get("/auth/google")
async def google_auth():
    """Redirect to Google OAuth"""
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={urllib.parse.quote(GOOGLE_REDIRECT_URI or '')}&"
        f"scope=openid%20email%20profile&"
        f"response_type=code&"
        f"access_type=offline"
    )
    return RedirectResponse(url=google_auth_url)


@app.get("/auth/callback")
async def google_callback(request: Request, code: str):
    """Google OAuth callback"""
    try:
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": GOOGLE_REDIRECT_URI,
        }

        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        id_token = token_json["id_token"]

        user_info = google.oauth2.id_token.verify_oauth2_token(
            id_token, google_requests.Request(), GOOGLE_CLIENT_ID
        )

        # Store user info in session
        request.session["user"] = {
            "sub": user_info["sub"],
            "email": user_info["email"],
            "name": user_info.get("name", user_info["email"]),
        }

        return RedirectResponse(url="/calculator", status_code=302)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")


@app.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/calculator")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
