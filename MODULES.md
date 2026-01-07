# 📦 Módulos de Mimo

Este documento describe los bounded contexts (módulos) de Mimo y sus responsabilidades.

---

## 📊 tax_calculation

**Bounded Context:** Cálculo de ISR anual para personas físicas mexicanas

### Responsabilidades

- Calcular impuestos mensuales y anuales según tablas ISR
- Aplicar exenciones de aguinaldo y prima vacacional (UMA-based)
- Calcular deducciones autorizadas con límites proporcionales
- Generar balance a favor o a pagar

### Estructura

```
tax_calculation/
├── domain/
│   ├── entities/
│   │   └── tax_calculation.py          # TaxCalculation entity con lógica de cálculo
│   ├── services/
│   │   └── tax_calculation_service.py  # TaxCalculationService (business logic)
│   └── value_objects/
│       └── tax_data.py                 # TaxpayerInfo, IncomeData, DeductionData
├── application/
│   └── calculate_tax_use_case.py       # CalculateTaxUseCase (orchestration)
└── infrastructure/
    └── api/
        └── tax_router.py               # REST API (driving adapter)
```

### API Endpoints

- `POST /api/calculate` - Calcular ISR anual

### Dependencias

- **shared**: ISR tables (`get_tabla_isr`), logging, config
- **No depende de otros módulos**

### Ejemplo de uso

```python
from src.tax_calculation.application.calculate_tax_use_case import (
    CalculateTaxUseCase, CalculateTaxRequest
)

request = CalculateTaxRequest(
    taxpayer_name="Juan Pérez",
    fiscal_year=2024,
    monthly_gross_income=15000.0,
    general_deductions=50000.0,
    ppr_deductions=30000.0,
    education_deductions=20000.0
)

use_case = CalculateTaxUseCase()
response = use_case.execute(request)
print(f"Balance: ${response.calculation.final_balance:,.2f}")
```

---

## 🤖 recommendations

**Bounded Context:** Recomendaciones fiscales personalizadas con IA

### Responsabilidades

- Generar recomendaciones fiscales usando AI (DeepSeek, Gemini)
- Streaming SSE para respuestas en tiempo real
- Rate limiting (3 recomendaciones/día por usuario)
- Personalización basada en datos fiscales del usuario

### Estructura

```
recommendations/
├── domain/
│   └── ports/
│       └── recommendation_provider.py   # RecommendationProvider port
├── application/
│   └── generate_recommendations_use_case.py  # Use case principal
└── infrastructure/
    ├── api/
    │   └── recommendations_router.py    # REST API (driving adapter)
    ├── providers/                       # Driven adapters (AI providers)
    │   ├── deepseek_adapter.py         # DeepSeek implementation
    │   └── gemini_adapter.py           # Gemini implementation
    └── prompts/
        └── recommendation_prompts.py    # Prompt templates
```

### API Endpoints

- `POST /api/recommendations/stream` - Streaming SSE de recomendaciones (requiere auth)
- `GET /api/recommendations/usage` - Consultar uso diario

### Dependencias

- **shared**: Config, logging, persistence (`UsageRepository`), schemas
- **tax_calculation**: Usa `TaxCalculation` entity para análisis
- **auth**: Requiere autenticación OAuth

### Características

- ✅ Prioridad: DeepSeek → Gemini (sin fallback estático)
- ✅ Streaming SSE con chunks progresivos
- ✅ Prompts con personalidad de "Mimo el Gatito Fiscal"
- ✅ Rate limiting diario por usuario

---

## 🎭 multi_agent

**Bounded Context:** Análisis multi-agente con debate de expertos fiscales

### Responsabilidades

- Debate entre 3 agentes AI con personalidades y profesiones únicas
- Chat interactivo con selección de agente
- Memoria conversacional con FAISS
- Streaming SSE de análisis multi-ronda
- Rate limiting (3 análisis/día por usuario)

### Estructura

