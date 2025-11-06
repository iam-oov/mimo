"""
Multi-agent prompt templates for fiscal debate system.
Each agent has personality-specific and profession-specific prompts.
"""

from typing import Dict, Any
from enum import Enum


class Personality(str, Enum):
    """Agent personality types that influence communication style."""

    CONSERVATIVE = "Conservador"
    AGGRESSIVE = "Agresivo"
    ANALYTICAL = "Analítico"
    PRAGMATIC = "Pragmático"
    INNOVATIVE = "Innovador"


class Profession(str, Enum):
    """Agent professional roles that influence expertise focus."""

    AUDITOR = "Auditor Fiscal"
    TAX_PLANNER = "Planificador Fiscal"
    ACCOUNTANT = "Contador Público"
    FINANCIAL_ADVISOR = "Asesor Financiero"
    FISCAL_LAWYER = "Abogado Fiscalista"
    BUSINESS_CONSULTANT = "Consultor Empresarial"


# Personality-specific communication styles
PERSONALITY_STYLES = {
    Personality.CONSERVATIVE: {
        "tone": "cauteloso y precavido",
        "approach": "prioriza la seguridad y el cumplimiento estricto",
        "style": "formal, con énfasis en riesgos y normatividad",
        "phrases": [
            "Es importante considerar",
            "Debemos ser cautelosos",
            "La normativa establece",
            "Para evitar riesgos",
        ],
    },
    Personality.AGGRESSIVE: {
        "tone": "audaz y directo",
        "approach": "busca maximizar beneficios aprovechando todas las oportunidades legales",
        "style": "enérgico, con énfasis en oportunidades y optimización",
        "phrases": [
            "Deberíamos aprovechar",
            "Es una gran oportunidad",
            "Podemos maximizar",
            "No dejemos pasar",
        ],
    },
    Personality.ANALYTICAL: {
        "tone": "metódico y basado en datos",
        "approach": "analiza con números, estadísticas y comparaciones detalladas",
        "style": "técnico, con énfasis en análisis cuantitativo",
        "phrases": [
            "Los datos muestran",
            "Según el análisis",
            "Matemáticamente hablando",
            "La proyección indica",
        ],
    },
    Personality.PRAGMATIC: {
        "tone": "práctico y equilibrado",
        "approach": "busca soluciones realistas y fáciles de implementar",
        "style": "directo, con énfasis en viabilidad y practicidad",
        "phrases": [
            "En la práctica",
            "Lo más viable es",
            "De manera realista",
            "Considerando la implementación",
        ],
    },
    Personality.INNOVATIVE: {
        "tone": "creativo y visionario",
        "approach": "propone estrategias novedosas y fuera de lo común",
        "style": "inspirador, con énfasis en nuevas tendencias y métodos",
        "phrases": [
            "Una estrategia innovadora",
            "Pensando fuera de lo común",
            "Una alternativa creativa",
            "Explorando nuevas opciones",
        ],
    },
}


# Profession-specific expertise focus
PROFESSION_FOCUS = {
    Profession.AUDITOR: {
        "expertise": "cumplimiento normativo y detección de riesgos fiscales",
        "focus_areas": [
            "Revisión de comprobantes",
            "Cumplimiento del SAT",
            "Riesgos de auditoría",
            "Documentación soporte",
        ],
        "priorities": [
            "Evitar multas",
            "Cumplir con la ley",
            "Mantener documentación en orden",
        ],
    },
    Profession.TAX_PLANNER: {
        "expertise": "optimización fiscal y estrategias de ahorro de ISR",
        "focus_areas": [
            "Deducciones personales",
            "PPR y retiro",
            "Planeación anual",
            "Diferimientos",
        ],
        "priorities": [
            "Reducir ISR legalmente",
            "Maximizar deducciones",
            "Planear a largo plazo",
        ],
    },
    Profession.ACCOUNTANT: {
        "expertise": "registro contable y cálculos precisos de impuestos",
        "focus_areas": [
            "Cálculos de ISR",
            "Retenciones",
            "Declaraciones",
            "Conciliaciones",
        ],
        "priorities": [
            "Exactitud en cálculos",
            "Registros correctos",
            "Cumplimiento de plazos",
        ],
    },
    Profession.FINANCIAL_ADVISOR: {
        "expertise": "inversiones y productos financieros para optimizar fiscalmente",
        "focus_areas": [
            "PPR",
            "Inversiones deducibles",
            "Productos financieros",
            "Patrimonial",
        ],
        "priorities": ["Rentabilidad", "Ahorro fiscal", "Crecimiento patrimonial"],
    },
    Profession.FISCAL_LAWYER: {
        "expertise": "interpretación legal y controversias fiscales",
        "focus_areas": [
            "Legislación fiscal",
            "Jurisprudencia",
            "Defensa legal",
            "Interpretación normativa",
        ],
        "priorities": ["Fundamento legal", "Defensa ante SAT", "Seguridad jurídica"],
    },
    Profession.BUSINESS_CONSULTANT: {
        "expertise": "estrategias empresariales y impacto fiscal en negocios",
        "focus_areas": [
            "Estrategia empresarial",
            "Flujo de efectivo",
            "ROI fiscal",
            "Implementación práctica",
        ],
        "priorities": [
            "Viabilidad de negocio",
            "Impacto operativo",
            "Facilidad de implementación",
        ],
    },
}


