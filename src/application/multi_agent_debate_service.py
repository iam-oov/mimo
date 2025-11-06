"""
Multi-agent debate service using new architecture.
Implements fiscal expert debate using LiteLLM and personality-based prompts.
"""

import random
import logging
from typing import Dict, Any, Generator, List
from dataclasses import dataclass

from src.infrastructure.ai_providers.litellm_adapter import create_agent_adapter
from src.infrastructure.ai_providers.prompts import (
    Personality,
    Profession,
    build_agent_system_prompt,
    build_debate_context,
    build_round_prompt,
    build_synthesis_prompt,
)
from tabla_isr_constants import get_tabla_isr

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for a debate agent."""

    agent_id: str
    name: str
    personality: Personality
    profession: Profession


@dataclass
class DebateRound:
    """Data for a single debate round."""

    round_number: int
    round_type: str  # 'initial', 'response', 'consensus'
    arguments: List[Dict[str, Any]]


class MultiAgentDebateService:
    """
    Service for orchestrating multi-agent fiscal debates.
    Uses personality-based prompts and LiteLLM for model routing.
    """

    def __init__(self):
        # Pool of personalities and professions for randomization
        self.personalities = list(Personality)
        self.professions = list(Profession)

        # Agent names pool (Mexican names)
        self.names = [
            "María González",
            "Roberto Silva",
            "Laura Martínez",
            "Carlos Méndez",
            "Ana Torres",
            "Jorge Ramírez",
        ]

    def _create_agents(self, num_agents: int = 3) -> List[AgentConfig]:
        """
        Create debate agents with randomized personalities and professions.

        Args:
            num_agents: Number of agents to create (default: 3)

        Returns:
            List of AgentConfig objects
        """
        # Shuffle and select unique combinations
        personalities = random.sample(self.personalities, num_agents)
        professions = random.sample(self.professions, num_agents)
        names = random.sample(self.names, num_agents)

        agents = []
        for i, (name, personality, profession) in enumerate(
            zip(names, personalities, professions)
        ):
            agents.append(
                AgentConfig(
                    agent_id=f"agent_{i + 1}",
                    name=name,
                    personality=personality,
                    profession=profession,
                )
            )

        return agents

    def run_analysis_stream(
        self,
        calculation_result: Any,
        user_data: Dict[str, Any],
        fiscal_year: int,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Run multi-agent analysis with streaming output.

        Args:
            calculation_result: Tax calculation entity
            user_data: User's input data
            fiscal_year: Fiscal year

        Yields:
            Stream events with type and content
        """
        # Create agents
        agents = self._create_agents(3)

        # Build fiscal context
        tabla_isr = get_tabla_isr(fiscal_year)
        uma_annual = tabla_isr.constantes.valor_uma_anual
        general_deduction_limit = 5 * uma_annual

        # Handle calculation_result as dict or object
        if isinstance(calculation_result, dict):
            gross_income = calculation_result.get("gross_annual_income", 0)
        else:
            gross_income = getattr(calculation_result, "gross_annual_income", 0)

        total_deduction_limit_15_percent = gross_income * 0.15
        effective_deduction_limit = min(
            general_deduction_limit, total_deduction_limit_15_percent
        )

        # build_debate_context now handles both dict and object formats
        context = build_debate_context(
            calculation_result=calculation_result,
            user_data=user_data,
            fiscal_year=fiscal_year,
            uma_annual=uma_annual,
            effective_deduction_limit=effective_deduction_limit,
        )

        # Yield agent introductions with expertise
        from src.infrastructure.ai_providers.multi_agent_prompts import PROFESSION_FOCUS

        yield {
            "type": "agent_intro",
            "agents": [
                {
                    "name": agent.name,
                    "personality": agent.personality.value,
                    "profession": agent.profession.value,
                    "expertise": PROFESSION_FOCUS[agent.profession]["expertise"],
                }
                for agent in agents
            ],
        }

        # Store all arguments for synthesis
        all_arguments = []

        # Round 1: Initial proposals
        yield {
            "type": "round_start",
            "round_number": 1,
            "round_name": "Propuestas Iniciales",
        }

        round_1_args = []
        for agent in agents:
            # Create adapter for this agent
            adapter = create_agent_adapter(agent.agent_id)
            if not adapter:
                logger.warning(f"No adapter available for {agent.name}")
                continue

            # Build system prompt
            system_prompt = build_agent_system_prompt(
                personality=agent.personality,
                profession=agent.profession,
                agent_name=agent.name,
            )

            # Build round prompt
            user_prompt = build_round_prompt(
                round_number=1, round_type="initial", context=context
            )

            # Stream agent response
            yield {
                "type": "agent_turn",
                "agent_name": agent.name,
                "agent_profession": agent.profession.value,
                "round": 1,
            }

            response_text = ""
            try:
                for chunk in adapter.generate_stream(system_prompt, user_prompt):
                    response_text += chunk
                    yield {"type": "agent_chunk", "content": chunk}
            except Exception as e:
                logger.error(f"Error generating response for {agent.name}: {e}")
                response_text = "Error generando respuesta."

            yield {"type": "agent_complete"}

            round_1_args.append(
                {"agent": agent.name, "content": response_text, "round": 1}
            )

        all_arguments.extend(round_1_args)

        # Round 2: Responses and debate
        yield {
            "type": "round_start",
            "round_number": 2,
            "round_name": "Debate y Respuestas",
        }

        round_2_args = []
        for agent in agents:
            adapter = create_agent_adapter(agent.agent_id)
            if not adapter:
                continue

            # Get other agents' arguments
            other_args = [arg for arg in round_1_args if arg["agent"] != agent.name]

            system_prompt = build_agent_system_prompt(
                personality=agent.personality,
                profession=agent.profession,
                agent_name=agent.name,
            )

            user_prompt = build_round_prompt(
                round_number=2,
                round_type="response",
                context=context,
                previous_arguments=other_args,
            )

            yield {
                "type": "agent_turn",
                "agent_name": agent.name,
                "agent_profession": agent.profession.value,
                "round": 2,
            }

            response_text = ""
            try:
                for chunk in adapter.generate_stream(system_prompt, user_prompt):
                    response_text += chunk
                    yield {"type": "agent_chunk", "content": chunk}
            except Exception as e:
                logger.error(f"Error generating response for {agent.name}: {e}")
                response_text = "Error generando respuesta."

            yield {"type": "agent_complete"}

            round_2_args.append(
                {"agent": agent.name, "content": response_text, "round": 2}
            )

        all_arguments.extend(round_2_args)

        # Round 3: Consensus
        yield {
            "type": "round_start",
            "round_number": 3,
            "round_name": "Consenso y Priorización",
        }

        for agent in agents:
            adapter = create_agent_adapter(agent.agent_id)
            if not adapter:
                continue

            system_prompt = build_agent_system_prompt(
                personality=agent.personality,
                profession=agent.profession,
                agent_name=agent.name,
            )

            user_prompt = build_round_prompt(
                round_number=3,
                round_type="consensus",
                context=context,
                previous_arguments=all_arguments,
            )

            yield {
                "type": "agent_turn",
                "agent_name": agent.name,
                "agent_profession": agent.profession.value,
                "round": 3,
            }

            response_text = ""
            try:
                for chunk in adapter.generate_stream(system_prompt, user_prompt):
                    response_text += chunk
                    yield {"type": "agent_chunk", "content": chunk}
            except Exception as e:
                logger.error(f"Error generating response for {agent.name}: {e}")
                response_text = "Error generando respuesta."

            yield {"type": "agent_complete"}

            all_arguments.append(
                {"agent": agent.name, "content": response_text, "round": 3}
            )

        # Final synthesis
        yield {"type": "synthesis_start"}

        # Use moderator agent for synthesis
        moderator_adapter = create_agent_adapter("moderator")
        if moderator_adapter:
            synthesis_prompt = build_synthesis_prompt(
                all_arguments=all_arguments, context=context
            )

            moderator_system = "Eres un moderador experto en fiscalidad mexicana. Tu tarea es sintetizar el debate de expertos y generar conclusiones accionables."

            synthesis_text = ""
            try:
                for chunk in moderator_adapter.generate_stream(
                    moderator_system, synthesis_prompt
                ):
                    synthesis_text += chunk
                    yield {"type": "synthesis_chunk", "content": chunk}
            except Exception as e:
                logger.error(f"Error generating synthesis: {e}")
                synthesis_text = "Error generando síntesis."

            yield {"type": "synthesis_complete", "full_text": synthesis_text}

        # Complete event
        yield {"type": "complete"}
