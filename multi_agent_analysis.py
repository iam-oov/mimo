#!/usr/bin/env python3
"""
Multi-agent fiscal analysis system.
3 experts with random personalities/professions debate tax optimization strategies.
Follows SOLID principles and project conventions.
"""

import os
import random
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Generator
from dataclasses import dataclass
from enum import Enum
from collections import Counter

import google.generativeai as genai
import requests
from dotenv import load_dotenv

from tabla_isr_constants import get_tabla_isr

load_dotenv()

# Configuration for debate character limits
DEBATE_MIN_CHARACTER = int(os.getenv("DEBATE_MIN_CHARACTER", "150"))
DEBATE_MAX_CHARACTER = int(os.getenv("DEBATE_MAX_CHARACTER", "250"))


class Personality(Enum):
    """Available personality types for agents."""

    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"
    ANALYTICAL = "analytical"
    PRAGMATIC = "pragmatic"
    INNOVATIVE = "innovative"


class Profession(Enum):
    """Available professions for fiscal experts."""

    AUDITOR = "auditor"
    TAX_PLANNER = "tax_planner"
    ACCOUNTANT = "accountant"
    FINANCIAL_ADVISOR = "financial_advisor"
    FISCAL_LAWYER = "fiscal_lawyer"
    BUSINESS_CONSULTANT = "business_consultant"


@dataclass
class PersonalityTraits:
    """Defines personality characteristics for prompts."""

    name: str
    description: str
    approach: str


@dataclass
class ProfessionTraits:
    """Defines professional expertise for prompts."""

    title: str
    expertise: str
    focus_areas: str


PERSONALITY_CONFIGS: Dict[Personality, PersonalityTraits] = {
    Personality.CONSERVATIVE: PersonalityTraits(
        name="Conservador",
        description="Cauteloso y meticuloso, prioriza seguridad sobre riesgo",
        approach="Enfócate en deducciones 100% seguras y documentadas. Evita zonas grises.",
    ),
    Personality.AGGRESSIVE: PersonalityTraits(
        name="Agresivo",
        description="Audaz y optimizador, busca maximizar beneficios legales",
        approach="Explora todas las deducciones permitidas. Maximiza cada peso legalmente posible.",
    ),
    Personality.ANALYTICAL: PersonalityTraits(
        name="Analítico",
        description="Basado en datos y cálculos precisos",
        approach="Usa números exactos y proyecciones. Cada recomendación debe tener cálculo respaldado.",
    ),
    Personality.PRAGMATIC: PersonalityTraits(
        name="Pragmático",
        description="Práctico y enfocado en implementación realista",
        approach="Recomienda solo lo que el contribuyente pueda implementar fácilmente. Prioriza viabilidad.",
    ),
    Personality.INNOVATIVE: PersonalityTraits(
        name="Innovador",
        description="Creativo y propone estrategias no convencionales",
        approach="Busca estrategias fiscales creativas y poco utilizadas pero legales. Piensa fuera de la caja.",
    ),
}

PROFESSION_CONFIGS: Dict[Profession, ProfessionTraits] = {
    Profession.AUDITOR: ProfessionTraits(
        title="Auditor Fiscal",
        expertise="Revisión de cumplimiento y riesgos fiscales",
        focus_areas="Identifica áreas de mejora en documentación y aprovechamiento de deducciones existentes",
    ),
    Profession.TAX_PLANNER: ProfessionTraits(
        title="Planeador Fiscal",
        expertise="Diseño de estrategias fiscales a largo plazo",
        focus_areas="Propone estrategias multianuales para maximizar beneficios fiscales sostenibles",
    ),
    Profession.ACCOUNTANT: ProfessionTraits(
        title="Contador Público",
        expertise="Contabilidad y cálculos fiscales precisos",
        focus_areas="Análisis detallado de números y proyecciones exactas de ahorros fiscales",
    ),
    Profession.FINANCIAL_ADVISOR: ProfessionTraits(
        title="Asesor Financiero",
        expertise="Optimización de inversiones y patrimonio",
        focus_areas="Relaciona estrategia fiscal con salud financiera integral del contribuyente",
    ),
    Profession.FISCAL_LAWYER: ProfessionTraits(
        title="Abogado Fiscalista",
        expertise="Marco legal y jurisprudencia fiscal",
        focus_areas="Asegura legalidad completa y cita fundamentos legales de cada recomendación",
    ),
    Profession.BUSINESS_CONSULTANT: ProfessionTraits(
        title="Consultor Empresarial",
        expertise="Estrategia de negocios y eficiencia operativa",
        focus_areas="Vincula optimización fiscal con estrategia empresarial y crecimiento",
    ),
}


class LanguageModelProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def generate_stream(
        self, messages: List[Dict[str, str]]
    ) -> Generator[str, None, None]:
        """Generates streaming response from the model."""
        pass


class DeepSeekProvider(LanguageModelProvider):
    """DeepSeek implementation via OpenAI-compatible API."""

    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.base_url = "https://api.deepseek.com/v1"

        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not found")

    def generate_stream(
        self, messages: List[Dict[str, str]]
    ) -> Generator[str, None, None]:
        """Streams response from DeepSeek."""
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True,
                    "temperature": 0.7,
                    "max_tokens": 600,
                },
                stream=True,
                timeout=30,
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    line_str = line.decode("utf-8")
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"[Error generando respuesta: {str(e)}]"


class GeminiProvider(LanguageModelProvider):
    """Gemini implementation as fallback."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def generate_stream(
        self, messages: List[Dict[str, str]]
    ) -> Generator[str, None, None]:
        """Streams response from Gemini."""
        try:
            prompt = "\n\n".join([f"{m['role']}: {m['content']}" for m in messages])
            response = self.model.generate_content(
                prompt,
                stream=True,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7, max_output_tokens=600
                ),
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"[Error generando respuesta: {str(e)}]"


class ModelProviderFactory:
    """Factory for creating LLM providers."""

    @staticmethod
    def create() -> LanguageModelProvider:
        """Creates provider with fallback chain: DeepSeek -> Gemini."""
        try:
            return DeepSeekProvider()
        except ValueError:
            try:
                return GeminiProvider()
            except ValueError:
                raise ValueError(
                    "No AI provider available. Set DEEPSEEK_API_KEY or GEMINI_API_KEY"
                )


@dataclass
class AgentProfile:
    """Complete profile for a fiscal expert agent."""

    name: str
    personality: Personality
    profession: Profession
    personality_traits: PersonalityTraits
    profession_traits: ProfessionTraits


class FiscalExpertAgent:
    """Represents a fiscal expert with specific personality and profession."""

    def __init__(self, profile: AgentProfile, model_provider: LanguageModelProvider):
        self.profile = profile
        self.model_provider = model_provider

    def _build_system_prompt(self) -> str:
        """Builds the system prompt defining agent's role and constraints."""
        return f"""Eres {self.profile.name}, un {self.profile.profession_traits.title}.

PERSONALIDAD: {self.profile.personality_traits.name}
{self.profile.personality_traits.description}

ENFOQUE PROFESIONAL:
{self.profile.profession_traits.expertise}
{self.profile.profession_traits.focus_areas}

ESTRATEGIA:
{self.profile.personality_traits.approach}

RESTRICCIONES CRÍTICAS:
- Tu respuesta debe tener EXACTAMENTE entre {DEBATE_MIN_CHARACTER}-{DEBATE_MAX_CHARACTER} caracteres
- Sé específico y proporciona números concretos
- Enfócate en una estrategia clara desde tu perspectiva profesional
- Mantén tono profesional pero accesible
- Usa tu personalidad {self.profile.personality_traits.name} en tus argumentos"""

    def generate_analysis(
        self, taxpayer_context: str, conversation_history: str, other_agents: List[str]
    ) -> Generator[str, None, None]:
        """Generates fiscal analysis from this agent's perspective."""
        others_names = ", ".join(other_agents)

        # Determine if this is first round or if there's debate to respond to
        has_prior_discussion = len(conversation_history.strip()) > 100

        if has_prior_discussion:
            debate_instruction = f"""
DEBATE ACTIVO: Los otros expertos ({others_names}) ya han dado sus opiniones.

TU RESPONSABILIDAD:
1. Proporciona tu análisis profesional desde tu perspectiva como {self.profile.profession_traits.title}
2. DEBATE: Identifica y desafía los puntos con los que NO estés de acuerdo de los otros expertos
3. ARGUMENTA: Explica por qué tu enfoque es más apropiado para este caso específico
4. Sé directo y profesional en tus críticas constructivas

Si hay algo que consideres crítico aclarar o corregir de lo dicho anteriormente, hazlo con datos concretos."""
        else:
            debate_instruction = f"""
PRIMERA INTERVENCIÓN: Eres el primero en analizar este caso.

TU RESPONSABILIDAD:
1. Proporciona tu análisis profesional desde tu perspectiva como {self.profile.profession_traits.title}
2. Presenta tu estrategia recomendada con datos concretos
3. Identifica los puntos más críticos que los siguientes expertos deberían considerar"""

        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {
                "role": "user",
                "content": f"""
Estás en una mesa de debate fiscal con {others_names}.

CONTEXTO DEL CONTRIBUYENTE:
{taxpayer_context}

CONVERSACIÓN PREVIA:
{conversation_history}

{debate_instruction}

IMPORTANTE: Tu respuesta debe tener entre {DEBATE_MIN_CHARACTER}-{DEBATE_MAX_CHARACTER} caracteres. Sé específico con números y estrategias concretas.""",
            },
        ]

        yield from self.model_provider.generate_stream(messages)

    def vote(
        self,
        conversation_history: str,
        options: List[str],
        exclude_self_index: int = -1,
    ) -> Generator[str, None, None]:
        """Votes for the best strategy discussed."""
        # Filter out own option if exclude_self_index is provided
        filtered_options = []
        option_mapping = {}  # Maps displayed number to actual index

        for i, opt in enumerate(options):
            if i != exclude_self_index:
                filtered_options.append(opt)
                option_mapping[len(filtered_options)] = i + 1

        options_text = "\n".join(
            [f"{i + 1}. {opt}" for i, opt in enumerate(filtered_options)]
        )

        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {
                "role": "user",
                "content": f"""
Basándote en la discusión, vota por la mejor estrategia de LOS OTROS EXPERTOS (no puedes votar por ti mismo).

OPCIONES:
{options_text}

CONVERSACIÓN:
{conversation_history}

Responde SOLO con el número (1 o 2) de la estrategia que consideras mejor desde tu perspectiva profesional como {self.profile.profession_traits.title}.
Responde únicamente el número.""",
            },
        ]

        yield from self.model_provider.generate_stream(messages)


