# 🐱 Mimo - Calculadora de Saldo a Favor ISR

**Mimo el Gatito Fiscal** es una calculadora de impuestos mexicana para personas físicas que calcula el saldo a favor/a pagar anual y genera recomendaciones fiscales personalizadas con IA.

## 🚀 Inicio Rápido

### Requisitos

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (gestor de paquetes Python)

### Instalación

```bash
# Clonar el repositorio
git clone https://github.com/iam-oov/mimo.git
cd mimo

# Instalar dependencias
uv sync

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys
```

### Ejecutar el Servidor

```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

El servidor estará disponible en:

- **Web UI**: http://localhost:8000/calculator
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🏗️ Arquitectura

Mimo sigue una **arquitectura modular (module-first)** con capas hexagonales dentro de cada módulo:

```
src/
├── tax_calculation/       # Módulo de cálculo ISR
│   ├── domain/           # Entities, Services, Value Objects
│   ├── application/      # Use Cases
│   └── infrastructure/   # Adapters (API, etc.)
│
├── recommendations/      # Módulo de recomendaciones AI
│   ├── domain/          # Ports (interfaces)
│   ├── application/     # Use Cases
│   └── infrastructure/  # Adapters (API, AI providers)
│
├── multi_agent/         # Módulo de análisis multi-agente
│   ├── domain/          # Ports (interfaces)
│   ├── application/     # Use Cases, Debate Service
│   └── infrastructure/  # Adapters (API, providers, LiteLLM)
│
├── auth/                # Módulo de autenticación (infrastructure-only)
│   └── infrastructure/  # OAuth, dependencies
│
├── shared/              # Código compartido entre módulos
│   ├── domain/          # ISR tables, constants
│   └── infrastructure/  # Config, logging, persistence
│
└── main.py             # FastAPI application entry point
```

Ver [ARCHITECTURE.md](./ARCHITECTURE.md) para detalles completos.  
Ver [MODULES.md](./MODULES.md) para descripción de cada módulo.

## 🔑 Variables de Entorno

```bash
# OAuth (requerido para recomendaciones AI)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret

# Session security
SECRET_KEY=your_secret_key

# AI Providers (al menos uno requerido)
DEEPSEEK_API_KEY=your_deepseek_key  # Preferido
GEMINI_API_KEY=your_gemini_key      # Fallback

# Configuración opcional
DAILY_RECOMMENDATIONS_LIMIT=3  # Límite diario de recomendaciones por usuario
```

## 📡 API Endpoints

### Autenticación

- `GET /auth/google` - Iniciar OAuth con Google
- `GET /auth/callback` - Callback de OAuth
- `GET /auth/logout` - Cerrar sesión
- `GET /auth/status` - Estado de autenticación

### Cálculo de Impuestos

- `POST /api/calculate` - Calcular ISR anual

### Recomendaciones AI (requiere autenticación)

- `POST /api/recommendations` - Generar recomendaciones
- `POST /api/recommendations/stream` - Streaming SSE
- `GET /api/recommendations/usage` - Consultar uso diario

### Análisis Multi-Agente (requiere autenticación)

- `POST /api/multi-agent-analysis` - Debate de 3 agentes fiscales
- `POST /api/multi-agent-analysis/stream` - Streaming SSE
- `GET /api/multi-agent-analysis/usage` - Consultar uso diario

### Chat Interactivo Multi-Agente (requiere autenticación)

- `POST /api/chat/ask` - Enviar pregunta a un agente específico
- `POST /api/chat/ask/stream` - Chat con streaming SSE
- `GET /api/chat/agents` - Obtener lista de agentes disponibles
- `POST /api/chat/context` - Guardar contexto fiscal para chat
- `GET /api/chat/history` - Consultar historial de conversación

## 🧪 Ejemplos de Uso

### Cálculo Básico de ISR

```python
import requests

# Endpoint: POST /api/calculate
response = requests.post('http://localhost:8000/api/calculate', json={
    "taxpayer_name": "Juan Pérez",
    "fiscal_year": 2024,
    "monthly_gross_income": 15000.0,
    "monthly_net_income": 12600.0,
    "bonus_days": 30,
    "vacation_days": 12,
    "vacation_premium_percentage": 25.0,
    "general_deductions": 50000.0,
    "total_ppr": 30000.0,
    "total_tuition": 20000.0
})

result = response.json()
print(f"Saldo a favor/pagar: ${result['final_balance']:,.2f}")
print(f"Tasa efectiva: {result['effective_tax_rate']}%")
```

### Recomendaciones AI con Streaming

```python
import requests
import json

# Endpoint: POST /api/recommendations/stream (requiere autenticación)
headers = {"Cookie": "session=your_session_cookie"}

