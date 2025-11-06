# 🎯 Sistema Multi-Agente con Prompts Personalizados

## ✅ Implementación Completada

He creado un sistema flexible de multi-agentes donde **cada agente tiene su propio prompt y puede usar diferentes modelos de IA**.

## 📁 Archivos Creados

### 1. `src/infrastructure/ai_providers/multi_agent_prompts.py` (370 líneas)

**Funcionalidad:**

- ✅ **Enums de Personalidades**: Conservative, Aggressive, Analytical, Pragmatic, Innovative
- ✅ **Enums de Profesiones**: Auditor, Tax Planner, Accountant, Financial Advisor, Fiscal Lawyer, Business Consultant
- ✅ **Estilos de Personalidad**: Cada personalidad tiene tono, enfoque, estilo y frases características
- ✅ **Focus por Profesión**: Cada profesión tiene expertise, áreas de enfoque y prioridades específicas
- ✅ **`build_agent_system_prompt()`**: Genera prompt de sistema único para cada agente combinando personalidad + profesión
- ✅ **`build_debate_context()`**: Genera contexto fiscal compartido por todos los agentes
- ✅ **`build_round_prompt()`**: Genera prompts específicos por ronda (inicial, respuesta, consenso)
- ✅ **`build_synthesis_prompt()`**: Genera prompt para síntesis final del moderador
- ✅ **`AgentModelConfig`**: Clase para configurar modelo por agente (provider, model, temperature, max_tokens)
- ✅ **`DEFAULT_AGENT_MODELS`**: Configuración por defecto (todos usan DeepSeek actualmente)
- ✅ **`get_agent_model_config()`**: Obtiene configuración de modelo por agent_id

### 2. `src/infrastructure/ai_providers/litellm_adapter.py` (220 líneas)

**Funcionalidad:**

- ✅ **`LiteLLMAdapter`**: Adaptador unificado para múltiples proveedores AI
- ✅ **`generate_stream()`**: Generación con streaming
- ✅ **`generate()`**: Generación completa (no streaming)
- ✅ **`is_available()`**: Verifica si el proveedor está disponible
- ✅ **`get_model_info()`**: Info legible del modelo
- ✅ **`create_agent_adapter()`**: Factory function para crear adaptadores por agente
- ✅ **Soporte para múltiples proveedores**: DeepSeek, OpenAI, Gemini, Anthropic, Ollama (local), y 100+ más vía LiteLLM

### 3. `docs/MULTI_AGENT_USAGE.md`

**Documentación completa con:**

- ✅ Quick start con ejemplos de código
- ✅ Cómo configurar diferentes modelos por agente
- ✅ Lista de proveedores soportados
- ✅ Ejemplo completo de debate de 3 agentes
- ✅ Variables de entorno requeridas
- ✅ Beneficios de la arquitectura

### 4. `examples/test_multi_agent.py`

**Script de prueba que:**

- ✅ Crea 3 agentes con personalidades diferentes
- ✅ Ejecuta Ronda 1 con cada agente
- ✅ Demuestra cómo cada agente responde según su personalidad
- ✅ Listo para ejecutar y probar

### 5. `pyproject.toml`

- ✅ Agregado `litellm>=1.50.0` a las dependencias

### 6. `src/infrastructure/ai_providers/prompts.py`

- ✅ Re-exporta todas las funciones de multi-agente para conveniencia
- ✅ Import centralizado desde un solo lugar

## 🎨 Características Principales

### 1. **Prompts Personalizados por Agente**

Cada agente tiene su propio system prompt que combina:

- **Personalidad** (ej: Analítico = metódico, basado en datos)
- **Profesión** (ej: Tax Planner = optimización fiscal, deducciones)
- **Estilo de comunicación** (frases características, tono específico)

### 2. **Modelos Configurables**

```python
# Actualmente todos usan DeepSeek
"agent_1": AgentModelConfig(provider="deepseek", model="deepseek-chat", temperature=0.7)
"agent_2": AgentModelConfig(provider="deepseek", model="deepseek-chat", temperature=0.7)
"agent_3": AgentModelConfig(provider="deepseek", model="deepseek-chat", temperature=0.7)

# Futuro: Mezclar proveedores
"agent_1": AgentModelConfig(provider="deepseek", model="deepseek-chat")
"agent_2": AgentModelConfig(provider="openai", model="gpt-4-turbo")
"agent_3": AgentModelConfig(provider="gemini", model="gemini-1.5-pro")
```

### 3. **Prompts por Ronda**

- **Ronda 1 (Initial)**: Cada agente propone su estrategia principal
- **Ronda 2 (Response)**: Agentes responden a propuestas de otros
- **Ronda 3 (Consensus)**: Agentes priorizan y votan por estrategias
- **Síntesis**: Moderador genera conclusión final

### 4. **Flexibilidad Total**