class ModeratorAgent:
    """Moderates the multi-agent discussion."""

    def __init__(self, model_provider: LanguageModelProvider):
        self.model_provider = model_provider
        self.name = "Moderador Fiscal"

    def _build_system_prompt(self) -> str:
        """Builds moderator's system prompt."""
        return f"""Eres un Moderador Fiscal neutral y eficiente.

RESPONSABILIDADES:
- Presentar el caso brevemente
- Resumir puntos clave de cada ronda
- Anunciar fases de votación
- Sintetizar conclusión final

RESTRICCIONES:
- Tus intervenciones deben tener entre {DEBATE_MIN_CHARACTER}-{DEBATE_MAX_CHARACTER} caracteres
- Sé conciso y objetivo
- No tomes partido por ningún experto
- Mantén el enfoque en optimización fiscal"""

    def introduce_case(
        self, taxpayer_context: str, experts: List[str]
    ) -> Generator[str, None, None]:
        """Introduces the fiscal case to analyze."""
        experts_list = ", ".join(experts)

        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {
                "role": "user",
                "content": f"""
Presenta brevemente el caso fiscal a analizar. Los expertos presentes son: {experts_list}

DATOS DEL CONTRIBUYENTE:
{taxpayer_context}

Da la bienvenida y explica que analizarán cómo optimizar su situación fiscal.
IMPORTANTE: Tu introducción debe tener entre {DEBATE_MIN_CHARACTER}-{DEBATE_MAX_CHARACTER} caracteres.""",
            },
        ]

        yield from self.model_provider.generate_stream(messages)

    def summarize_round(
        self, round_number: int, conversation: str
    ) -> Generator[str, None, None]:
        """Summarizes key points from a discussion round."""
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {
                "role": "user",
                "content": f"""
Resume los puntos clave de la Ronda {round_number}.

DISCUSIÓN:
{conversation}

ENFOQUE DEL RESUMEN:
- Destaca las propuestas principales de cada experto
- Identifica los puntos de ACUERDO y DESACUERDO entre los expertos
- Menciona brevemente qué aspectos están siendo debatidos
- Mantén neutralidad, no favorezas ninguna postura

IMPORTANTE: Tu resumen debe tener entre {DEBATE_MIN_CHARACTER}-{DEBATE_MAX_CHARACTER} caracteres.""",
            },
        ]

        yield from self.model_provider.generate_stream(messages)

    def announce_voting(self) -> Generator[str, None, None]:
        """Announces the voting phase."""
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {
                "role": "user",
                "content": f"""
Anuncia que es momento de votar por la mejor estrategia fiscal.
Explica que cada experto votará por la propuesta más sólida.
IMPORTANTE: Tu anuncio debe tener entre {DEBATE_MIN_CHARACTER}-{DEBATE_MAX_CHARACTER} caracteres.""",
            },
        ]

        yield from self.model_provider.generate_stream(messages)

    def conclude(
        self, conversation: str, winning_strategy: str, vote_count: Dict[str, int]
    ) -> Generator[str, None, None]:
        """Provides final conclusion for the taxpayer."""
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {
                "role": "user",
                "content": f"""
Proporciona la conclusión final para el contribuyente.

ESTRATEGIA GANADORA: {winning_strategy}
VOTOS: {vote_count}

DISCUSIÓN COMPLETA:
{conversation}

Resume la estrategia ganadora y los beneficios esperados para el contribuyente.
IMPORTANTE: Tu conclusión debe tener entre {DEBATE_MIN_CHARACTER}-{DEBATE_MAX_CHARACTER} caracteres.""",
            },
        ]

        yield from self.model_provider.generate_stream(messages)