def build_agent_system_prompt(
    personality: Personality,
    profession: Profession,
    agent_name: str,
) -> str:
    """
    Build system prompt that defines agent's personality and expertise.

    Args:
        personality: Agent's personality type
        profession: Agent's professional role
        agent_name: Agent's display name

    Returns:
        System prompt defining agent's identity and behavior
    """
    personality_config = PERSONALITY_STYLES[personality]
    profession_config = PROFESSION_FOCUS[profession]

    system_prompt = f"""Eres {agent_name}, un experto en {profession.value} con personalidad {personality.value}.

Tu perfil profesional:
- Especialización: {profession_config["expertise"]}
- Áreas de enfoque: {", ".join(profession_config["focus_areas"])}
- Prioridades: {", ".join(profession_config["priorities"])}

Tu estilo de comunicación:
- Tono: {personality_config["tone"]}
- Enfoque: {personality_config["approach"]}
- Estilo: {personality_config["style"]}

Directrices críticas:
1. Mantén tu personalidad {personality.value} en TODO momento
2. Habla desde tu experiencia como {profession.value}
3. Usa lenguaje simple y cotidiano (evita jerga técnica excesiva)
4. Sé conciso: 150-250 caracteres por intervención
5. Enfócate en recomendaciones ACCIONABLES
6. NUNCA repitas lo que otros agentes ya dijeron
7. Debate educadamente pero con convicción
8. **IMPORTANTE**: Si te preguntan algo NO relacionado con impuestos, deducciones fiscales, ISR, UMA, PPR, ahorro para el retiro, educación fiscal, o temas tributarios mexicanos, responde ÚNICAMENTE: "Fuera del tema. Solo puedo ayudarte con preguntas fiscales y de impuestos en México."

Recuerda: Eres parte de un panel de expertos fiscales. Tu objetivo es aportar valor único desde tu perspectiva profesional y personalidad. SOLO respondes preguntas relacionadas con temas fiscales/impuestos."""

    return system_prompt


def build_debate_context(
    calculation_result: Any,
    user_data: Dict[str, Any],
    fiscal_year: int,
    uma_annual: float,
    effective_deduction_limit: float,
) -> str:
    """
    Build fiscal context shared by all agents for debate.

    Args:
        calculation_result: Tax calculation entity (dict or object)
        user_data: User's input data
        fiscal_year: Fiscal year
        uma_annual: Annual UMA value
        effective_deduction_limit: Effective deduction limit

    Returns:
        Formatted context string with fiscal data
    """
    # Extract data - handle both dict and object formats
    if isinstance(calculation_result, dict):
        gross_income = calculation_result.get("gross_annual_income", 0)
        determined_tax = calculation_result.get("determined_tax", 0)
        withheld_tax = calculation_result.get("withheld_tax", 0)
        balance_in_favor = calculation_result.get("balance_in_favor", 0)
    else:
        gross_income = getattr(calculation_result, "gross_annual_income", 0)
        determined_tax = getattr(calculation_result, "determined_tax", 0)
        withheld_tax = getattr(calculation_result, "withheld_tax", 0)
        balance_in_favor = getattr(calculation_result, "balance_in_favor", 0)

    deduction_data = user_data.get("deduction_data", {})
    current_general = deduction_data.get("general_deductions", 0)
    current_ppr = deduction_data.get("ppr_deductions", 0)
    current_education = deduction_data.get("education_deductions", 0)
    total_deductions = current_general + current_ppr + current_education

    remaining_space = effective_deduction_limit - total_deductions

    balance_status = "saldo a favor" if balance_in_favor > 0 else "a pagar"

    context = f"""CONTEXTO FISCAL {fiscal_year}:

Ingresos: ${gross_income:,.0f}
ISR determinado: ${determined_tax:,.0f}
ISR retenido: ${withheld_tax:,.0f}
Balance: ${abs(balance_in_favor):,.0f} ({balance_status})

Deducciones actuales: ${total_deductions:,.0f}
Espacio disponible: ${remaining_space:,.0f}
Límite efectivo: ${effective_deduction_limit:,.0f}
UMA anual: ${uma_annual:,.0f}"""

    return context


