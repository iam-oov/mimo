"""
AI prompt templates for fiscal recommendations.
Reusable prompts that can be shared across projects.
"""

from typing import Dict, Any
from datetime import datetime

# Re-export multi-agent prompts for convenience
from src.infrastructure.ai_providers.multi_agent_prompts import (
    Personality,
    Profession,
    AgentModelConfig,
    build_agent_system_prompt,
    build_debate_context,
    build_round_prompt,
    build_synthesis_prompt,
    get_agent_model_config,
)

__all__ = [
    "build_fiscal_recommendation_prompt",
    "build_fallback_recommendations_prompt",
    "Personality",
    "Profession",
    "AgentModelConfig",
    "build_agent_system_prompt",
    "build_debate_context",
    "build_round_prompt",
    "build_synthesis_prompt",
    "get_agent_model_config",
]


def build_fiscal_recommendation_prompt(
    calculation_result: Any,
    user_data: Dict[str, Any],
    fiscal_year: int,
    uma_annual: float,
    general_deduction_limit: float,
    effective_deduction_limit: float,
    education_limits: Dict[str, float],
) -> str:
    """
    Build a comprehensive prompt for AI-powered fiscal recommendations.

    This prompt is designed for Mexican tax calculations (ISR) and generates
    personalized recommendations with a friendly cat persona ("Mimo el Gatito Fiscal").

    Args:
        calculation_result: Tax calculation entity with computed values
        user_data: User's input data including deductions
        fiscal_year: Fiscal year for the calculation
        uma_annual: Annual UMA value for the fiscal year
        general_deduction_limit: 5 UMAs limit
        effective_deduction_limit: Minimum between 5 UMAs and 15% gross income
        education_limits: Dictionary with education level limits (preescolar, primaria, secundaria)

    Returns:
        Formatted prompt string ready for AI provider consumption

    Example:
        >>> prompt = build_fiscal_recommendation_prompt(
        ...     calculation_result=tax_calc,
        ...     user_data={"deduction_data": {"general_deductions": 50000}},
        ...     fiscal_year=2024,
        ...     uma_annual=39606.36,
        ...     general_deduction_limit=198031.80,
        ...     effective_deduction_limit=180000.00,
        ...     education_limits={"preescolar": 14200, "primaria": 12900, "secundaria": 19900}
        ... )
    """
    # Determine greeting based on time of day
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        greeting = "¡Miau buenos días!"
    elif 12 <= current_hour < 19:
        greeting = "¡Miau buenas tardes!"
    else:
        greeting = "¡Miau buenas noches!"

    # Extract data from calculation result
    gross_income = calculation_result.gross_annual_income
    taxable_bonus = calculation_result.taxable_bonus
    taxable_vacation_premium = calculation_result.taxable_vacation_premium
    determined_tax = calculation_result.determined_tax
    withheld_tax = calculation_result.withheld_tax
    balance_in_favor = calculation_result.balance_in_favor

    # Extract deduction data
    deduction_data = user_data.get("deduction_data", {})
    current_general = deduction_data.get("general_deductions", 0)
    current_ppr = deduction_data.get("ppr_deductions", 0)
    current_education = deduction_data.get("education_deductions", 0)
    total_current_deductions = current_general + current_ppr + current_education

    # Calculate limits
    total_deduction_limit_15_percent = gross_income * 0.15
    remaining_deduction_space = effective_deduction_limit - total_current_deductions

    # Balance status text
    balance_status = "(Saldo a favor)" if balance_in_favor > 0 else "(A pagar)"

    prompt = f"""{greeting} Soy Mimo, tu fiscal experto

Analiza esta declaración anual y dame recomendaciones personalizadas en español de México.

📊 INFORMACIÓN FISCAL {fiscal_year}

**Ingresos Anuales:**
- Salarios: ${gross_income:,.2f}
- Aguinaldo gravable: ${taxable_bonus:,.2f}
- Prima vacacional gravable: ${taxable_vacation_premium:,.2f}

**Deducciones Actuales:**
- Personales: ${current_general:,.2f}
- PPR (Retiro): ${current_ppr:,.2f}
- Educación: ${current_education:,.2f}
- **Total deducido: ${total_current_deductions:,.2f}**

**Límites Oficiales {fiscal_year}:**
- UMA Anual: ${uma_annual:,.2f}
- Límite 5 UMAs: ${general_deduction_limit:,.2f}
- Límite 15% ingresos: ${total_deduction_limit_15_percent:,.2f}
- **Límite efectivo aplicable: ${effective_deduction_limit:,.2f}** (el menor entre ambos)
- **Espacio disponible para deducir: ${remaining_deduction_space:,.2f}**

**Resultado Fiscal:**
- ISR a cargo: ${determined_tax:,.2f}
- ISR retenido: ${withheld_tax:,.2f}
- Balance: ${balance_in_favor:,.2f} {balance_status}

🎯 INSTRUCCIONES CRÍTICAS:

1. **NUNCA recomiendes maximizar deducciones si ya están al límite o cerca del límite efectivo**
2. Si el espacio disponible es < $10,000, menciona que ya están optimizadas
3. Recomienda PPR solo si hay espacio significativo disponible
4. Menciona límites específicos de educación por nivel (Preescolar: ${education_limits.get("preescolar", 0):,.0f}, Primaria: ${education_limits.get("primaria", 0):,.0f}, Secundaria: ${education_limits.get("secundaria", 0):,.0f})
5. Formato Markdown con emojis y secciones claras
6. Máximo 500 palabras, directo y accionable

📝 FORMATO DE RESPUESTA:

## 🎯 Análisis Rápido
[Estado actual en 2-3 líneas]

## 💡 Recomendaciones Principales
[2-3 recomendaciones específicas y accionables]

## 📚 Tips Adicionales
[2-3 tips fiscales relevantes]

## ⚠️ Importante
[1-2 advertencias o consideraciones legales]
"""

    return prompt


def build_fallback_recommendations_prompt(
    fiscal_year: int,
    general_limit: float,
) -> str:
    """
    Build static fallback recommendations when AI providers are unavailable.

    Args:
        fiscal_year: Fiscal year for the calculation
        general_limit: 5 UMAs deduction limit

    Returns:
        Formatted markdown string with general fiscal recommendations
    """
    recommendations = f"""# 🐱 Recomendaciones Fiscales - Mimo

¡Miau! Como no pude conectarme con mis amigos AI, aquí van mis recomendaciones generales:

## 💰 Deducciones Personales
- **Límite anual**: ${general_limit:,.2f} (5 UMAs) o 15% de tus ingresos
- Gastos médicos, dentales, lentes
- Colegiaturas (con límites por nivel educativo)
- Intereses hipotecarios
- Donativos a instituciones autorizadas
- Aportaciones voluntarias a tu Afore

## 📚 Tips Importantes
1. **Guarda todas tus facturas** con requisitos fiscales
2. **Revisa tu constancia de retenciones** antes de declarar
3. **Considera un PPR** para reducir ISR y ahorrar para el retiro
4. **Declara a tiempo** para evitar multas y recargos

## ⚠️ Recuerda
- Las deducciones deben estar a tu nombre
- Paga con tarjeta, transferencia o cheque (no efectivo)
- Conserva facturas por 5 años

---
*Miau miau* 🐱 - Mimo, tu asistente fiscal

**Nota:** Estas son recomendaciones generales. Para asesoría personalizada, consulta a un contador.
"""

    return recommendations