class AgentFactory:
    """Factory for creating agents with random profiles."""

    @staticmethod
    def create_random_experts(count: int = 3) -> List[FiscalExpertAgent]:
        """Creates specified number of experts with unique random profiles."""
        if count > min(len(Personality), len(Profession)):
            raise ValueError(f"Cannot create {count} unique experts")

        selected_personalities = random.sample(list(Personality), count)
        selected_professions = random.sample(list(Profession), count)

        expert_names = [
            "Dr. Martínez",
            "Lic. García",
            "Mtra. López",
            "Ing. Rodríguez",
            "C.P. Hernández",
            "Dr. Ramírez",
        ]
        random.shuffle(expert_names)

        experts = []
        for i in range(count):
            profile = AgentProfile(
                name=expert_names[i],
                personality=selected_personalities[i],
                profession=selected_professions[i],
                personality_traits=PERSONALITY_CONFIGS[selected_personalities[i]],
                profession_traits=PROFESSION_CONFIGS[selected_professions[i]],
            )

            provider = ModelProviderFactory.create()
            experts.append(FiscalExpertAgent(profile, provider))

        return experts

    @staticmethod
    def create_moderator() -> ModeratorAgent:
        """Creates the moderator agent."""
        provider = ModelProviderFactory.create()
        return ModeratorAgent(provider)


