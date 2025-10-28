#!/usr/bin/env python3
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

from jinja2 import Template
from fiscal_recommendations import RecommendationFactory
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env
load_dotenv()


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
        # The company does not know the employee's personal deductions when calculating withholdings.
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

        # Art. 151 LISR: Total personal deductions cannot exceed the lesser of 5 annual UMAs or 15% of total gross income.
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


class ReportGenerator:
    def __init__(self, messages: Dict[str, Any], template_path: str):
        self.messages = messages
        self.template_path = template_path
        self.template_html = self._load_template()
        self.recommendation_service = RecommendationFactory.create_service()

    def _load_template(self) -> str:
        with open(self.template_path, "r", encoding="utf-8") as f:
            return f.read()

    def generate_report(
        self,
        calculation: TaxCalculationResult,
        user_data: Dict[str, Any],
        fiscal_year: int,
        output_path: str = "tax_balance_report",
        output_format: str = "html",
    ):
        # Generar recomendaciones fiscales personalizadas
        fiscal_recommendations = self.recommendation_service.get_recommendations(
            calculation, user_data, fiscal_year
        )

        template_data = {
            "messages": self.messages,
            "fiscal_year": fiscal_year,
            "taxpayer_name": user_data["contribuyente"]["nombre_o_referencia"],
            "user_data": user_data,
            "calculation": calculation,
            "fiscal_recommendations": fiscal_recommendations,
            "generation_date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        }

        template = Template(self.template_html)
        html_content = template.render(**template_data)

        if output_format.lower() == "pdf":
            try:
                import weasyprint

                pdf_path = f"{output_path}.pdf"
                weasyprint.HTML(string=html_content).write_pdf(pdf_path)
                print(f"✅ PDF report generated successfully: {pdf_path}")
                return pdf_path
            except ImportError:
                print(self.messages["weasyprint_not_available"])
                output_format = "html"
            except Exception as e:
                print(self.messages["pdf_generation_error"].format(error=e))
                print(self.messages["generating_html_as_fallback"])
                output_format = "html"

        if output_format.lower() == "html":
            html_path = f"{output_path}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(self.messages["html_report_generated"].format(file_path=html_path))
            print(self.messages["open_in_browser_or_convert_to_pdf"])
            return html_path


def main():
    try:
        with open("messages.json", "r", encoding="utf-8") as f:
            messages = json.load(f)

        data_reader = DataReader("data/sim1.json")
        user_data = data_reader.get_user_data()
        fiscal_year = user_data["contribuyente"]["ejercicio_fiscal"]
        isr_table = data_reader.get_isr_table(fiscal_year)

        tax_calculator = TaxCalculator(user_data, isr_table)

        print(messages["calculating_balance"])
        result = tax_calculator.calculate_tax_balance()

        print("\n" + "=" * 60)
        print(f"📊 {messages['calculation_results']}")
        print("=" * 60)
        print(
            f"{messages['taxpayer']}: {user_data['contribuyente']['nombre_o_referencia']}"
        )
        print(f"{messages['fiscal_year']}: {fiscal_year}")
        print("-" * 60)
        print(
            f"{messages['gross_annual_income']:<25} ${result.gross_annual_income:,.2f}"
        )

        if "ingreso_neto_mensual_ordinario" in user_data["ingresos"]:
            net_annual_income = (
                user_data["ingresos"]["ingreso_neto_mensual_ordinario"] * 12
            )
            print(f"{messages['net_annual_income']:<25} ${net_annual_income:,.2f}")

        print(f"{messages['taxable_bonus']:<25} ${result.taxable_bonus:,.2f}")
        print(
            f"{messages['taxable_vacation_premium']:<25} ${result.taxable_vacation_premium:,.2f}"
        )
        print(
            f"{messages['total_taxable_income']:<25} ${result.total_taxable_income:,.2f}"
        )
        print(
            f"{messages['authorized_deductions']:<25} ${result.authorized_deductions:,.2f}"
        )
        print(f"{messages['taxable_base']:<25} ${result.taxable_base:,.2f}")
        print(f"{messages['determined_tax']:<25} ${result.determined_tax:,.2f}")
        print(f"{messages['withheld_tax']:<25} ${result.withheld_tax:,.2f}")
        print("-" * 60)

        if result.balance_in_favor > 0:
            print(f"{messages['balance_in_favor']:<25} ${result.balance_in_favor:,.2f}")
        elif result.balance_to_pay > 0:
            print(f"{messages['balance_to_pay']:<25} ${result.balance_to_pay:,.2f}")
        else:
            print(f"{messages['no_balance']}")

        print("=" * 60)

        print(f"\n{messages['generating_report']}")
        report_generator = ReportGenerator(messages, "report_template.html")
        report_generator.generate_report(
            result, user_data, fiscal_year, "tax_balance_report", "html"
        )

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