with requests.post(
    'http://localhost:8000/api/recommendations/stream',
    json={
        "taxpayer_name": "María González",
        "fiscal_year": 2024,
        "monthly_gross_income": 20000.0,
        "general_deductions": 75000.0,
        # ... otros campos
    },
    headers=headers,
    stream=True
) as response:
    for line in response.iter_lines():
        if line.startswith(b'data: '):
            data = json.loads(line[6:])
            if data['type'] == 'chunk':
                print(data['content'], end='', flush=True)
            elif data['type'] == 'complete':
                print("\n\n✅ Recomendaciones completas")
```

### Análisis Multi-Agente con SSE

```python
import requests
import json

# Endpoint: POST /api/multi-agent-analysis (requiere autenticación)
headers = {"Cookie": "session=your_session_cookie"}

with requests.post(
    'http://localhost:8000/api/multi-agent-analysis',
    json={
        "calculation_result": {
            "gross_annual_income": 240000.0,
            "final_balance": -15000.0,
            # ... resultado completo de cálculo
        },
        "user_data": {
            "deduction_data": {
                "general_deductions": 50000.0,
                "ppr_deductions": 30000.0,
                "education_deductions": 20000.0
            }
        },
        "fiscal_year": 2024
    },
    headers=headers,
    stream=True
) as response:
    for line in response.iter_lines():
        if line.startswith(b'event: message'):
            # Siguiente línea contiene los datos
            continue
        if line.startswith(b'data: '):
            event = json.loads(line[6:])

            if event['type'] == 'agent_intro':
                print("🎭 Agentes del debate:")
                for agent in event['agents']:
                    print(f"  - {agent['name']} ({agent['profession']})")

            elif event['type'] == 'agent_turn':
                print(f"\n💬 {event['agent_name']}:")

            elif event['type'] == 'agent_chunk':
                print(event['content'], end='', flush=True)

            elif event['type'] == 'synthesis_complete':
                print("\n\n✅ Análisis completo")
```

### Consultar Uso de API

```python
import requests

# Endpoint: GET /api/recommendations/usage (requiere autenticación)
headers = {"Cookie": "session=your_session_cookie"}

response = requests.get(
    'http://localhost:8000/api/recommendations/usage',
    headers=headers
)

usage = response.json()
print(f"Uso: {usage['usage_count']}/{usage['daily_limit']}")
print(f"Restantes: {usage['remaining_usage']}")
```

### Autenticación OAuth

```python
# 1. Iniciar flujo OAuth
# GET http://localhost:8000/auth/google
# -> Redirige a Google

# 2. Google redirige a callback con código
# GET http://localhost:8000/auth/callback?code=...
# -> Crea sesión y redirige a /calculator

# 3. Verificar estado de autenticación
import requests

response = requests.get('http://localhost:8000/auth/status')
status = response.json()

if status['authenticated']:
    print(f"Sesión activa: {status['user']['name']}")
else:
    print("No autenticado")
```

## 🎯 Características

- ✅ **Cálculo ISR mexicano**: Implementa tablas ISR 2024-2025 con UMAs
- ✅ **Deducciones autorizadas**: Personales, PPR, educación con límites oficiales
- ✅ **Recomendaciones AI**: Generadas por DeepSeek/Gemini con personalidad gatuna
- ✅ **Análisis multi-agente**: 3 agentes debaten estrategias fiscales
- ✅ **Chat interactivo**: Conversación con agentes fiscales individuales
- ✅ **Memoria semántica**: FAISS guarda contexto de conversaciones por usuario
- ✅ **OAuth Google**: Autenticación segura
- ✅ **Rate limiting**: 3 consultas AI por día (configurable)
- ✅ **Error handling**: Respuestas JSON consistentes
- ✅ **Streaming**: SSE para respuestas AI en tiempo real

## 🛠️ Tecnologías

- **Backend**: FastAPI + Uvicorn
- **Auth**: Google OAuth 2.0
- **AI**: Google Gemini + DeepSeek
- **Database**: SQLite (usage tracking)
- **Memory**: FAISS + Sentence Transformers (semantic search)
- **Package Manager**: uv
- **Validation**: Pydantic v2

## 📚 Documentación

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Guía completa de arquitectura
- [.github/copilot-instructions.md](./.github/copilot-instructions.md) - Instrucciones para desarrollo
- [.github/RECOMMENDATIONS_MIGRATION.md](./.github/RECOMMENDATIONS_MIGRATION.md) - Migración de recomendaciones

## 🤝 Contribuir

1. Todo el código debe estar en **inglés** (variables, funciones, comentarios)
2. Seguir **principios SOLID**
3. Usar **type hints** en todas las funciones
4. Código auto-documentado, comentarios solo para lógica compleja
5. Nuevas features en `src/`, no modificar archivos legacy

## 📝 Licencia

MIT License - Ver [LICENSE](./LICENSE) para detalles.

## 🙋 Soporte

Para preguntas o issues, abre un [issue en GitHub](https://github.com/iam-oov/mimo/issues).

---

Hecho con ❤️ y 🐱 por el equipo de Mimo