```
multi_agent/
├── domain/
│   └── ports/
│       ├── multi_agent_provider.py      # MultiAgentProvider port
│       └── memory.py                    # MemoryStore port
├── application/
│   ├── generate_multi_agent_analysis_use_case.py  # Análisis completo
│   ├── multi_agent_chat_use_case.py              # Chat interactivo
│   └── multi_agent_debate_service.py             # Domain service (debate logic)
└── infrastructure/
    ├── api/
    │   ├── multi_agent_router.py        # REST API para análisis
    │   └── multi_agent_chat_router.py   # REST API para chat
    ├── providers/
    │   ├── deepseek_adapter.py          # DeepSeek adapter
    │   └── gemini_adapter.py            # Gemini adapter
    ├── litellm/
    │   └── adapter.py                   # LiteLLM integration (multi-model)
    ├── memory/
    │   └── faiss_memory.py              # FAISS memory adapter
    └── prompts/
        └── multi_agent_prompts.py       # Prompt templates + agent configs
```

### API Endpoints

- `POST /api/multi-agent-analysis/stream` - Análisis con debate (requiere auth)
- `GET /api/multi-agent-analysis/usage` - Consultar uso diario
- `POST /api/chat/agents` - Obtener lista de agentes disponibles
- `POST /api/chat/message` - Enviar mensaje a agente específico (streaming)

### Dependencias

- **shared**: Config, logging, persistence (`UsageRepository`), schemas
- **tax_calculation**: Usa `TaxCalculation` entity para contexto fiscal
- **auth**: Requiere autenticación OAuth

### Características

- ✅ 3 agentes con personalidades aleatorias (Conservative, Aggressive, Analytical, etc.)
- ✅ 6 profesiones aleatorias (Auditor, Tax Planner, Accountant, etc.)
- ✅ LiteLLM para routing flexible de modelos (Claude, DeepSeek, GPT-4, etc.)
- ✅ FAISS para memoria semántica por usuario
- ✅ 3 rondas de debate: Propuestas iniciales → Respuestas → Consenso
- ✅ Síntesis final con roadmap de implementación

---

## 🔐 auth

**Bounded Context:** Autenticación y autorización

### Responsabilidades

- OAuth 2.0 con Google
- Gestión de sesiones con cookies
- Middleware de autenticación
- Dependencies de FastAPI para proteger endpoints

### Estructura

```
auth/
└── infrastructure/                      # Infrastructure-only module
    ├── api/
    │   └── auth_router.py               # REST API (OAuth callbacks)
    ├── oauth_service.py                 # GoogleOAuthService
    └── dependencies.py                  # get_user_id, get_current_user
```

**Nota:** Este módulo es **infrastructure-only** porque la autenticación es una responsabilidad transversal (cross-cutting concern), no lógica de dominio.

### API Endpoints

- `GET /auth/google` - Iniciar flujo OAuth
- `GET /auth/callback` - Callback de Google
- `GET /auth/logout` - Cerrar sesión
- `GET /auth/status` - Estado de autenticación

### Dependencias

- **shared**: Config (`settings.google_client_id`, etc.)

### Características

