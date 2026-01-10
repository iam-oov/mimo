"""
Multi-agent chat use case.
Interactive chat where user selects which agent responds.
"""

from collections.abc import Generator
from dataclasses import dataclass
from datetime import date
from typing import Any

from src.multi_agent.domain.ports.memory import MemoryStore
from src.multi_agent.infrastructure.litellm.adapter import create_agent_adapter
from src.multi_agent.infrastructure.prompts.multi_agent_prompts import (
    Personality,
    Profession,
    build_debate_context,
)
from src.shared.domain.constants.isr_tables import get_isr_table
from src.shared.domain.ports.repositories import UsageRepository
from src.shared.infrastructure.logging.structured_logger import StructuredLogger

logger = StructuredLogger(__name__)


@dataclass
class AgentChatRequest:
    """Request for agent chat response."""

    agent_id: str  # 'agent_1', 'agent_2', or 'agent_3'
    user_message: str
    calculation_result: dict[str, Any]
    user_data: dict[str, Any]
    fiscal_year: int
    conversation_history: list[dict[str, str]] | None = None  # Optional chat history


@dataclass
class AgentInfo:
    """Agent information."""

    agent_id: str
    name: str
    personality: str
    profession: str
    expertise: str


class MultiAgentChatUseCase:
    """
    Use case for interactive multi-agent chat.
    User asks questions and selects which agent responds.
    """

    def __init__(
        self,
        usage_repository: UsageRepository,
        daily_limit: int = 3,
        memory_store: MemoryStore | None = None,
    ):
        self.usage_repository = usage_repository
        self._daily_limit = daily_limit
        self._memory = memory_store
        self._agent_sessions: dict[
            str, AgentInfo
        ] = {}  # Store agent info by user_id + agent_id

    def get_usage_info(self, user_id: str) -> dict[str, int]:
        """Get current usage information for user."""
        today = date.today()
        usage_count = self.usage_repository.get_usage_count(user_id, today)

        return {
            "usage_count": usage_count,
            "remaining_usage": max(0, self._daily_limit - usage_count),
            "daily_limit": self._daily_limit,
        }

    def can_generate(self, user_id: str) -> bool:
        """Check if user can generate a chat response."""
        today = date.today()
        usage_count = self.usage_repository.get_usage_count(user_id, today)
        return usage_count < self._daily_limit

    def get_available_agents(
        self,
        calculation_result: dict[str, Any],
        user_data: dict[str, Any],
        fiscal_year: int,
        user_id: str | None = None,
    ) -> list[AgentInfo]:
        """
        Get list of available agents with their profiles.
        Generates 3 random agents with different personalities/professions.
        """
        import random

        from src.multi_agent.infrastructure.prompts.multi_agent_prompts import (
            PROFESSION_FOCUS,
        )

        # Generate 3 unique agents
        personalities = list(Personality)
        professions = list(Profession)

        # Shuffle for randomness
        random.shuffle(personalities)
        random.shuffle(professions)

        agent_names = [
            "Carlos Méndez",
            "Ana Torres",
            "Roberto Silva",
            "María González",
            "Jorge Ramírez",
            "Laura Martínez",
        ]
        random.shuffle(agent_names)

        agents = []
        for i in range(3):
            agent_id = f"agent_{i + 1}"
            personality = personalities[i]
            profession = professions[i]
            expertise = PROFESSION_FOCUS[profession]["expertise"]

            agent_info = AgentInfo(
                agent_id=agent_id,
                name=agent_names[i],
                personality=personality.value,
                profession=profession.value,
                expertise=expertise,
            )
            agents.append(agent_info)

            # Store agent info in session for later use
            if user_id:
                session_key = f"{user_id}_{agent_id}"
                self._agent_sessions[session_key] = agent_info

        # Seed memory with calculation context so agents can recall it later
        try:
            if self._memory is not None:
                summary = self._build_calculation_summary(
                    calculation_result, user_data, fiscal_year
                )
                target_user = (
                    user_id or user_data.get("user_id", "anonymous")
                    if isinstance(user_data, dict)
                    else (user_id or "anonymous")
                )
                self._memory.add_memory(
                    user_id=target_user,
                    text=summary,
                    metadata={
                        "type": "calculation_context",
                        "fiscal_year": fiscal_year,
                    },
                )
        except Exception:
            # Memory is best-effort; do not break on failures
            pass

        return agents

    def generate_response_stream(
        self, request: AgentChatRequest, user_id: str
    ) -> Generator[str, None, None]:
        """
        Generate streaming response from selected agent.

        Yields:
            Content chunks from the AI response
        """
        logger.info(
            "📝 Chat request received",
            agent_id=request.agent_id,
            user_id=user_id,
            message_preview=request.user_message[:50] if request.user_message else "",
        )

        # Get agent configuration
        adapter = create_agent_adapter(request.agent_id)

        if not adapter:
            logger.error(
                "❌ Cannot create adapter for agent - check API key configuration",
                agent_id=request.agent_id,
                user_id=user_id,
            )
            raise ValueError(
                f"No hay un proveedor de IA disponible para el agente {request.agent_id}. "
                "Verifica que las API keys estén configuradas correctamente."
            )

        # Build fiscal context
        isr_table = get_isr_table(request.fiscal_year)
        uma_annual = isr_table.constants.annual_uma_value
        general_deduction_limit = 5 * uma_annual

        gross_income = request.calculation_result.get("gross_annual_income", 0)

        total_deduction_limit_15_percent = gross_income * 0.15
        effective_deduction_limit = min(
            general_deduction_limit, total_deduction_limit_15_percent
        )

        context = build_debate_context(
            calculation_result=request.calculation_result,
            user_data=request.user_data,
            fiscal_year=request.fiscal_year,
            uma_annual=uma_annual,
            effective_deduction_limit=effective_deduction_limit,
        )

        # Retrieve relevant memories and include as context
        memory_context = ""
        if self._memory is not None:
            try:
                memories = self._memory.search(
                    user_id=user_id, query=request.user_message, k=5
                )
                if memories:
                    memory_context = (
                        "\n\nMEMORIA RELEVANTE (de este usuario):\n"
                        + "\n".join([f"- {m['text']}" for m in memories[:5]])
                    )
            except Exception:
                pass

        # Get agent info from session
        session_key = f"{user_id}_{request.agent_id}"
        agent_info = self._agent_sessions.get(session_key)

        agent_name = agent_info.name if agent_info else "Experto Fiscal"
        agent_profession = agent_info.profession if agent_info else "Contador Público"

        # Build conversation history context
        history_context = ""
        is_first_message = (
            not request.conversation_history or len(request.conversation_history) == 0
        )

        if request.conversation_history:
            history_context = "\n\nCONVERSACIÓN PREVIA:\n"
            for msg in request.conversation_history[-5:]:  # Last 5 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    history_context += f"Usuario: {content}\n"
                else:
                    history_context += f"Agente: {content}\n"

        # Build system prompt with agent-specific info
        system_prompt = f"""Eres {agent_name}, un {agent_profession} mexicano especializado en ISR para personas físicas.

CONTEXTO FISCAL DEL USUARIO:
{context}
{memory_context}
{history_context}

COMPORTAMIENTO REQUERIDO:
1. SIEMPRE responde tomando en cuenta los datos fiscales del usuario mostrados arriba
2. Cuando menciones cifras, usa los datos reales del usuario (ingresos, deducciones, saldo a favor, etc.)
3. Si el usuario pregunta algo genérico, personaliza tu respuesta con sus datos específicos
4. NO inventes datos - solo usa la información proporcionada en el CONTEXTO FISCAL

{"INSTRUCCIÓN ESPECIAL - PRIMER MENSAJE:" if is_first_message else ""}
{"Si esta es tu primera respuesta, inicia confirmando brevemente los datos clave del usuario (ingreso mensual, saldo a favor/a pagar) y pregunta cómo puedes ayudarle. Ejemplo: '¡Hola! Veo que tienes ingresos de $X al mes y un saldo a favor de $Y. ¿En qué puedo ayudarte hoy? 💰'" if is_first_message else ""}

INSTRUCCIONES DE RESPUESTA:
- Responde de manera directa y útil
- Usa un lenguaje simple, evita tecnicismos innecesarios
- Siempre referencia los datos del usuario cuando sea relevante
- Usa emojis ocasionalmente para hacer la respuesta más amigable

LONGITUD DINÁMICA DE RESPUESTAS:
- Para preguntas simples, saludos, o temas no relacionados con su situación fiscal: Responde de forma BREVE (100-150 caracteres)
- Para preguntas sobre su situación fiscal, estrategias, deducciones, o cuando el usuario muestre interés en profundizar: Responde de forma DETALLADA (300-600 caracteres)
- Si el usuario pide ejemplos, planes, o pasos específicos: Da una respuesta COMPLETA con puntos numerados o detalles concretos
- Si el usuario pregunta "¿por qué?", "¿cómo?", "cuéntame más" o similares: Expande tu respuesta con detalles relevantes

EJEMPLOS DE LONGITUD APROPIADA:
- "hola" → BREVE: "¡Hola! ¿En qué puedo ayudarte con tu situación fiscal? 👋"
- "gracias" → BREVE: "¡Con gusto! ¿Algo más en lo que pueda ayudarte? 😊"
- "¿cómo maximizar deducciones?" → DETALLADA: Explica opciones específicas con montos basados en SUS datos
- "dame un plan para reducir ISR" → COMPLETA: Lista de pasos numerados con cifras concretas de su situación
"""

        # Build user prompt
        if is_first_message:
            user_prompt = "El usuario acaba de seleccionarte. Inicia la conversación confirmando sus datos fiscales y preguntando cómo puedes ayudarle."
        else:
            user_prompt = f"Pregunta del usuario: {request.user_message}\n\nResponde de manera concisa y práctica, usando sus datos fiscales."

        # Stream response while buffering to store in memory afterwards
        full_response_chunks: list[str] = []
        for chunk in adapter.generate_stream(system_prompt, user_prompt):
            full_response_chunks.append(chunk)
            yield chunk

        # Increment usage after successful generation
        today = date.today()
        self.usage_repository.increment_usage(user_id, today)

        # Store user question and agent answer into memory
        try:
            if self._memory is not None:
                answer_text = "".join(full_response_chunks).strip()
                if answer_text:
                    self._memory.add_memory(
                        user_id=user_id,
                        text=f"Pregunta: {request.user_message}",
                        metadata={"type": "question"},
                    )
                    self._memory.add_memory(
                        user_id=user_id,
                        text=f"Respuesta: {answer_text}",
                        metadata={"type": "answer"},
                    )
        except Exception:
            pass

    def _build_calculation_summary(
        self,
        calculation_result: dict[str, Any],
        user_data: dict[str, Any],
        fiscal_year: int,
    ) -> str:
        """Create a concise, retrieval-friendly summary of the user's calculation context."""
        # Extract safe values
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

        deduction_data = (
            user_data.get("deduction_data", {}) if isinstance(user_data, dict) else {}
        )
        general_deductions = deduction_data.get("general_deductions", 0)
        ppr_deductions = deduction_data.get("ppr_deductions", 0)
        education_deductions = deduction_data.get("education_deductions", 0)

        summary = (
            f"Resumen fiscal {fiscal_year}: ingreso anual ${gross_income:,.0f}; "
            f"ISR determinado ${determined_tax:,.0f}; retenido ${withheld_tax:,.0f}; "
            f"balance {'a favor' if balance_in_favor > 0 else 'a pagar'} ${abs(balance_in_favor):,.0f}; "
            f"deducciones: generales ${general_deductions:,.0f}, PPR ${ppr_deductions:,.0f}, educación ${education_deductions:,.0f}."
        )
        return summary