def build_taxpayer_context(
    calculation_result: Any, user_data: Dict[str, Any], fiscal_year: int
) -> str:
    """Builds comprehensive taxpayer context for agents."""
    taxpayer_data = user_data["contribuyente"]
    isr_table = get_tabla_isr(fiscal_year)
    constants = isr_table.constantes

    return f"""PERFIL FISCAL {fiscal_year}:
- Nombre: {taxpayer_data.get("nombre_o_referencia", "Contribuyente")}
- Ingreso bruto anual: ${calculation_result.gross_annual_income:,.2f}
- Ingreso gravado: ${calculation_result.total_taxable_income:,.2f}
- Deducciones actuales: ${calculation_result.authorized_deductions:,.2f}
  · Generales: ${calculation_result.personal_deductions:,.2f}
  · PPR/Afore: ${calculation_result.ppr_deductions:,.2f}
  · Colegiaturas: ${calculation_result.education_deductions:,.2f}
- Base gravable: ${calculation_result.taxable_base:,.2f}
- Impuesto determinado: ${calculation_result.determined_tax:,.2f}
- Impuesto retenido: ${calculation_result.withheld_tax:,.2f}
- Saldo a favor: ${calculation_result.balance_in_favor:,.2f}
- Saldo a pagar: ${calculation_result.balance_to_pay:,.2f}

LÍMITES {fiscal_year}:
- Tope deducciones generales: {constants.tope_general_deducciones_umas} UMAs (${constants.valor_uma_anual * constants.tope_general_deducciones_umas:,.0f})
- Tope PPR/Afore: {constants.tope_ppr_deducciones_umas} UMAs (${constants.valor_uma_anual * constants.tope_ppr_deducciones_umas:,.0f})
- UMA anual: ${constants.valor_uma_anual:,.2f}"""


@dataclass
class MultiAgentAnalysisResult:
    """Complete result from multi-agent analysis."""

    expert_profiles: List[Dict[str, str]]
    moderator_name: str
    rounds: List[Dict[str, Any]]
    voting_results: Dict[str, Any]
    conclusion: str
    full_transcript: str