- ✅ Railway/Proxy-aware (usa headers `X-Forwarded-*`)
- ✅ Clock skew tolerance (10 segundos)
- ✅ Session cookies con `httponly`, `secure`
- ✅ User ID: `user["sub"]` (Google's unique ID) o email como fallback

---

## 🔧 shared

**Bounded Context:** Código compartido entre módulos (Shared Kernel)

### Responsabilidades

- Tablas ISR y constantes fiscales
- Configuración centralizada (Pydantic Settings)
- Logging estructurado (JSON en prod, legible en dev)
- Persistencia (SQLite para usage tracking)
- Middleware (error handlers, request logging)
- Schemas compartidos (DTOs)

### Estructura

```
shared/
├── domain/
│   ├── constants/
│   │   └── isr_tables.py                # ISR tables 2024-2025 (hardcoded)
│   ├── value_objects/                   # Shared value objects
│   └── ports/
│       └── repositories.py              # UsageRepository port
└── infrastructure/
    ├── api/
    │   ├── middleware/
    │   │   └── error_handler.py         # Global error handling
    │   └── schemas/
    │       ├── tax_schemas.py           # Tax DTOs
    │       ├── recommendation_schemas.py # Recommendation DTOs
    │       └── multi_agent_schemas.py   # Multi-agent DTOs
    ├── config/
    │   ├── settings.py                  # Pydantic Settings
    │   └── dependency_injection.py      # DI Container
    ├── logging/
    │   └── structured_logger.py         # Structured logger
    └── persistence/
        └── sqlite_usage_repository.py   # SQLite implementation
```

### Dependencias

- **No depende de otros módulos** (es la base)

### Características

- ✅ ISR tables para años fiscales 2024-2025 (hardcoded, no JSON)
- ✅ UMA values, tax brackets, deduction limits
- ✅ Settings con validación (Pydantic)
- ✅ DI Container con lazy loading de providers
- ✅ Logging: JSON en prod, human-readable en dev
- ✅ Usage tracking con SQLite (recommendations.db)

---

## 📐 Convenciones de Imports

### ✅ Correcto: Imports directos desde archivos

```python
# Tax calculation
from src.tax_calculation.domain.entities.tax_calculation import TaxCalculation
from src.tax_calculation.application.calculate_tax_use_case import CalculateTaxUseCase

# Recommendations
from src.recommendations.domain.ports.recommendation_provider import RecommendationProvider
from src.recommendations.infrastructure.providers.deepseek_adapter import DeepSeekRecommendationAdapter

# Multi-agent
from src.multi_agent.application.multi_agent_debate_service import MultiAgentDebateService
from src.multi_agent.infrastructure.litellm.adapter import create_agent_adapter

# Auth
from src.auth.infrastructure.dependencies import get_user_id

# Shared
from src.shared.domain.constants.isr_tables import get_tabla_isr
from src.shared.infrastructure.config.settings import get_settings
```

### ❌ Incorrecto: Usar `__init__.py` para exports

```python
# ❌ NO HACER ESTO
from src.tax_calculation.domain import TaxCalculation
from src.recommendations import GenerateRecommendationsUseCase
```

**Razón:** Los `__init__.py` están vacíos por convención para evitar imports circulares.

---

## 🔄 Dependencias entre Módulos

```
┌─────────────┐
│   shared    │  ← Base (ISR tables, config, logging)
└──────┬──────┘
       │
       ├─────────────┬───────────────┬────────────────┐
       │             │               │                │
┌──────▼──────┐ ┌───▼────────┐ ┌────▼─────────┐ ┌───▼──────┐
│tax_calculation│ │recommendations│ │ multi_agent │ │   auth   │
└──────────────┘ └───────┬────┘ └────┬─────────┘ └──────────┘
                         │           │
                         │           │
                    ┌────▼───────────▼───┐
                    │ tax_calculation    │ (usa TaxCalculation entity)
                    └────────────────────┘
```

**Reglas:**

- ✅ Todos los módulos pueden usar **shared**
- ✅ `recommendations` y `multi_agent` pueden usar `tax_calculation` (para análisis)
- ❌ `tax_calculation` NO debe depender de `recommendations` ni `multi_agent`
- ❌ Módulos de features NO se importan entre sí directamente

---

## 🚀 Agregar un Nuevo Módulo

1. **Crear estructura:**

   ```bash
   mkdir -p src/nuevo_modulo/domain/{entities,services,ports}
   mkdir -p src/nuevo_modulo/application
   mkdir -p src/nuevo_modulo/infrastructure/{api,providers}
   ```

2. **Definir ports (interfaces) en `domain/ports/`**

3. **Implementar use cases en `application/`**

4. **Crear adapters en `infrastructure/`**

5. **Registrar router en `src/main.py`:**

   ```python
   from src.nuevo_modulo.infrastructure.api.nuevo_router import router as nuevo_router
   app.include_router(nuevo_router)
   ```

6. **Actualizar `dependency_injection.py` si necesitas DI**

7. **Documentar en este archivo (MODULES.md)**

---

## 📚 Referencias

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Detalles técnicos de arquitectura
- [MODULAR_ARCHITECTURE_PLAN.md](./MODULAR_ARCHITECTURE_PLAN.md) - Plan de migración
- [README.md](./README.md) - Guía de inicio rápido
