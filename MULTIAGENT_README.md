# 🐱 Sistema Multi-Agente de Análisis Fiscal

## Descripción General

Sistema de análisis fiscal multi-agente que simula una mesa de discusión con 3 expertos fiscales de diferentes personalidades y profesiones, más un moderador. Los expertos debaten durante 3 rondas cómo optimizar la situación fiscal del contribuyente, luego votan por la mejor estrategia y entregan una conclusión final.

## 🏗️ Arquitectura

### Componentes Principales

```
multi_agent_analysis.py (838 líneas)
├── Enums & Configurations
│   ├── Personality (6 tipos)
│   ├── Profession (6 tipos)
│   ├── PERSONALITY_CONFIGS
│   └── PROFESSION_CONFIGS
│
├── LLM Providers (Strategy Pattern)
│   ├── LanguageModelProvider (Abstract)
│   ├── DeepSeekProvider
│   ├── GeminiProvider
│   └── ModelProviderFactory
│
├── Agents
│   ├── FiscalExpertAgent
│   ├── ModeratorAgent
│   └── AgentFactory
│
├── Orchestration
│   └── MultiAgentConversationOrchestrator
│
└── Service Layer
    └── MultiAgentAnalysisService
```

### Principios SOLID Aplicados

1. **Single Responsibility**
   - `FiscalExpertAgent`: Solo genera análisis desde su perspectiva
   - `ModeratorAgent`: Solo modera y sintetiza
   - `AgentFactory`: Solo crea agentes con perfiles aleatorios

2. **Open/Closed**
   - Nuevas personalidades/profesiones se agregan al enum sin modificar código existente
   - Nuevos proveedores LLM implementan `LanguageModelProvider` interface

3. **Liskov Substitution**
   - Todos los `LanguageModelProvider` son intercambiables
   - DeepSeek y Gemini pueden sustituirse sin afectar la lógica

4. **Interface Segregation**
   - `LanguageModelProvider` define solo `generate_stream()`
   - Agentes tienen interfaces específicas (análisis, votación, moderación)

5. **Dependency Inversion**
   - Agentes dependen de `LanguageModelProvider` abstraction, no implementaciones concretas
   - Factory crea dependencias, no los agentes directamente

## 📋 Flujo de Ejecución

### Fase 1: Inicialización
1. Usuario hace clic en "Iniciar Análisis Multi-Agente"
2. Backend recibe datos fiscales del contribuyente
3. Se crean 3 expertos con personalidades/profesiones aleatorias
4. Se crea el moderador
5. Se calcula la situación fiscal actual

### Fase 2: Introducción (450-500 caracteres)
- Moderador presenta el caso y los expertos participantes

### Fase 3: Rondas de Discusión (3 rondas)
**Cada ronda:**
1. Cada experto genera su análisis (450-500 caracteres)
   - Desde su perspectiva profesional
   - Con su personalidad característica
   - Con números concretos
2. Moderador resume puntos clave de la ronda (450-500 caracteres)

### Fase 4: Votación
1. Moderador anuncia la votación (450-500 caracteres)
2. Cada experto vota por la mejor estrategia (puede votar por sí mismo)
3. Se cuentan votos con `Counter`
4. Se determina estrategia ganadora

### Fase 5: Conclusión Final (450-500 caracteres)
- Moderador entrega conclusión con estrategia ganadora y beneficios esperados

## 🎭 Personalidades Disponibles

### Conservative (Conservador)
- **Descripción:** Cauteloso y meticuloso, prioriza seguridad sobre riesgo
- **Enfoque:** Deducciones 100% seguras y documentadas, evita zonas grises

### Aggressive (Agresivo)
- **Descripción:** Audaz y optimizador, busca maximizar beneficios legales
- **Enfoque:** Explora todas las deducciones permitidas, maximiza cada peso

### Balanced (Balanceado)
- **Descripción:** Equilibrado entre riesgo y beneficio
- **Enfoque:** Balancea optimización fiscal con seguridad jurídica