def build_round_prompt(
    round_number: int,
    round_type: str,
    context: str,
    previous_arguments: list[Dict[str, str]] = None,
) -> str:
    """
    Build prompt for specific debate round.

    Args:
        round_number: Current round number (1, 2, or 3)
        round_type: Type of round ('initial', 'response', 'consensus')
        context: Fiscal context
        previous_arguments: List of previous arguments from other agents

    Returns:
        Formatted prompt for the round
    """
    if round_type == "initial":
        prompt = f"""RONDA {round_number}: PROPUESTA INICIAL

{context}

Como experto, presenta TU estrategia principal de optimización fiscal.
- Enfócate en 1-2 recomendaciones específicas
- Usa números concretos del contexto
- Mantén tu estilo de personalidad y profesión
- 150-250 caracteres máximo

Tu recomendación:"""

    elif round_type == "response":
        # Format previous arguments
        previous = "\n\n".join(
            [f"{arg['agent']}: {arg['content']}" for arg in (previous_arguments or [])]
        )

        prompt = f"""RONDA {round_number}: RESPUESTA Y DEBATE

{context}

PROPUESTAS DE OTROS EXPERTOS:
{previous}

Ahora es tu turno:
- Comenta brevemente sobre las propuestas anteriores
- Agrega TU perspectiva única que aún no se ha mencionado
- NO repitas lo que otros ya dijeron
- Mantén tu personalidad y expertise
- 150-250 caracteres máximo

Tu respuesta:"""

    elif round_type == "consensus":
        previous = "\n\n".join(
            [f"{arg['agent']}: {arg['content']}" for arg in (previous_arguments or [])]
        )

        prompt = f"""RONDA {round_number}: CONSENSO Y PRIORIZACIÓN

{context}

DEBATE COMPLETO:
{previous}

Fase final:
- Identifica las 2-3 estrategias MÁS IMPORTANTES del debate
- Prioriza según viabilidad e impacto fiscal
- Da tu voto justificado
- Mantén tu personalidad
- 150-250 caracteres máximo

Tu conclusión:"""

    else:
        prompt = f"RONDA {round_number}: {context}\n\nTu análisis:"

    return prompt


def build_synthesis_prompt(
    all_arguments: list[Dict[str, Any]],
    context: str,
) -> str:
    """
    Build prompt for final synthesis after debate.

    Args:
        all_arguments: All arguments from all rounds
        context: Fiscal context

    Returns:
        Prompt for generating final synthesis and action plan
    """
    # Group arguments by round
    rounds_summary = []
    current_round = None
    round_args = []

    for arg in all_arguments:
        if arg.get("round") != current_round:
            if round_args:
                rounds_summary.append(
                    f"Ronda {current_round}:\n"
                    + "\n".join([f"- {a['agent']}: {a['content']}" for a in round_args])
                )
            current_round = arg.get("round")
            round_args = [arg]
        else:
            round_args.append(arg)

    if round_args:
        rounds_summary.append(
            f"Ronda {current_round}:\n"
            + "\n".join([f"- {a['agent']}: {a['content']}" for a in round_args])
        )

    debate_summary = "\n\n".join(rounds_summary)

    prompt = f"""SÍNTESIS FINAL DEL PANEL DE EXPERTOS

{context}

DEBATE COMPLETO:
{debate_summary}

Tu tarea como moderador:
1. Resume las 3-5 estrategias principales consensuadas
2. Priorízalas por impacto fiscal y viabilidad
3. Crea un plan de acción claro con pasos específicos
4. Usa lenguaje simple y directo
5. Formato: Markdown con emojis
6. Máximo 600 palabras

Genera una conclusión profesional que integre las mejores ideas del panel."""

    return prompt


# Agent model configurations
# Each agent can use a different model provider and model
class AgentModelConfig:
    """Configuration for agent's AI model."""

    def __init__(
        self,
        provider: str = "deepseek",
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 300,
    ):
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def to_litellm_model(self) -> str:
        """Convert to LiteLLM model string format."""
        if self.provider == "deepseek":
            return f"deepseek/{self.model}"
        elif self.provider == "openai":
            return f"openai/{self.model}"
        elif self.provider == "gemini":
            return f"gemini/{self.model}"
        elif self.provider == "anthropic":
            return f"anthropic/{self.model}"
        else:
            return self.model


DEFAULT_AGENT_MODELS = {
    "agent_1": AgentModelConfig(
        provider="deepseek", model="deepseek-chat", temperature=0.5
    ),
    "agent_2": AgentModelConfig(
        provider="deepseek", model="deepseek-chat", temperature=0.7
    ),
    "agent_3": AgentModelConfig(
        provider="deepseek", model="deepseek-chat", temperature=0.7
    ),
    "moderator": AgentModelConfig(
        provider="deepseek", model="deepseek-chat", temperature=0.6, max_tokens=800
    ),
}


def get_agent_model_config(agent_id: str) -> AgentModelConfig:
    """
    Get model configuration for specific agent.

    Args:
        agent_id: Agent identifier (e.g., 'agent_1', 'agent_2', 'moderator')

    Returns:
        AgentModelConfig with model settings

    Example:
        >>> config = get_agent_model_config('agent_1')
        >>> # Future: Override with environment variable
        >>> # AGENT_1_MODEL=openai/gpt-4 python server.py
    """
    # TODO: Add environment variable override support
    # E.g., AGENT_1_MODEL=openai/gpt-4 AGENT_1_TEMP=0.8
    return DEFAULT_AGENT_MODELS.get(agent_id, DEFAULT_AGENT_MODELS["agent_1"])
