# 🐱 Mimo - Calculadora de Saldo a Favor ISR

Calculadora de impuestos mexicana para personas físicas con recomendaciones fiscales personalizadas por IA.

## 🚀 Inicio Rápido

```bash
# Instalar dependencias
uv sync

# Configurar variables de entorno
cp .env.example .env

# Ejecutar servidor
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

**URLs:** http://localhost:8000/calculator | http://localhost:8000/docs

## 🔑 Variables de Entorno

```bash
# OAuth (requerido)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
SECRET_KEY=

# AI (al menos uno)
DEEPSEEK_API_KEY=
GEMINI_API_KEY=
```

## 📡 API Principal

- `POST /api/calculate` - Calcular ISR anual
- `POST /api/recommendations/stream` - Recomendaciones AI (SSE)
- `POST /api/multi-agent-analysis/stream` - Debate multi-agente (SSE)
- `GET /auth/google` - Iniciar OAuth

Requiere autenticación Google OAuth para AI features.
