"""
AI prompt templates for fiscal recommendations.
Reusable prompts that can be shared across projects.
"""

from datetime import datetime
from typing import Any

# Re-export multi-agent prompts for convenience
from src.multi_agent.infrastructure.prompts.multi_agent_prompts import (
    AgentModelConfig,
    Personality,
    Profession,
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
    user_data: dict[str, Any],
    fiscal_year: int,
    uma_annual: float,
    general_deduction_limit: float,
    effective_deduction_limit: float,
    education_limits: dict[str, float],
) -> str:
    """
    Build a comprehensive prompt for AI-powered fiscal recommendations.

    This prompt defines the persona "Asesor Fiscal Digital" and instructs it
    to analyze a user's tax data to provide personalized recommendations
    WITH practical scenarios.

    Args:
        calculation_result: Tax calculation entity with computed values
        user_data: User's input data including deductions
        fiscal_year: Fiscal year for the calculation
        uma_annual: Annual UMA value for the fiscal year
        general_deduction_limit: 5 UMAs limit (absolute top limit)
        effective_deduction_limit: Minimum between 5 UMAs and 15% gross income
        education_limits: Dictionary with education level limits

    Returns:
        Formatted prompt string ready for AI provider consumption
    """
    # Determine greeting based on time of day for the AI to use
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        greeting = "Buenos días."
    elif 12 <= current_hour < 19:
        greeting = "Buenas tardes."
    else:
        greeting = "Buenas noches."

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
    balance_status = "(Saldo a favor)" if balance_in_favor > 0 else "(Impuesto a cargo)"

    # Calculate total income and current tax base
    total_taxable_income = gross_income + taxable_bonus + taxable_vacation_premium
    current_base_gravable = total_taxable_income - total_current_deductions

    # Dynamically build education limits string
    education_limits_parts = []
    for level, limit in education_limits.items():
        if limit > 0:
            education_limits_parts.append(f"{level.capitalize()}: ${limit:,.0f}")
    education_limits_details = ", ".join(education_limits_parts)
    if not education_limits_details:
        education_limits_details = "No se proporcionaron límites de educación."

    # --- Start of the Prompt ---
    prompt = f"""
**ROL Y PERSONA:**
Eres un "Asesor Fiscal Digital". Eres un experto en temas de impuestos del SAT en México. Tu tono es profesional, claro, directo y confiable. Tu objetivo es ayudar a los usuarios a entender su situación fiscal y darles recomendaciones prácticas y accionables. Usas un lenguaje preciso pero fácil de entender, evitando el argot fiscal complejo. Usas emojis profesionales (ej. 📊💡📚⚠️📈) para estructurar la información. Tu lenguaje es español de México.

**TAREA:**
Analiza la siguiente información fiscal de un usuario para el año {fiscal_year}. Con base en sus datos, genera un reporte de recomendaciones personalizadas. Para cada recomendación clave, DEBES incluir un "Ejemplo Práctico" con cálculos que muestre el impacto en el saldo. Finalmente, presenta un escenario global. Sigue estrictamente el formato.

**CONTEXTO (DATOS DEL USUARIO):**
📊 INFORMACIÓN FISCAL {fiscal_year}

**Ingresos Anuales (Gravables):**
- Salarios: ${gross_income:,.2f}
- Aguinaldo: ${taxable_bonus:,.2f}
- Prima Vacacional: ${taxable_vacation_premium:,.2f}
- **Total Ingresos Gravables: ${total_taxable_income:,.2f}**

**Deducciones Actuales Registradas:**
- Personales (Salud, Funerarios, etc.): ${current_general:,.2f}
- PPR (Plan Personal de Retiro): ${current_ppr:,.2f}
- Colegiaturas: ${current_education:,.2f}
- **Total Deducido Actual: ${total_current_deductions:,.2f}**

**Cálculo Base Actual:**
- **Base Gravable Actual: ${current_base_gravable:,.2f}** (Ingresos Gravables - Total Deducido)
- **Impuesto Calculado (ISR Causado): ${determined_tax:,.2f}**
- **Impuesto Retenido (Estimado): ${withheld_tax:,.2f}**
- **Balance Final Actual: ${balance_in_favor:,.2f} {balance_status}**

**Análisis de Límites de Deducción ({fiscal_year}):**
- Límite General (Tope de 5 UMAs Anuales): ${general_deduction_limit:,.2f}
- Límite del 15% (Sobre Ingresos Brutos): ${total_deduction_limit_15_percent:,.2f}
- **LÍMITE EFECTIVO (El menor de los dos anteriores): ${effective_deduction_limit:,.2f}**
- **ESPACIO DISPONIBLE PARA DEDUCIR: ${remaining_deduction_space:,.2f}**


**INSTRUCCIONES CRÍTICAS (DEBES SEGUIRLAS ESTRICTAMENTE):**
1.  **Saludo Inicial:** Comienza tu respuesta EXACTAMENTE con el saludo: "{greeting} Soy tu Asesor Fiscal Digital. Aquí está tu análisis."
2.  **Análisis del Espacio Disponible:** Esta es la lógica más importante.
    * Si el `ESPACIO DISPONIBLE PARA DEDUCIR` es **menor a $10,000 MXN**, **FELICITA** al usuario por su excelente optimización. Tus recomendaciones deben centrarse en **mantener** esos buenos hábitos. **NO incluyas ejemplos prácticos** para deducir más.
    * Si el `ESPACIO DISPONIBLE` es **grande**, tus recomendaciones deben enfocarse en **cómo aprovechar** ese espacio de forma inteligente.
3.  **Límites de Colegiaturas:** Al hablar de deducciones de educación, DEBES mencionar los topes anuales específicos: "{education_limits_details}".
4.  **Tono y Formato:** Usa Markdown, emojis profesionales (📊💡📚⚠️📈), y un lenguaje claro, directo y profesional.
5.  **Longitud:** Sé conciso y ve al grano. Máximo 600 palabras.

6.  **CÁLCULO DE ESCENARIOS (¡MUY IMPORTANTE!):**
    * Para CADA recomendación principal, debes agregar un sub-apartado `**Ejemplo Práctico:**`.
    * En ese ejemplo, simula un monto realista (ej. "si aportas $50,000 a tu PPR...").
    * Para calcular el impacto:
        1.  Toma la `Base Gravable Actual` (${current_base_gravable:,.2f}).
        2.  Resta el monto del ejemplo para obtener una `Nueva Base Gravable`.
        3.  Recalcula el `Nuevo Impuesto Causado` (tú eres un experto fiscal, conoces las tablas de ISR del {fiscal_year} para esta `Nueva Base Gravable`).
        4.  Calcula el `Ahorro en Impuestos` (Impuesto Original - Nuevo Impuesto).
        5.  Calcula el `Nuevo Saldo a Favor` (Balance Final Actual + Ahorro en Impuestos).
    * **Presenta el resultado claramente**, como: "si ahorras $50,000, tu ahorro en impuestos sería de $X,XXX y esto llevaría tu saldo a favor a $Y,YYY."

7.  **Escenario Global:** Al final, en la sección `📈 Tu Escenario Optimizado (Global)`, suma los ahorros de TODOS los ejemplos prácticos que diste y presenta un "Nuevo Saldo a Favor Potencial" total.

**FORMATO DE RESPUESTA REQUERIDO:**
(Debes seguir esta estructura exacta)

{greeting} Soy tu Asesor Fiscal Digital. Aquí está tu análisis.

## 📊 Análisis Rápido de tu Proyección
[Escribe 2-3 líneas sobre el estado actual. Menciona el {balance_status} y si su nivel de deducción es bueno o tiene mucha oportunidad (basado en la Instrucción Crítica #2).]

## 💡 Recomendaciones Estratégicas
[Escribe 2-3 recomendaciones *específicas* y accionables. Si no hay espacio (Instrucción #2), felicita y da tips de mantenimiento SIN ejemplos.]

* **Acción 1: [Título de la Recomendación]**
    * [Detalle de la recomendación...]
    * **Ejemplo Práctico:** [Aquí va el cálculo de la Instrucción #6. "Si aplicaras esto (ej. aportando $XX,XXX), tu ahorro en impuestos sería de $Y,YYY, y tu nuevo saldo a favor proyectado sería de $Z,ZZZ."]

* **Acción 2: [Título de la Recomendación]**
    * [Detalle de la recomendación...]
    * **Ejemplo Práctico:** [Aquí va el cálculo de la Instrucción #6.]

## 📈 Tu Escenario Optimizado (Global)
[Aquí, suma todos los ahorros de los ejemplos prácticos. Muestra un "Nuevo Saldo a Favor Potencial". "Si sigues estas estrategias, tu saldo a favor podría aumentar de ${balance_in_favor:,.2f} a un potencial de $XX,XXX.XX."]

## 📚 Puntos Clave Adicionales
[Escribe 2-3 tips generales relevantes, como métodos de pago (no efectivo), revisar el visor de nómina, etc.]

## ⚠️ Importante
[Incluye 1-2 advertencias legales. "Recuerda que esta es una *proyección* basada en los datos proporcionados. El cálculo final del SAT puede variar." y "Consulta siempre a un contador público para una asesoría personalizada."]
"""

    return prompt.strip()