class MultiAgentConversationOrchestrator:
    """Orchestrates the complete multi-agent fiscal analysis session."""

    def __init__(
        self,
        experts: List[FiscalExpertAgent],
        moderator: ModeratorAgent,
        taxpayer_context: str,
    ):
        self.experts = experts
        self.moderator = moderator
        self.taxpayer_context = taxpayer_context
        self.conversation_history = ""
        self.rounds_data: List[Dict[str, Any]] = []

    def _collect_stream(self, generator: Generator[str, None, None]) -> str:
        """Collects all chunks from a generator into a single string."""
        chunks = []
        for chunk in generator:
            chunks.append(chunk)
        return "".join(chunks)

    def _get_expert_names(self) -> List[str]:
        """Returns list of expert names."""
        return [
            f"{e.profile.name} ({e.profile.profession_traits.title})"
            for e in self.experts
        ]

    def run_analysis(self, total_rounds: int = 3) -> MultiAgentAnalysisResult:
        """Runs the complete multi-agent analysis with 3 rounds + voting + conclusion."""

        self._introduction_phase()

        for round_num in range(1, total_rounds + 1):
            self._discussion_round(round_num)

        voting_results = self._voting_phase()

        conclusion = self._conclusion_phase(voting_results)

        return MultiAgentAnalysisResult(
            expert_profiles=[
                {
                    "name": e.profile.name,
                    "profession": e.profile.profession_traits.title,
                    "personality": e.profile.personality_traits.name,
                    "expertise": e.profile.profession_traits.expertise,
                }
                for e in self.experts
            ],
            moderator_name=self.moderator.name,
            rounds=self.rounds_data,
            voting_results=voting_results,
            conclusion=conclusion,
            full_transcript=self.conversation_history,
        )

    def _introduction_phase(self):
        """Phase 1: Moderator introduces the case."""
        expert_names = self._get_expert_names()
        intro = self._collect_stream(
            self.moderator.introduce_case(self.taxpayer_context, expert_names)
        )

        self.conversation_history += f"\n{self.moderator.name}: {intro}\n"

    def _discussion_round(self, round_num: int):
        """Executes one discussion round with all experts."""
        round_data = {"round_number": round_num, "interventions": []}

        other_names = [e.profile.name for e in self.experts]

        for expert in self.experts:
            others = [n for n in other_names if n != expert.profile.name]

            response = self._collect_stream(
                expert.generate_analysis(
                    self.taxpayer_context, self.conversation_history, others
                )
            )

            intervention = f"{expert.profile.name} ({expert.profile.profession_traits.title}): {response}"
            self.conversation_history += f"\n{intervention}\n"

            round_data["interventions"].append(
                {
                    "agent": expert.profile.name,
                    "profession": expert.profile.profession_traits.title,
                    "content": response,
                }
            )

        summary = self._collect_stream(
            self.moderator.summarize_round(round_num, self.conversation_history)
        )
        self.conversation_history += f"\n{self.moderator.name}: {summary}\n"

        round_data["moderator_summary"] = summary
        self.rounds_data.append(round_data)

    def _voting_phase(self) -> Dict[str, Any]:
        """Phase 4: Voting for best strategy."""
        announcement = self._collect_stream(self.moderator.announce_voting())
        self.conversation_history += f"\n{self.moderator.name}: {announcement}\n"

        expert_strategies = [
            f"{e.profile.name}: {e.profile.profession_traits.focus_areas}"
            for e in self.experts
        ]

        votes = []
        vote_details = []

        for expert_index, expert in enumerate(self.experts):
            # Expert votes, excluding themselves
            vote_response = self._collect_stream(
                expert.vote(self.conversation_history, expert_strategies, expert_index)
            )

            try:
                vote_num = int("".join(filter(str.isdigit, vote_response[:10])))

                # Build mapping of available options (excluding self)
                available_indices = [
                    i for i in range(len(self.experts)) if i != expert_index
                ]

                # Validate vote is within valid range (1 or 2 for 3 experts)
                if 1 <= vote_num <= len(available_indices):
                    # Map vote number to actual expert index
                    actual_expert_index = available_indices[vote_num - 1]
                    voted_expert = self.experts[actual_expert_index].profile.name

                    votes.append(voted_expert)
                    vote_details.append(
                        {"voter": expert.profile.name, "voted_for": voted_expert}
                    )
                else:
                    # Invalid vote - default to first available expert (not self)
                    default_expert = self.experts[available_indices[0]].profile.name
                    votes.append(default_expert)
                    vote_details.append(
                        {"voter": expert.profile.name, "voted_for": default_expert}
                    )
            except (ValueError, IndexError):
                # Error parsing vote - default to first available expert (not self)
                available_indices = [
                    i for i in range(len(self.experts)) if i != expert_index
                ]
                default_expert = self.experts[available_indices[0]].profile.name
                votes.append(default_expert)
                vote_details.append(
                    {"voter": expert.profile.name, "voted_for": default_expert}
                )

        vote_counts = Counter(votes)
        winner = (
            vote_counts.most_common(1)[0][0]
            if vote_counts
            else self.experts[0].profile.name
        )

        winning_expert = next(
            (e for e in self.experts if e.profile.name == winner), self.experts[0]
        )

        return {
            "votes": vote_details,
            "vote_counts": dict(vote_counts),
            "winner": winner,
            "winning_strategy": winning_expert.profile.profession_traits.focus_areas,
        }

    def _conclusion_phase(self, voting_results: Dict[str, Any]) -> str:
        """Phase 5: Final conclusion."""
        conclusion = self._collect_stream(
            self.moderator.conclude(
                self.conversation_history,
                voting_results["winning_strategy"],
                voting_results["vote_counts"],
            )
        )

        self.conversation_history += (
            f"\n{self.moderator.name} - CONCLUSIÓN FINAL: {conclusion}\n"
        )
        return conclusion


