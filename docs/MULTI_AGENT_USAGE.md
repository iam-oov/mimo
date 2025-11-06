# Multi-Agent System - Usage Examples

## Overview

The multi-agent system uses **LiteLLM** for unified model access, allowing each agent to use different AI providers seamlessly. By default, all agents use DeepSeek, but you can easily configure different models.

## Quick Start

### Using Default Configuration (All DeepSeek)

```python
from src.infrastructure.ai_providers.litellm_adapter import create_agent_adapter
from src.infrastructure.ai_providers.prompts import (
    Personality,
    Profession,
    build_agent_system_prompt,
    build_round_prompt,
)

# Create agent 1 adapter (DeepSeek by default)
adapter = create_agent_adapter('agent_1')

# Build agent personality
system_prompt = build_agent_system_prompt(
    personality=Personality.ANALYTICAL,
    profession=Profession.TAX_PLANNER,
    agent_name="Carlos Méndez"
)

# Build round prompt
user_prompt = build_round_prompt(
    round_number=1,
    round_type='initial',
    context="Fiscal context here..."
)

# Generate response (streaming)
for chunk in adapter.generate_stream(system_prompt, user_prompt):
    print(chunk, end='', flush=True)
```

## Configuring Different Models Per Agent

### Option 1: Modify `multi_agent_prompts.py`

Edit the `DEFAULT_AGENT_MODELS` dictionary:

```python
DEFAULT_AGENT_MODELS = {
    "agent_1": AgentModelConfig(
        provider="deepseek",
        model="deepseek-chat",
        temperature=0.7
    ),
    "agent_2": AgentModelConfig(
        provider="openai",
        model="gpt-4-turbo-preview",
        temperature=0.6
    ),
    "agent_3": AgentModelConfig(
        provider="gemini",
        model="gemini-1.5-pro",
        temperature=0.8
    ),
    "moderator": AgentModelConfig(
        provider="anthropic",
        model="claude-3-opus-20240229",
        temperature=0.5,
        max_tokens=800
    ),
}
```

### Option 2: Environment Variables (Future Implementation)

```bash
# Configure models via environment variables
export AGENT_1_PROVIDER=deepseek
export AGENT_1_MODEL=deepseek-chat
export AGENT_1_TEMPERATURE=0.7

export AGENT_2_PROVIDER=openai
export AGENT_2_MODEL=gpt-4-turbo-preview
export AGENT_2_TEMPERATURE=0.6

export AGENT_3_PROVIDER=gemini
export AGENT_3_MODEL=gemini-1.5-pro
export AGENT_3_TEMPERATURE=0.8
```

## Supported Providers

LiteLLM supports 100+ models from different providers:

### DeepSeek

```python
AgentModelConfig(provider="deepseek", model="deepseek-chat")
```

### OpenAI

```python
AgentModelConfig(provider="openai", model="gpt-4-turbo-preview")
AgentModelConfig(provider="openai", model="gpt-3.5-turbo")
```

### Google Gemini

```python
AgentModelConfig(provider="gemini", model="gemini-1.5-pro")
AgentModelConfig(provider="gemini", model="gemini-1.5-flash")
```

### Anthropic Claude

```python
AgentModelConfig(provider="anthropic", model="claude-3-opus-20240229")
AgentModelConfig(provider="anthropic", model="claude-3-sonnet-20240229")
```

### Local Models (Ollama)

```python
AgentModelConfig(provider="ollama", model="llama2")
AgentModelConfig(provider="ollama", model="mistral")
```

## Agent Personalities & Professions

### Personalities

```python
from src.infrastructure.ai_providers.prompts import Personality

Personality.CONSERVATIVE  # Cauteloso y precavido
Personality.AGGRESSIVE    # Audaz y directo
Personality.ANALYTICAL    # Metódico y basado en datos
Personality.PRAGMATIC     # Práctico y equilibrado
Personality.INNOVATIVE    # Creativo y visionario
```

### Professions

```python
from src.infrastructure.ai_providers.prompts import Profession

Profession.AUDITOR               # Auditor Fiscal
Profession.TAX_PLANNER          # Planificador Fiscal
Profession.ACCOUNTANT           # Contador Público
Profession.FINANCIAL_ADVISOR    # Asesor Financiero
Profession.FISCAL_LAWYER        # Abogado Fiscalista
Profession.BUSINESS_CONSULTANT  # Consultor Empresarial
```

