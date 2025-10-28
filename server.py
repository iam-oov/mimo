#!/usr/bin/env python3
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import google.oauth2.id_token
import google.auth.transport.requests as google_requests
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from fiscal_recommendations import RecommendationFactory
from datetime import date
import sqlite3
from pathlib import Path
# from main import calculate_tax, TaxData, TaxCalculationResult  # Using local definitions instead

# Load environment variables
from dotenv import load_dotenv

load_dotenv()


# Initialize SQLite database for tracking recommendation usage
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


# Initialize database on startup
init_db()

app = FastAPI()

# OAuth2 settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "your-google-client-id")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "your-google-client-secret")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback"
)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

templates = Jinja2Templates(directory="templates")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")


@dataclass
class TaxCalculationResult:
    gross_annual_income: float
    taxable_bonus: float
    taxable_vacation_premium: float
    total_taxable_income: float
    authorized_deductions: float
    personal_deductions: float
    ppr_deductions: float
    education_deductions: float
    taxable_base: float
    determined_tax: float
    withheld_tax: float
    balance_in_favor: float
    balance_to_pay: float


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
        incomes = self.user_data["ingresos"]
        gross_annual_income = incomes["ingreso_bruto_mensual_ordinario"] * 12

        daily_salary = incomes["ingreso_bruto_mensual_ordinario"] / 30
        gross_bonus = daily_salary * incomes["dias_aguinaldo"]
        gross_vacation_premium = (
            daily_salary
            * incomes["dias_vacaciones_anuales"]
            * incomes["porcentaje_prima_vacacional"]
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
        incomes = self.user_data["ingresos"]
        monthly_income = incomes["ingreso_bruto_mensual_ordinario"]
        bonus_days = incomes["dias_aguinaldo"]

        total_bonus = (monthly_income / 30) * bonus_days

        uma_daily = self.isr_table["constantes"]["valor_uma_diario"]
        exemption_umas = self.isr_table["constantes"]["exencion_aguinaldo_umas"]
        bonus_exemption = uma_daily * exemption_umas

        return max(0, total_bonus - bonus_exemption)

    def _calculate_taxable_vacation_premium(self) -> float:
        incomes = self.user_data["ingresos"]
        monthly_income = incomes["ingreso_bruto_mensual_ordinario"]
        vacation_days = incomes["dias_vacaciones_anuales"]
        premium_percentage = incomes["porcentaje_prima_vacacional"]

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
        deductions = self.user_data["deducciones_personales"]
        total_deductions = sum(deductions["general"].values())

        uma_annual = self.isr_table["constantes"]["valor_uma_anual"]
        general_cap = (
            uma_annual * self.isr_table["constantes"]["tope_general_deducciones_umas"]
        )
        limited_general_deductions = min(total_deductions, general_cap)

        ppr = deductions["ppr"]["aportaciones_ppr_art_151_frac_v"]
        ppr_cap = uma_annual * self.isr_table["constantes"]["tope_ppr_deducciones_umas"]
        limited_ppr = min(ppr, ppr_cap)

        total_education_deductions = 0.0
        education_caps = self.isr_table["topes_colegiaturas"]

        for tuition in deductions["colegiaturas"]:
            level = tuition["nivel_educativo"]
            amount = tuition["monto_pagado"]
            cap = education_caps.get(level, 0)
            total_education_deductions += min(amount, cap)

        cap_5_umas = uma_annual * 5
        cap_15_percent = total_gross_income * 0.15
        total_legal_cap = min(cap_5_umas, cap_15_percent)

        total_uncapped = (
            limited_general_deductions + limited_ppr + total_education_deductions
        )
        total_capped = min(total_uncapped, total_legal_cap)

        if total_capped < total_uncapped:
            adjustment_factor = (
                total_capped / total_uncapped if total_uncapped > 0 else 0
            )
            limited_general_deductions *= adjustment_factor
            limited_ppr *= adjustment_factor
            total_education_deductions *= adjustment_factor

        return (
            total_capped,
            limited_general_deductions,
            limited_ppr,
            total_education_deductions,
        )


async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    user = request.session.get("user")
    if user:
        return user
    return None


@app.get("/", response_class=HTMLResponse)
async def read_root(
    request: Request, user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@app.get("/calculator", response_class=HTMLResponse)
async def calculator(
    request: Request, user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    return templates.TemplateResponse(
        "calculator.html", {"request": request, "user": user}
    )


class TaxInputData(BaseModel):
    # Taxpayer data
    taxpayer_name: str = "Taxpayer"
    fiscal_year: int = 2024

    # Income
    monthly_gross_income: float
    monthly_net_income: float = 0
    bonus_days: int = 15
    vacation_days: int = 12
    vacation_premium_percentage: float = 0.25

    # Personal deductions - General
    medical_dental_expenses: float = 0
    funeral_expenses: float = 0
    donations: float = 0
    mortgage_interest: float = 0
    voluntary_retirement_contributions: float = 0
    medical_insurance_premiums: float = 0
    school_transportation_expenses: float = 0
    special_savings_account_deposits: float = 0
    educational_services_payments: float = 0

    # PPR deductions
    ppr_contributions: float = 0

    # Tuition (simplified list)
    preschool_tuition: float = 0
    elementary_tuition: float = 0
    middle_school_tuition: float = 0
    technical_school_tuition: float = 0
    high_school_tuition: float = 0


@app.post("/api/calculate")
def calculate_tax_dynamic(tax_data: TaxInputData):
    # Convert input data to the format expected by the calculator
    user_data = {
        "contribuyente": {
            "nombre_o_referencia": tax_data.taxpayer_name,
            "ejercicio_fiscal": tax_data.fiscal_year,
        },
        "ingresos": {
            "ingreso_bruto_mensual_ordinario": tax_data.monthly_gross_income,
            "ingreso_neto_mensual_ordinario": tax_data.monthly_net_income,
            "dias_aguinaldo": tax_data.bonus_days,
            "dias_vacaciones_anuales": tax_data.vacation_days,
            "porcentaje_prima_vacacional": tax_data.vacation_premium_percentage,
        },
        "deducciones_personales": {
            "general": {
                "gastos_medicos_dentales": tax_data.medical_dental_expenses,
                "gastos_funerarios": tax_data.funeral_expenses,
                "donativos": tax_data.donations,
                "intereses_reales_creditos_hipotecarios": tax_data.mortgage_interest,
                "aportaciones_voluntarias_subcuenta_retiro": tax_data.voluntary_retirement_contributions,
                "primas_seguros_gastos_medicos": tax_data.medical_insurance_premiums,
                "gastos_transportacion_escolar": tax_data.school_transportation_expenses,
                "depositos_cuentas_especiales_ahorro": tax_data.special_savings_account_deposits,
                "pagos_servicios_educativos": tax_data.educational_services_payments,
            },
            "ppr": {"aportaciones_ppr_art_151_frac_v": tax_data.ppr_contributions},
            "colegiaturas": [
                {
                    "nivel_educativo": "preescolar",
                    "monto_pagado": tax_data.preschool_tuition,
                },
                {
                    "nivel_educativo": "primaria",
                    "monto_pagado": tax_data.elementary_tuition,
                },
                {
                    "nivel_educativo": "secundaria",
                    "monto_pagado": tax_data.middle_school_tuition,
                },
                {
                    "nivel_educativo": "profesional_tecnico",
                    "monto_pagado": tax_data.technical_school_tuition,
                },
                {
                    "nivel_educativo": "preparatoria",
                    "monto_pagado": tax_data.high_school_tuition,
                },
            ],
        },
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
    daily_limit = 2

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
    daily_limit = 2

    if used_today >= daily_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Daily recommendation limit reached ({daily_limit}/day). Try again tomorrow!",
        )

    # For now, return fallback recommendations
    # In a complete implementation, you would use the Gemini API
    fallback_recommendations = [
        "Consider maximizing your personal deductions to reduce taxable income.",
        "Review your withholding tax to avoid large payments at year-end.",
        "Keep detailed records of all deductible expenses throughout the year.",
        "Consider contributing to a retirement plan for additional tax benefits.",
    ]

    # Increment usage count
    new_count = increment_user_recommendation_usage(user_id)

    return {
        "recommendations": fallback_recommendations,
        "usage_info": {
            "used_today": new_count,
            "daily_limit": daily_limit,
            "remaining": max(0, daily_limit - new_count),
        },
    }


@app.get("/api/calculate")
def calculate_tax():
    data_reader = DataReader("data/sim1.json")
    user_data = data_reader.get_user_data()
    fiscal_year = user_data["contribuyente"]["ejercicio_fiscal"]
    isr_table = data_reader.get_isr_table(fiscal_year)

    tax_calculator = TaxCalculator(user_data, isr_table)
    result = tax_calculator.calculate_tax_balance()
    return result


@app.get("/api/recommendations")
async def get_recommendations(
    user: Dict[str, Any] = Depends(get_current_user),
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Rate limiting logic
    now = datetime.now()
    user_recommendations = user.get("recommendations", [])
    recent_recommendations = [
        r for r in user_recommendations if now - r["timestamp"] < timedelta(days=5)
    ]

    if len(recent_recommendations) >= 3:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    data_reader = DataReader("data/sim1.json")
    user_data = data_reader.get_user_data()
    fiscal_year = user_data["contribuyente"]["ejercicio_fiscal"]
    isr_table = data_reader.get_isr_table(fiscal_year)

    tax_calculator = TaxCalculator(user_data, isr_table)
    calculation_result = tax_calculator.calculate_tax_balance()

    recommendation_service = RecommendationFactory.create_service()
    recommendations = await recommendation_service.get_recommendations(
        calculation_result, user_data, fiscal_year
    )

    # Store recommendation request
    user_recommendations.append({"timestamp": now})
    user["recommendations"] = user_recommendations

    return {"recommendations": recommendations}


@app.get("/auth/google")
async def login_google():
    return RedirectResponse(
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"response_type=code&client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&scope=openid%20email%20profile"
    )


@app.get("/auth/google/callback")
async def auth_google_callback(request: Request, code: str):
    try:
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        id_token = token_json["id_token"]

        user_info = google.oauth2.id_token.verify_oauth2_token(
            id_token, google_requests.Request(), GOOGLE_CLIENT_ID
        )

        request.session["user"] = {
            "email": user_info["email"],
            "name": user_info["name"],
            "recommendations": [],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to authenticate with Google: {e}"
        )

    return RedirectResponse(url="/")


@app.get("/auth/google")
async def google_auth():
    """Redirect to Google OAuth"""
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={urllib.parse.quote(GOOGLE_REDIRECT_URI)}&"
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
    return RedirectResponse(url="/")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