class MultiAgentAnalysisService:
    """Main service for running multi-agent fiscal analysis."""

    @staticmethod
    def run_analysis(
        calculation_result: Any, user_data: Dict[str, Any], fiscal_year: int
    ) -> MultiAgentAnalysisResult:
        """
        Runs a complete multi-agent analysis session.

        Args:
            calculation_result: Tax calculation result from TaxCalculator
            user_data: User input data
            fiscal_year: Fiscal year for analysis

        Returns:
            Complete analysis result with all rounds, voting, and conclusion
        """
        taxpayer_context = build_taxpayer_context(
            calculation_result, user_data, fiscal_year
        )

        experts = AgentFactory.create_random_experts(count=3)
        moderator = AgentFactory.create_moderator()

        orchestrator = MultiAgentConversationOrchestrator(
            experts=experts, moderator=moderator, taxpayer_context=taxpayer_context
        )

        return orchestrator.run_analysis(total_rounds=3)

    @staticmethod
    def run_analysis_stream(
        calculation_result: Any, user_data: Dict[str, Any], fiscal_year: int
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Runs analysis with streaming output for real-time UI updates.

        Yields:
            Dict with type and content for each phase of the analysis
        """
        taxpayer_context = build_taxpayer_context(
            calculation_result, user_data, fiscal_year
        )

        experts = AgentFactory.create_random_experts(count=3)
        moderator = AgentFactory.create_moderator()

        yield {
            "type": "initialization",
            "experts": [
                {
                    "name": e.profile.name,
                    "profession": e.profile.profession_traits.title,
                    "personality": e.profile.personality_traits.name,
                }
                for e in experts
            ],
        }

        orchestrator = MultiAgentConversationOrchestrator(
            experts=experts, moderator=moderator, taxpayer_context=taxpayer_context
        )

        # Introduction phase
        yield {"type": "phase", "phase": "introduction", "agent": moderator.name}

        expert_names_list = [
            f"{e.profile.name} ({e.profile.profession_traits.title})" for e in experts
        ]

        full_intro = []
        for chunk in moderator.introduce_case(taxpayer_context, expert_names_list):
            full_intro.append(chunk)
            yield {"type": "chunk", "content": chunk}

        intro = "".join(full_intro)
        orchestrator.conversation_history += f"\n{moderator.name}: {intro}\n"
        yield {"type": "intervention_complete"}

        # Three rounds of debate
        for round_num in range(1, 4):
            yield {"type": "phase", "phase": f"round_{round_num}"}

            other_names = [e.profile.name for e in experts]
            for expert in experts:
                # Start new intervention for this expert
                yield {
                    "type": "phase",
                    "phase": f"round_{round_num}",
                    "agent": expert.profile.name,
                }

                others = [n for n in other_names if n != expert.profile.name]

                full_response = []
                for chunk in expert.generate_analysis(
                    taxpayer_context, orchestrator.conversation_history, others
                ):
                    full_response.append(chunk)
                    yield {"type": "chunk", "content": chunk}

                response = "".join(full_response)
                orchestrator.conversation_history += (
                    f"\n{expert.profile.name}: {response}\n"
                )

                yield {"type": "intervention_complete"}

            # Moderator summarizes the round
            yield {
                "type": "phase",
                "phase": f"round_{round_num}_summary",
                "agent": moderator.name,
            }

            full_summary = []
            for chunk in moderator.summarize_round(
                round_num, orchestrator.conversation_history
            ):
                full_summary.append(chunk)
                yield {"type": "chunk", "content": chunk}

            summary = "".join(full_summary)
            orchestrator.conversation_history += f"\n{moderator.name}: {summary}\n"
            yield {"type": "intervention_complete"}

        # Voting phase
        yield {"type": "phase", "phase": "voting", "agent": moderator.name}
        voting_results = orchestrator._voting_phase()

        yield {
            "type": "voting_results",
            "votes": voting_results["vote_counts"],
            "winner": voting_results["winning_strategy"],
        }
        yield {"type": "intervention_complete"}

        # Conclusion phase
        yield {"type": "phase", "phase": "conclusion", "agent": moderator.name}

        full_conclusion = []
        for chunk in moderator.conclude(
            orchestrator.conversation_history,
            voting_results["winning_strategy"],
            voting_results["vote_counts"],
        ):
            full_conclusion.append(chunk)
            yield {"type": "chunk", "content": chunk}

        conclusion = "".join(full_conclusion)
        yield {"type": "intervention_complete"}

        yield {
            "type": "complete",
            "conclusion": conclusion,
            "full_transcript": orchestrator.conversation_history,
        }