def build_fallback_recommendations_prompt(
    fiscal_year: int,
    general_limit: float,
    education_limits: dict[str, float] | None = None,
) -> str:
    """
    Build static fallback recommendations when AI providers are unavailable.
    (Versión profesional sin personalidad de "Mimo")

    Args:
        fiscal_year: Fiscal year for the calculation
        general_limit: 5 UMAs deduction limit
        education_limits: Optional dict with education limits to include

    Returns:
        Formatted markdown string with general fiscal recommendations
    """

    # Build dynamic education string for fallback
    education_details = ""
    if education_limits:
        edu_parts = [
            f"  * {level.capitalize()}: (hasta ${limit:,.0f})"
            for level, limit in education_limits.items()
            if limit > 0
        ]
        if edu_parts:
            education_details = "\n".join(
                ["* **Colegiaturas** (con topes por nivel):", *edu_parts]
            )
    else:
        education_details = (
            "* **Colegiaturas** (con límites específicos por nivel educativo)"
        )

    recommendations = f"""
# 💡 Recomendaciones Fiscales Generales

El servicio de análisis personalizado no está disponible en este momento.
Sin embargo, aquí tienes nuestras recomendaciones generales para tu declaración del {fiscal_year}.

## 💰 Deducciones Personales (Generales)

El objetivo es reducir tu "Base Gravable". Estas deducciones comparten un límite global que es el menor entre **${general_limit:,.2f}** (5 UMAs anuales) o el 15% de tus ingresos totales.

* **Gastos de Salud**: Honorarios médicos, dentales, psicólogos, nutriólogos, gastos hospitalarios, lentes ópticos (hasta $2,500).
* **Intereses Hipotecarios**: Los intereses reales de tu crédito INFONAVIT o bancario.
* **Gastos Funerarios**: De tu cónyuge, padres, hijos, etc.
* **Donativos**: A instituciones autorizadas.
{education_details}

## 📈 Aportaciones (con su propio límite)
Estas deducciones tienen su propio tope, independiente del anterior.

* **Plan Personal de Retiro (PPR)**: Te permite deducir hasta el 10% de tu ingreso anual o 5 UMAs, lo que sea menor.
* **Aportaciones Voluntarias a tu AFORE**: (Bajo el mismo rubro que el PPR).

## 📚 Tips Esenciales
1.  **Facturación (CFDI)**: Solicita factura (CFDI) por todos estos gastos.
2.  **Método de Pago**: Paga siempre con medios electrónicos (tarjeta de crédito/débito, transferencia). **Las deducciones pagadas en efectivo no son válidas.**
3.  **Visor de Nómina**: Antes de declarar, revisa el "Visor de Nómina" en el portal del SAT para asegurar que tus recibos de nómina estén correctos.
4.  **Fechas Límite**: La declaración anual de personas físicas es en Abril.

## ⚠️ Advertencia
Esta es una guía general y no constituye una asesoría personalizada. Para revisar tu caso específico, te recomendamos consultar con un contador público.
"""

    return recommendations.strip()
