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
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

El servidor estará disponible en:

- **Web UI**: http://localhost:8000/calculator
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🏗️ Arquitectura

Mimo sigue una **arquitectura hexagonal híbrida** con separación clara de concerns:

```
src/
├── domain/          # Lógica de negocio pura (entidades, servicios)
├── application/     # Casos de uso (orquestación)
├── infrastructure/  # Adaptadores (DB, AI, OAuth)
└── api/            # Capa de presentación (FastAPI)
```

Ver [ARCHITECTURE.md](./ARCHITECTURE.md) para detalles completos.

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

## 🧪 Ejemplo de Uso

```python
import requests

# Calcular impuestos
response = requests.post('http://localhost:8000/api/calculate', json={
    "fiscal_year": 2024,
    "taxpayer_info": {
        "rfc": "XAXX010101000",
        "name": "Juan Pérez"
    },
    "income_data": {
        "monthly_income": 12600,
        "bonus_days": 15,
        "vacation_days": 12,
        "vacation_premium_percentage": 0.25
    },
    "deduction_data": {
        "general_deductions": 71000,
        "ppr_deductions": 15000,
        "education_deductions": 25000
    }
})

print(response.json())
```

## 🎯 Características

- ✅ **Cálculo ISR mexicano**: Implementa tablas ISR 2024-2025 con UMAs
- ✅ **Deducciones autorizadas**: Personales, PPR, educación con límites oficiales
- ✅ **Recomendaciones AI**: Generadas por DeepSeek/Gemini con personalidad gatuna
- ✅ **Análisis multi-agente**: 3 agentes debaten estrategias fiscales
- ✅ **OAuth Google**: Autenticación segura
- ✅ **Rate limiting**: 3 consultas AI por día (configurable)
- ✅ **Error handling**: Respuestas JSON consistentes
- ✅ **Streaming**: SSE para respuestas AI en tiempo real

## 🛠️ Tecnologías

- **Backend**: FastAPI + Uvicorn
- **Auth**: Google OAuth 2.0
- **AI**: Google Gemini + DeepSeek
- **Database**: SQLite (usage tracking)
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
