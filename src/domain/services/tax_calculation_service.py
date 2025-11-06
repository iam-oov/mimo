from typing import Tuple
from src.domain.entities.tax_calculation import TaxCalculation
from src.domain.value_objects.tax_data import IncomeData, DeductionData
from tabla_isr_constants import TablaISR


class TaxCalculationService:
    """
    Domain service containing tax calculation business logic.
    Pure business rules with no infrastructure dependencies.
    """

    def __init__(self, isr_table: TablaISR):
        self._isr_table = isr_table

    def calculate_tax(
        self, income_data: IncomeData, deduction_data: DeductionData
    ) -> TaxCalculation:
        """
        Main method to calculate tax balance.
        Orchestrates all calculation steps following Mexican ISR rules.
        """
        gross_annual_income = income_data.annual_gross_income
        gross_bonus = income_data.gross_bonus
        gross_vacation_premium = income_data.gross_vacation_premium

        total_gross_income = gross_annual_income + gross_bonus + gross_vacation_premium

        taxable_bonus = self._calculate_taxable_bonus(income_data)
        taxable_vacation_premium = self._calculate_taxable_vacation_premium(income_data)

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
        ) = self._calculate_authorized_deductions(deduction_data, total_gross_income)

        taxable_base = max(0, total_taxable_income - authorized_deductions)
        determined_tax = self._calculate_annual_tax(taxable_base)
        withheld_tax = self._estimate_withheld_tax(taxable_income_without_deductions)

        difference = withheld_tax - determined_tax
        balance_in_favor = max(0, difference)
        balance_to_pay = max(0, -difference)

        return TaxCalculation(
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
        """Calculate annual tax using monthly ISR brackets"""
        monthly_base = taxable_base / 12
        monthly_tax = 0.0

        for bracket in self._isr_table.tabla_isr_mensual:
            if bracket.limite_inferior <= monthly_base <= bracket.limite_superior:
                surplus = monthly_base - bracket.limite_inferior + 0.01
                monthly_tax = bracket.cuota_fija + (
                    surplus * bracket.porcentaje_excedente
                )
                break

        return monthly_tax * 12

    def _calculate_taxable_bonus(self, income_data: IncomeData) -> float:
        """
        Calculate taxable portion of bonus (aguinaldo) after UMA-based exemption.
        Exemption: 30 UMAs daily
        """
        total_bonus = income_data.gross_bonus

        uma_daily = self._isr_table.constantes.valor_uma_diario
        exemption_umas = self._isr_table.constantes.exencion_aguinaldo_umas
        bonus_exemption = uma_daily * exemption_umas

        return max(0, total_bonus - bonus_exemption)

    def _calculate_taxable_vacation_premium(self, income_data: IncomeData) -> float:
        """
        Calculate taxable portion of vacation premium after UMA-based exemption.
        Exemption: 15 UMAs daily
        """
        total_premium = income_data.gross_vacation_premium

        uma_daily = self._isr_table.constantes.valor_uma_diario
        exemption_umas = self._isr_table.constantes.exencion_prima_vacacional_umas
        premium_exemption = uma_daily * exemption_umas

        return max(0, total_premium - premium_exemption)

    def _estimate_withheld_tax(self, taxable_income_without_deductions: float) -> float:
        """Estimate withheld tax during the year"""
        return self._calculate_annual_tax(taxable_income_without_deductions)

    def _calculate_authorized_deductions(
        self,
        deduction_data: DeductionData,
        total_gross_income: float,
    ) -> Tuple[float, float, float, float]:
        """
        Calculate authorized deductions applying all caps and limits.

        Rules:
        1. Apply individual caps per deduction type
        2. Apply global cap: min(5 UMAs annual, 15% gross income)
        3. If global cap is exceeded, reduce proportionally

        Returns: (total_capped, personal, ppr, education)
        """
        uma_annual = self._isr_table.constantes.valor_uma_anual

        # Step 1: Apply individual caps
        general_cap = (
            uma_annual * self._isr_table.constantes.tope_general_deducciones_umas
        )
        limited_general_deductions = min(deduction_data.general_deductions, general_cap)

        ppr_cap = uma_annual * self._isr_table.constantes.tope_ppr_deducciones_umas
        limited_ppr = min(deduction_data.ppr_deductions, ppr_cap)

        education_caps = {
            "preescolar": self._isr_table.topes_colegiaturas.preescolar,
            "primaria": self._isr_table.topes_colegiaturas.primaria,
            "secundaria": self._isr_table.topes_colegiaturas.secundaria,
            "profesional_tecnico": self._isr_table.topes_colegiaturas.profesional_tecnico,
            "preparatoria": self._isr_table.topes_colegiaturas.preparatoria,
        }
        max_education_cap = max(education_caps.values()) if education_caps else 0
        limited_education_deductions = min(
            deduction_data.education_deductions, max_education_cap
        )

        # Step 2: Calculate global cap (5 UMAs OR 15% of gross, whichever is lower)
        cap_5_umas = uma_annual * 5
        cap_15_percent = total_gross_income * 0.15
        total_legal_cap = min(cap_5_umas, cap_15_percent)

        # Step 3: Apply global cap
        total_uncapped = (
            limited_general_deductions + limited_ppr + limited_education_deductions
        )
        total_capped = min(total_uncapped, total_legal_cap)

        # Step 4: If exceeded, reduce proportionally
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