## Complete Example: 3-Agent Debate

```python
import random
from src.infrastructure.ai_providers.litellm_adapter import create_agent_adapter
from src.infrastructure.ai_providers.prompts import (
    Personality,
    Profession,
    build_agent_system_prompt,
    build_debate_context,
    build_round_prompt,
)

# Define 3 agents with different personalities
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
        "personality": Personality.PRAGMATIC,
        "profession": Profession.ACCOUNTANT,
    },
    {
        "id": "agent_3",
        "name": "Laura Martínez",
        "personality": Personality.CONSERVATIVE,
        "profession": Profession.AUDITOR,
    },
]

# Create adapters
for agent in agents:
    agent["adapter"] = create_agent_adapter(agent["id"])
    agent["system_prompt"] = build_agent_system_prompt(
        personality=agent["personality"],
        profession=agent["profession"],
        agent_name=agent["name"],
    )

# Build fiscal context
context = build_debate_context(
    calculation_result=tax_calculation,
    user_data=user_data,
    fiscal_year=2024,
    uma_annual=39606.36,
    effective_deduction_limit=180000.00,
)

# Round 1: Initial proposals
print("=== RONDA 1: PROPUESTAS INICIALES ===\n")
round_1_args = []

for agent in agents:
    print(f"\n{agent['name']} ({agent['profession'].value}):")

    prompt = build_round_prompt(
        round_number=1,
        round_type='initial',
        context=context,
    )

    response = ""
    for chunk in agent["adapter"].generate_stream(
        agent["system_prompt"], prompt
    ):
        print(chunk, end='', flush=True)
        response += chunk

    round_1_args.append({
        "agent": agent["name"],
        "content": response,
        "round": 1,
    })
    print()

# Round 2: Responses and debate
print("\n=== RONDA 2: DEBATE Y RESPUESTAS ===\n")
round_2_args = []

for agent in agents:
    print(f"\n{agent['name']} ({agent['profession'].value}):")

    # Get other agents' arguments
    other_args = [arg for arg in round_1_args if arg["agent"] != agent["name"]]

    prompt = build_round_prompt(
        round_number=2,
        round_type='response',
        context=context,
        previous_arguments=other_args,
    )

    response = ""
    for chunk in agent["adapter"].generate_stream(
        agent["system_prompt"], prompt
    ):
        print(chunk, end='', flush=True)
        response += chunk

    round_2_args.append({
        "agent": agent["name"],
        "content": response,
        "round": 2,
    })
    print()

# Round 3: Consensus
print("\n=== RONDA 3: CONSENSO ===\n")
all_args = round_1_args + round_2_args

for agent in agents:
    print(f"\n{agent['name']} ({agent['profession'].value}):")

    prompt = build_round_prompt(
        round_number=3,
        round_type='consensus',
        context=context,
        previous_arguments=all_args,
    )

    for chunk in agent["adapter"].generate_stream(
        agent["system_prompt"], prompt
    ):
        print(chunk, end='', flush=True)

    print()
```

## Environment Variables Required

### DeepSeek (Default)

```bash
export DEEPSEEK_API_KEY=your_deepseek_api_key
```

### OpenAI (Optional)

```bash
export OPENAI_API_KEY=your_openai_api_key
```

### Gemini (Optional)

```bash
export GEMINI_API_KEY=your_gemini_api_key
```

### Anthropic (Optional)

```bash
export ANTHROPIC_API_KEY=your_anthropic_api_key
```

## Benefits of This Architecture

✅ **Flexibility:** Each agent can use a different AI provider  
✅ **Experimentation:** Easy to A/B test different models  
✅ **Cost Optimization:** Use cheaper models for simple agents, premium models for complex ones  
✅ **Fallback Strategy:** If one provider fails, others can continue  
✅ **Future-Proof:** Easy to add new providers supported by LiteLLM  
✅ **Unified Interface:** Same code works across all providers

## Next Steps

1. Install LiteLLM: `uv add litellm`
2. Configure your agents in `multi_agent_prompts.py`
3. Set environment variables for your chosen providers
4. Run the multi-agent analysis!