### Analytical (Analítico)
- **Descripción:** Basado en datos y cálculos precisos
- **Enfoque:** Números exactos, cada recomendación con cálculo respaldado

### Pragmatic (Pragmático)
- **Descripción:** Práctico y enfocado en implementación realista
- **Enfoque:** Solo lo que el contribuyente pueda implementar fácilmente

### Innovative (Innovador)
- **Descripción:** Creativo, propone estrategias no convencionales
- **Enfoque:** Estrategias fiscales creativas pero legales, piensa fuera de la caja

## 👔 Profesiones Disponibles

### Auditor Fiscal
- **Expertise:** Revisión de cumplimiento y riesgos fiscales
- **Focus:** Documentación y aprovechamiento de deducciones existentes

### Planeador Fiscal
- **Expertise:** Diseño de estrategias fiscales a largo plazo
- **Focus:** Estrategias multianuales sostenibles

### Contador Público
- **Expertise:** Contabilidad y cálculos fiscales precisos
- **Focus:** Análisis detallado y proyecciones exactas

### Asesor Financiero
- **Expertise:** Optimización de inversiones y patrimonio
- **Focus:** Relaciona estrategia fiscal con salud financiera integral

### Abogado Fiscalista
- **Expertise:** Marco legal y jurisprudencia fiscal
- **Focus:** Legalidad completa y fundamentos legales

### Consultor Empresarial
- **Expertise:** Estrategia de negocios y eficiencia operativa
- **Focus:** Vincula optimización fiscal con estrategia empresarial

## 🔌 API Endpoints

### POST `/api/multi-agent-analysis`
Análisis completo sin streaming. Retorna todo al final.

**Request:**
```json
{
  "taxpayer_name": "Juan Pérez",
  "fiscal_year": 2025,
  "monthly_gross_income": 12600.00,
  "bonus_days": 15,
  "vacation_days": 12,
  "vacation_premium_percentage": 0.25,
  "general_deductions": 71000.00,
  "total_tuition": 25000.00,
  "total_ppr": 15000.00
}
```

**Response:**
```json
{
  "success": true,
  "expert_profiles": [
    {
      "name": "Dr. Martínez",
      "profession": "Auditor Fiscal",
      "personality": "Analítico",
      "expertise": "Revisión de cumplimiento y riesgos fiscales"
    }
  ],
  "moderator": "Moderador Fiscal",
  "rounds": [
    {
      "round_number": 1,
      "interventions": [...],
      "moderator_summary": "..."
    }
  ],
  "voting_results": {
    "votes": [...],
    "winner": "Dr. Martínez",
    "winning_strategy": "..."
  },
  "conclusion": "...",
  "full_transcript": "..."
}
```

### POST `/api/multi-agent-analysis/stream`
Análisis con streaming en tiempo real (Server-Sent Events).

**Event Types:**
- `initialization` - Perfiles de expertos creados
- `phase` - Nueva fase (introduction, round_1, round_2, round_3, voting, conclusion)
- `chunk` - Fragmento de texto del agente actual
- `intervention_complete` - Intervención terminada
- `voting_results` - Resultados de votación
- `complete` - Análisis terminado
- `error` - Error durante el proceso

**SSE Stream Example:**
```
data: {"type":"initialization","experts":[...]}

data: {"type":"phase","phase":"introduction"}

data: {"type":"chunk","agent":"Moderador Fiscal","content":"Bienvenidos..."}

data: {"type":"intervention_complete","agent":"Moderador Fiscal"}

data: {"type":"complete","conclusion":"...","full_transcript":"..."}
```

## 💻 Integración Frontend

Ver `frontend_multiagent_example.html` para ejemplo completo con:
- Botón de inicio
- Streaming en tiempo real con EventSource
- Visualización de fases
- Tarjetas de expertos
- Resultados de votación
- Conclusión final
- Manejo de errores

### Código Mínimo

```javascript
const eventSource = new EventSource('/api/multi-agent-analysis/stream');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'initialization':
            // Mostrar expertos
            break;
        case 'chunk':
            // Agregar texto en tiempo real
            break;
        case 'complete':
            // Mostrar conclusión
            eventSource.close();
            break;
    }
};
```

