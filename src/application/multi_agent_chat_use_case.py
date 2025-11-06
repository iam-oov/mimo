"""
Multi-agent chat use case.
Interactive chat where user selects which agent responds.
"""

from dataclasses import dataclass
from typing import Dict, Any, Generator, Optional
from datetime import date

from src.domain.ports.repositories import UsageRepository
from src.domain.ports.memory import MemoryStore
from src.infrastructure.ai_providers.litellm_adapter import create_agent_adapter
from src.infrastructure.ai_providers.multi_agent_prompts import (
    Personality,
    Profession,
    build_debate_context,
)
from tabla_isr_constants import get_tabla_isr


@dataclass
class AgentChatRequest:
    """Request for agent chat response."""

    agent_id: str  # 'agent_1', 'agent_2', or 'agent_3'
    user_message: str
    calculation_result: Dict[str, Any]
    user_data: Dict[str, Any]
    fiscal_year: int
    conversation_history: Optional[list[Dict[str, str]]] = None  # Optional chat history


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

    def get_usage_info(self, user_id: str) -> Dict[str, int]:
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
        calculation_result: Dict[str, Any],
        user_data: Dict[str, Any],
        fiscal_year: int,
        user_id: str | None = None,
    ) -> list[AgentInfo]:
        """
        Get list of available agents with their profiles.
        Generates 3 random agents with different personalities/professions.
        """
        import random
        from src.infrastructure.ai_providers.multi_agent_prompts import (
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

            agents.append(
                AgentInfo(
                    agent_id=agent_id,
                    name=agent_names[i],
                    personality=personality.value,
                    profession=profession.value,
                    expertise=expertise,
                )
            )

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
        # Get agent configuration
        adapter = create_agent_adapter(request.agent_id)

        if not adapter:
            raise ValueError(f"No adapter available for agent {request.agent_id}")

        # Build fiscal context
        tabla_isr = get_tabla_isr(request.fiscal_year)
        uma_annual = tabla_isr.constantes.valor_uma_anual
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

        # Get agent's personality and profession (from agent_id)
        # This assumes agent_id format is 'agent_1', 'agent_2', etc.
        # We need to retrieve the stored agent info (personality/profession)
        # For now, we'll use the model config defaults
        # TODO: Store agent sessions to maintain consistency

        # Build conversation history context
        history_context = ""
        if request.conversation_history:
            history_context = "\n\nCONVERSACIÓN PREVIA:\n"
            for msg in request.conversation_history[-5:]:  # Last 5 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    history_context += f"Usuario: {content}\n"
                else:
                    history_context += f"Agente: {content}\n"

        # Build system prompt (we need personality/profession)
        # For simplicity, using default Conservative/Auditor
        # In production, store agent selection in session
        system_prompt = f"""Eres un experto fiscal mexicano especializado en ISR para personas físicas.

Tu tarea es responder preguntas del usuario sobre su situación fiscal de manera clara y práctica.

{context}
{memory_context}
{history_context}

INSTRUCCIONES:
- Responde de manera directa y útil
- Usa un lenguaje simple, evita tecnicismos innecesarios
- Si el usuario pregunta sobre deducciones, menciona límites y requisitos
- Si pregunta sobre estrategias, sé específico con montos y plazos
- Máximo 250 caracteres por respuesta
- Usa emojis ocasionalmente para hacer la respuesta más amigable
"""

        # Build user prompt
        user_prompt = f"Pregunta del usuario: {request.user_message}\n\nResponde de manera concisa y práctica."

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
        calculation_result: Dict[str, Any],
        user_data: Dict[str, Any],
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