```python
# Cambiar modelo de un agente es tan fácil como:
DEFAULT_AGENT_MODELS["agent_1"] = AgentModelConfig(
    provider="openai",
    model="gpt-4-turbo-preview",
    temperature=0.6,
    max_tokens=400
)
```

## 🚀 Cómo Usar

### Opción 1: Usar el Script de Prueba

```bash
cd /Users/valdo/Personal/Repos/Python/mimo
uv run python examples/test_multi_agent.py
```

### Opción 2: Código Personalizado

```python
from src.infrastructure.ai_providers.litellm_adapter import create_agent_adapter
from src.infrastructure.ai_providers.prompts import (
    Personality,
    Profession,
    build_agent_system_prompt,
    build_round_prompt,
)

# Crear adaptador para agente 1
adapter = create_agent_adapter('agent_1')

# Definir personalidad del agente
system_prompt = build_agent_system_prompt(
    personality=Personality.ANALYTICAL,
    profession=Profession.TAX_PLANNER,
    agent_name="María González"
)

# Crear prompt de ronda
user_prompt = build_round_prompt(
    round_number=1,
    round_type='initial',
    context="CONTEXTO FISCAL..."
)

# Generar respuesta (streaming)
for chunk in adapter.generate_stream(system_prompt, user_prompt):
    print(chunk, end='', flush=True)
```

## 🔧 Configuración de Modelos

### Para cambiar modelos, edita `multi_agent_prompts.py`:

```python
DEFAULT_AGENT_MODELS = {
    "agent_1": AgentModelConfig(
        provider="deepseek",      # o "openai", "gemini", "anthropic"
        model="deepseek-chat",    # nombre del modelo
        temperature=0.7,          # creatividad (0.0-1.0)
        max_tokens=300           # longitud máxima de respuesta
    ),
    # ... más agentes
}
```

### Proveedores Soportados (vía LiteLLM):

- ✅ **DeepSeek** (default, más económico)
- ✅ **OpenAI** (GPT-4, GPT-3.5-turbo)
- ✅ **Google Gemini** (gemini-pro, gemini-1.5-flash)
- ✅ **Anthropic** (Claude 3 Opus, Sonnet, Haiku)
- ✅ **Ollama** (modelos locales: llama2, mistral, etc.)
- ✅ **100+ más** vía LiteLLM

## 📊 Ejemplo de Salida

```
🎯 RONDA 1: Propuestas Iniciales

👤 María González (Analítico - Planificador Fiscal)
💬 Según el análisis, tienes $72,500 de espacio para deducir.
Matemáticamente, podrías reducir tu ISR hasta $10,875 aprovechando
el 15% de tasa marginal. Recomiendo PPR + colegiaturas.

👤 Roberto Silva (Agresivo - Asesor Financiero)
💬 ¡Gran oportunidad! Deberíamos aprovechar TODO el espacio disponible.
PPR te da doble beneficio: deducción fiscal HOY y retiro futuro.
No dejemos pasar $72,500 en deducciones.

👤 Laura Martínez (Conservadora - Auditora Fiscal)
💬 Es importante considerar que toda deducción debe tener soporte fiscal.
Para evitar riesgos, asegúrate de tener facturas correctas y pagos
bancarizados. La normativa SAT es estricta en auditorías.
```

## 🎯 Próximos Pasos

1. ✅ **Ya está todo implementado y listo para usar**
2. 🔄 **Probar el sistema**: Ejecuta `examples/test_multi_agent.py`
3. 🎨 **Personalizar agentes**: Modifica personalidades/profesiones en tu código
4. 🔧 **Experimentar con modelos**: Cambia proveedores en `DEFAULT_AGENT_MODELS`
5. 🌐 **Variables de entorno** (futuro): Implementar override vía env vars

## 💡 Ventajas de Esta Arquitectura

✅ **Reutilizable**: Prompts en archivo separado, fácil de copiar a otros proyectos  
✅ **Flexible**: Cada agente usa el modelo que quieras  
✅ **Mantenible**: Cambios en prompts no afectan la lógica de negocio  
✅ **Testeable**: Puedes probar prompts sin ejecutar toda la app  
✅ **Escalable**: Agregar nuevos agentes es trivial  
✅ **Económico**: Usa modelos baratos para agentes simples, caros para complejos  
✅ **Experimentable**: A/B test entre diferentes modelos fácilmente

## 📚 Archivos de Referencia

- **Prompts Multi-Agente**: `src/infrastructure/ai_providers/multi_agent_prompts.py`
- **Adaptador LiteLLM**: `src/infrastructure/ai_providers/litellm_adapter.py`
- **Documentación**: `docs/MULTI_AGENT_USAGE.md`
- **Ejemplo de Uso**: `examples/test_multi_agent.py`
- **Re-exports**: `src/infrastructure/ai_providers/prompts.py`

---

🐱 **Mimo dice:** ¡Miau-ravilloso! Ahora cada experto tiene su propia personalidad y puede usar el modelo que más le guste. ¡Purr-fecto para debates fiscales! 🎉
