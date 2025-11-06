"""
Example: Quick test of multi-agent system with personalized prompts.
This demonstrates how each agent has its own personality and model configuration.
"""

from src.infrastructure.ai_providers.litellm_adapter import create_agent_adapter
from src.infrastructure.ai_providers.prompts import (
    Personality,
    Profession,
    build_agent_system_prompt,
    build_round_prompt,
)


def test_agent_personalities():
    """
    Test that each agent responds with its unique personality.
    """
    print("🧪 Testing Multi-Agent System with Personalized Prompts\n")
    print("=" * 70)

    # Define test agents
    agents = [
        {
            "id": "agent_1",
            "name": "María González",
            "personality": Personality.ANALYTICAL,
            "profession": Profession.TAX_PLANNER,
        },
        {
            "id": "agent_2",
            "name": "Roberto Silva",
            "personality": Personality.AGGRESSIVE,
            "profession": Profession.FINANCIAL_ADVISOR,
        },
        {
            "id": "agent_3",
            "name": "Laura Martínez",
            "personality": Personality.CONSERVATIVE,
            "profession": Profession.AUDITOR,
        },
    ]

    # Simple fiscal context for testing
    context = """CONTEXTO FISCAL 2024:

Ingresos: $150,000
ISR determinado: $20,000
ISR retenido: $18,000
Balance: $2,000 (a pagar)

Deducciones actuales: $50,000
Espacio disponible: $72,500
Límite efectivo: $122,500"""

    # Test Round 1: Each agent gives initial proposal
    print("\n🎯 RONDA 1: Propuestas Iniciales\n")

    for agent in agents:
        print(f"\n{'=' * 70}")
        print(f"👤 {agent['name']}")
        print(
            f"   {agent['profession'].value} - Personalidad {agent['personality'].value}"
        )
        print(f"{'=' * 70}\n")

        # Create adapter
        adapter = create_agent_adapter(agent["id"])

        if not adapter:
            print(f"❌ No se pudo crear adaptador para {agent['name']}")
            continue

        # Build system prompt (defines personality)
        system_prompt = build_agent_system_prompt(
            personality=agent["personality"],
            profession=agent["profession"],
            agent_name=agent["name"],
        )

        # Build round prompt
        user_prompt = build_round_prompt(
            round_number=1,
            round_type="initial",
            context=context,
        )

        # Generate response (streaming)
        print("💬 Respuesta: ", end="", flush=True)
        try:
            for chunk in adapter.generate_stream(system_prompt, user_prompt):
                print(chunk, end="", flush=True)
            print("\n")
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

    print("\n" + "=" * 70)
    print("✅ Test completado!")
    print("\nNota: Observa cómo cada agente responde de acuerdo a su personalidad:")
    print("  - María (Analítica): Usa números y análisis cuantitativo")
    print("  - Roberto (Agresivo): Busca maximizar oportunidades")
    print("  - Laura (Conservadora): Enfatiza riesgos y cumplimiento")


if __name__ == "__main__":
    test_agent_personalities()