## 🔧 Configuración

### Variables de Entorno Requeridas

```bash
# AI Provider (al menos uno)
DEEPSEEK_API_KEY=your_key_here      # Preferido
GEMINI_API_KEY=your_key_here        # Fallback

# Opcional
DEEPSEEK_MODEL=deepseek-chat        # Default
DEEPSEEK_TEMPERATURE=0.7            # Default
```

### Límites de Caracteres

Todos los agentes (expertos y moderador) deben generar entre **450-500 caracteres** por intervención. Esto está configurado en:

1. Los prompts del sistema
2. `max_tokens=600` en providers (buffer para seguridad)
3. Instrucciones explícitas en cada llamada

## 🎯 Casos de Uso

### 1. Usuario quiere segunda opinión
- 3 perspectivas profesionales diferentes
- Votación democrática
- Consenso en recomendación final

### 2. Análisis de escenarios complejos
- Personalidades conservadora vs. agresiva
- Balance entre riesgo y beneficio
- Estrategias creativas vs. tradicionales

### 3. Educación fiscal interactiva
- Usuario ve el proceso de debate
- Entiende diferentes enfoques profesionales
- Aprende criterios de decisión

## 🧪 Testing

### Prueba Manual
```bash
# Terminal 1: Iniciar servidor
uv run uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Test con curl
curl -X POST http://localhost:8000/api/multi-agent-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "taxpayer_name": "Test User",
    "fiscal_year": 2025,
    "monthly_gross_income": 12600,
    "bonus_days": 15,
    "vacation_days": 12,
    "vacation_premium_percentage": 0.25,
    "general_deductions": 50000,
    "total_tuition": 10000,
    "total_ppr": 10000
  }'
```

### Verificación de Streaming
```bash
curl -N -X POST http://localhost:8000/api/multi-agent-analysis/stream \
  -H "Content-Type: application/json" \
  -d '{...}'
```

## 🚀 Mejoras Futuras

### Corto Plazo
- [ ] Caché de análisis por perfil de contribuyente
- [ ] Métricas de calidad de recomendaciones
- [ ] Guardar transcripciones en base de datos

### Mediano Plazo
- [ ] Permitir al usuario elegir personalidades específicas
- [ ] Análisis comparativo de múltiples escenarios
- [ ] Exportar análisis a PDF

### Largo Plazo
- [ ] Integración con RAG para citar leyes específicas
- [ ] Análisis histórico de recomendaciones efectivas
- [ ] Modo "profesor" para educación fiscal

## 📊 Métricas y Monitoreo

### Logs Importantes
- Personalidades/profesiones asignadas
- Tiempo de respuesta por agente
- Tokens consumidos por análisis
- Errores de provider (fallback a Gemini)

### KPIs Sugeridos
- Tiempo promedio de análisis completo
- Tasa de consenso en votaciones
- Satisfacción del usuario por tipo de personalidad
- Frecuencia de uso del endpoint

## 🤝 Contribución

Al agregar nuevas funcionalidades:

1. **Nuevas Personalidades:** Agregar a `Personality` enum y `PERSONALITY_CONFIGS`
2. **Nuevas Profesiones:** Agregar a `Profession` enum y `PROFESSION_CONFIGS`
3. **Nuevos Providers:** Implementar `LanguageModelProvider` ABC
4. **Nuevas Fases:** Extender `MultiAgentConversationOrchestrator`

## 📝 Notas Técnicas

### Por qué 450-500 caracteres
- Suficiente para análisis sustancial
- No abruma al usuario
- Mantiene ritmo de conversación ágil
- Aproximadamente 2-3 párrafos cortos

### Selección Aleatoria
- `random.sample()` garantiza perfiles únicos
- Sin repetición en misma sesión
- Experiencia diferente en cada análisis

### Manejo de Errores
- Provider fallback (DeepSeek → Gemini)
- Votos inválidos asignan al primer experto
- Errores retornan mensaje descriptivo, no crash

## 📄 Licencia

Mismo que el proyecto principal Mimo.
