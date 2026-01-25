# Mimo 🐱 - Calculadora de Saldo a Favor ISR

**Mimo el Gatito Fiscal** es una calculadora de impuestos inteligente para personas físicas en México que calcula tu saldo a favor o a pagar del ISR (Impuesto Sobre la Renta) y genera recomendaciones fiscales personalizadas con IA.

## 🎯 Descripción General

Mimo es una aplicación web que simplifica el cálculo de impuestos anuales para contribuyentes mexicanos, aplicando las reglas oficiales del SAT y proporcionando análisis fiscal inteligente mediante múltiples agentes de IA con personalidades únicas.

### 💡 Origen del Nombre

**Mimo** proviene del juego de palabras en spanglish **"MI MO"ney** (Mi Dinero), simbolizando que tus recursos financieros te pertenecen, no al SAT. El proyecto nace de la necesidad de democratizar el conocimiento fiscal en México, donde la falta de información accesible lleva a muchos contribuyentes a perder beneficios legítimos al no solicitar facturas o realizar su declaración anual.

Mimo busca empoderar a las personas físicas para que tomen control de su situación fiscal mediante:

- **Transparencia**: Cálculos claros y explicados paso a paso
- **Educación**: Recomendaciones personalizadas que enseñan optimización fiscal legal
- **Accesibilidad**: Herramientas profesionales sin necesidad de conocimiento contable previo
- **Autonomía**: Información que permite tomar decisiones financieras informadas

### ¿Qué hace Mimo?

- **Cálculo preciso de ISR**: Aplica las tablas ISR oficiales 2024-2025 con exenciones de UMA
- **Recomendaciones personalizadas**: IA con personalidad de gato que genera consejos fiscales con juegos de palabras felinos

## ✨ Características Principales

### 📊 Cálculo de Impuestos

- Cálculo automático de ISR anual con deducciones personales
- Exenciones oficiales para aguinaldo y prima vacacional basadas en UMA
- Límites de deducción inteligentes: 5 UMAs o 15% del ingreso bruto (el menor)
- Deducciones autorizadas: personales, PPR (retiro), educación (colegiatura)
- Validación de límites oficiales por nivel educativo (preescolar, primaria, secundaria, preparatoria, universidad)

### 🤖 Recomendaciones con IA

- Streaming en tiempo real (Server-Sent Events)
- Saludos personalizados según la hora del día
- Análisis de espacio disponible para deducciones
- Límites de caracteres por respuesta (150-250 chars) para mantener debates concisos

### 🔒 Autenticación y Límites

- Google OAuth 2.0 para acceso seguro
- Límite diario de recomendaciones: 3 por usuario (configurable)
- Sesiones persistentes con SessionMiddleware
- Seguimiento de uso en PostgreSQL (SQLite solo en tests)

### 💬 Chat Interactivo con Agentes

- Selección de agente por personalidad y profesión
- Memoria conversacional con FAISS (vector store)
- Historial de mensajes con contexto fiscal
- Respuestas streaming en tiempo real

## 🚀 Instalación

### Prerequisitos

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)

### 1. Clonar el repositorio

```bash
git clone https://github.com/iam-oov/mimo.git
cd mimo
```

### 2. Instalar dependencias con uv

```bash
# Instalar uv si no lo tienes
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar dependencias del proyecto
uv sync
```

### 3. Configurar variables de entorno

Duplica el archivo `.env.example` a `.env` y completa las variables necesarias:

### 4. Ejecutar la aplicación

```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Acceder a la aplicación

Abre tu navegador y ve a `http://localhost:8000`

## ⚙️ Configuración

### Google OAuth

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un proyecto nuevo o selecciona uno existente
3. Habilita la API de Google+ (Google People API)
4. En "Credenciales" → "Crear credenciales" → "ID de cliente de OAuth 2.0"
5. Tipo de aplicación: "Aplicación web"
6. URIs de redireccionamiento autorizados:
   - Desarrollo: `http://localhost:8000/auth/callback`
   - Producción: `https://tu-dominio.com/auth/callback`
7. Copia el Client ID y Client Secret al `.env`

## 🛠️ Tecnologías Usadas

### Backend

- **[FastAPI](https://fastapi.tiangolo.com/)** - Framework web moderno y rápido
- **[Jinja2](https://jinja.palletsprojects.com/)** - Motor de templates para HTML

### Autenticación

- **[Authlib](https://authlib.org/)** - Cliente OAuth 2.0
- **[Starlette SessionMiddleware](https://www.starlette.io/)** - Manejo de sesiones

### IA y LLMs

- **[Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python)** - Claude Sonnet 4.5 (principal)
- **[LiteLLM](https://github.com/BerriAI/litellm)** - Router unificado para múltiples LLMs
- **[OpenAI-compatible API](https://platform.openai.com/docs/api-reference)** - DeepSeek
- **[Google Gemini API](https://ai.google.dev/)** - Fallback
- **[FAISS](https://github.com/facebookresearch/faiss)** - Vector store para memoria conversacional
- **[Sentence Transformers](https://www.sbert.net/)** - Embeddings para búsqueda semántica

### Frontend

- **[HTMX](https://htmx.org/)** - Interactividad sin escribir JavaScript
- **[Tailwind CSS](https://tailwindcss.com/)** - Framework CSS utility-first

### DevOps

- **[Railway](https://railway.app/)** - Hosting y deployment
- **[Nixpacks](https://nixpacks.com/)** - Build system
- **[Uvicorn](https://www.uvicorn.org/)** - Servidor ASGI

### Arquitectura

- **Hexagonal Architecture (Ports & Adapters)** - Separación de capas
- **Domain-Driven Design** - Modelado del dominio fiscal
- **Module-First Architecture** - Bounded contexts independientes
- **SOLID Principles** - Código mantenible y extensible

## 📝 Licencia

MIT License - Ver [LICENSE](LICENSE) para más detalles.

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Convenciones de código:

- Todo el código en **inglés** (variables, funciones, clases, comentarios)
- Seguir **SOLID principles**
- Type hints obligatorios
- Imports explícitos (nunca usar `__init__.py` para exportar)
- Comentarios mínimos (código auto-documentado)

## ⚠️ Disclaimer

Mimo es una herramienta educativa y de apoyo. **No sustituye el asesoramiento profesional de un contador o asesor fiscal certificado**. Siempre consulta con un profesional antes de tomar decisiones fiscales importantes.

## 🚧 Roadmap y Mejoras Planificadas

### Experiencia de Usuario

- **Diseño responsivo**: Optimización de la interfaz para dispositivos móviles y tablets
- **Formato de moneda**: Implementación de separadores de miles con coma (,) y símbolo de peso ($) en campos numéricos
- **Gestión de perfiles**: Sistema de preferencias de usuario con almacenamiento persistente

### Inteligencia Artificial

- **Detección contextual**: Capacidad de los agentes para identificar y reaccionar automáticamente a cambios en los datos de entrada
- **Análisis predictivo**: Sugerencias proactivas basadas en patrones de modificación de datos

### Gestión Documental

- **Repositorio de facturas**: Módulo de carga y almacenamiento de documentos fiscales (XML/PDF)
- **Extracción automatizada**: OCR y parsing de facturas para prellenado de campos
- **Biblioteca de documentos**: Organización categórica de comprobantes fiscales por período y tipo

### Infraestructura y Despliegue

- **Containerización**: Implementación de Docker para entorno de desarrollo y producción estandarizado

---

**Mimo el Gatito Fiscal** 🐱 - Haciendo tus impuestos "purr-fectos" desde 2025
