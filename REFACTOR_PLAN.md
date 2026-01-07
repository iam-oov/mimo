# 🎯 Plan de Refactorización - Mimo

**Fecha:** Enero 6, 2026  
**Objetivo:** Completar migración a arquitectura hexagonal y optimizar estructura del proyecto

---

## 📋 Estado Actual

### ✅ Completado

- Arquitectura hexagonal base implementada en `src/`
- SOLID principles aplicados correctamente
- Dependency Injection Container funcional
- Ports & Adapters para AI providers
- Sistema multi-agente con streaming
- Rate limiting y autenticación OAuth

### ⚠️ Pendiente

- Eliminar archivos legacy no utilizados
- Reorganizar estructura de AI providers
- Mover constantes de dominio a ubicación correcta
- Agregar tests unitarios e integración
- Limpiar datos de usuario del repositorio

---

## 🔥 Prioridad Alta - Limpieza Inmediata

### Tarea 1: Eliminar Archivos Legacy

**Estimación:** 30 minutos  
**Impacto:** Alto - Reduce deuda técnica

**Resultado:** ✅ Los archivos legacy no existían físicamente (ya eliminados previamente). Se actualizó la documentación.

**Checklist:**

- [x] Buscar referencias en codebase actual
- [x] Verificar que `src/api/main.py` es el único entry point
- [x] Eliminar archivos (ya no existían)
- [x] Actualizar documentación (ARCHITECTURE.md, copilot-instructions.md)

---

### Tarea 2: Mover Constantes ISR al Dominio ✅ COMPLETADA

**Estimación:** 1 hora  
**Impacto:** Alto - Mejora arquitectura hexagonal

**Resultado:** Constantes ISR movidas exitosamente a la capa de dominio con todos los imports actualizados.

**Pasos realizados:**

1. [x] Crear directorio `src/domain/constants/`
2. [x] Mover `tabla_isr_constants.py` → `src/domain/constants/isr_tables.py`
3. [x] Actualizar todos los imports (5 archivos):
   - `src/domain/services/tax_calculation_service.py`
   - `src/application/calculate_tax_use_case.py`
   - `src/application/multi_agent_debate_service.py`
   - `src/application/multi_agent_chat_use_case.py`
   - `src/infrastructure/ai_providers/recommendation_adapters.py`
4. [x] Eliminar archivo original de la raíz
5. [x] Verificar imports funcionando correctamente

---

### Tarea 3: Limpiar Memoria del Repositorio ✅ COMPLETADA

**Estimación:** 15 minutos  
**Impacto:** Alto - Seguridad y limpieza

**Resultado:** Datos de usuario eliminados del repositorio y agregados patrones a .gitignore para prevenir futuros commits.

**Acciones realizadas:**

1. [x] Eliminar directorio `memory/100675567570031060606/`
2. [x] Agregar a `.gitignore`:

   ```gitignore
   # User memory data (FAISS indices)
   memory/
   !memory/.gitkeep

   # SQLite databases
   *.db
   *.db-journal
   ```

3. [x] Crear `memory/.gitkeep` vacío (para mantener estructura del directorio)
4. [x] Verificar limpieza exitosa

---

## 🟡 Prioridad Media - Reorganización

### Tarea 4: Reorganizar AI Providers por Feature ✅ COMPLETADA

**Estimación:** 2-3 horas  
**Impacto:** Medio - Mejora mantenibilidad

**Resultado:** AI providers reorganizados en estructura modular por feature con un archivo por clase (SRP).

**Estructura nueva implementada:**

```
infrastructure/ai_providers/
├── litellm/
│   ├── __init__.py
│   └── adapter.py
├── recommendations/
│   ├── __init__.py
│   ├── _shared.py (utilidades compartidas)
│   ├── deepseek_adapter.py
│   ├── gemini_adapter.py
│   └── fallback_adapter.py
├── multi_agent/
│   ├── __init__.py
│   ├── deepseek_adapter.py
│   └── gemini_adapter.py
└── prompts/
    ├── __init__.py
    ├── recommendation_prompts.py
    └── multi_agent_prompts.py
```

**Pasos realizados:**

1. [x] Crear directorios feature-based
2. [x] Separar clases en archivos individuales (SRP)
3. [x] Mover prompts a subdirectorio
4. [x] Crear `__init__.py` vacíos (siguiendo convención del proyecto)
5. [x] Actualizar imports en:
   - `src/infrastructure/config/dependency_injection.py`
   - `src/application/multi_agent_chat_use_case.py`
   - `src/application/multi_agent_debate_service.py`
   - `src/infrastructure/ai_providers/litellm/adapter.py`
6. [x] Eliminar archivos originales planos
7. [x] Verificar estructura con tree

**Beneficios:**

- ✅ Cada archivo tiene una responsabilidad única
- ✅ Más fácil agregar nuevos providers
- ✅ Imports más claros y específicos
- ✅ Testing más granular

---

### Tarea 5: Agregar Tests Unitarios

**Estimación:** 4-6 horas  
**Impacto:** Alto - Confiabilidad

**Estructura:**

```
tests/
├── __init__.py
├── conftest.py
├── unit/
│   ├── __init__.py
│   ├── domain/
│   │   ├── test_tax_calculation_entity.py
│   │   ├── test_tax_calculation_service.py
│   │   └── test_value_objects.py
│   ├── application/
│   │   ├── test_calculate_tax_use_case.py
│   │   ├── test_recommendations_use_case.py
│   │   └── test_multi_agent_use_case.py
│   └── infrastructure/
│       ├── test_sqlite_repository.py
│       └── test_oauth_service.py
└── integration/
    ├── __init__.py
    ├── test_tax_calculation_flow.py
    └── test_recommendations_flow.py
```

**Prioridad de tests:**

1. [ ] **Domain services** (sin dependencias externas)
   - `TaxCalculationService` - 100% coverage objetivo
2. [ ] **Use cases** (mock dependencies)
   - `CalculateTaxUseCase`
   - `GenerateRecommendationsUseCase`
3. [ ] **Infrastructure** (integration tests)
   - `SqliteUsageRepository`
   - AI provider adapters (con mocks de API)

**Configuración:**

```toml
# En pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--cov=src",
    "--cov-report=html",
    "--cov-report=term-missing",
]

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/__init__.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

---

## 🟢 Prioridad Baja - Optimizaciones

### Tarea 6: Mejorar Configuración ✅ COMPLETADA

**Estimación:** 1-2 horas  
**Impacto:** Medio - Mejora validaciones y mantenibilidad

**Resultado:** Configuración mejorada con properties calculadas y validaciones automáticas.

**Mejoras implementadas:**

1. [x] Convertir métodos a properties con `@property`:

   ```python
   @property
   def is_production(self) -> bool:
       return self.environment.lower() == "production"

   @property
   def is_development(self) -> bool:
       return self.environment.lower() == "development"

   @property
   def log_level(self) -> str:
       return "INFO" if self.is_production else "DEBUG"
   ```

2. [x] Agregar validaciones con `@model_validator`:

   ```python
   @model_validator(mode='after')
   def validate_configuration(self) -> 'Settings':
       # Validar al menos un AI provider configurado
       if not self.has_any_ai_provider():
           raise ValueError("At least one AI provider must be configured")

       # Validar SECRET_KEY fuerte en producción
       if self.is_production:
           if not self.secret_key or len(self.secret_key) < 32:
               raise ValueError("Production requires strong SECRET_KEY (min 32 chars)")

       return self
   ```

**Beneficios:**

- ✅ Validación automática al inicializar settings
- ✅ Falla rápido si configuración es inválida
- ✅ Properties más idiomáticas (acceso directo sin paréntesis)
- ✅ Log level automático según ambiente

---

### Tarea 7: Logging Estructurado ✅

**Estimación:** 2 horas  
**Impacto:** Alto - Mejora observabilidad en producción

**Resultado:** Sistema de logging estructurado implementado con JSON en producción y formato legible en desarrollo.

**Implementación:**

```python
# src/infrastructure/logging/structured_logger.py
class StructuredLogger:
    """Structured logger with environment-aware formatting"""

    def info(self, message: str, **context: Any):
        self._log("INFO", message, context)

    def error(self, message: str, **context: Any):
        self._log("ERROR", message, context)

    def _format_log(self, level: str, message: str, context: Dict[str, Any]) -> str:
        timestamp = datetime.now(UTC).isoformat()

        if self._settings.is_production:
            # JSON format for log aggregators
            log_data = {
                "timestamp": timestamp,
                "level": level,
                "message": message,
                "logger": self._name,
                **context
            }
            return json.dumps(log_data)
        else:
            # Readable format for development
            context_str = " | ".join(f"{k}={v}" for k, v in context.items())
            return f"[{level}] {message} | {context_str}"
```

**Integrado en:**

- [x] AI provider adapters (deepseek_adapter.py)
- [x] Use cases (generate_recommendations, multi_agent_debate, calculate_tax)
- [x] Middleware (error_handler.py - request logging)

**Archivos modificados:**

1. `src/infrastructure/logging/structured_logger.py` - Módulo creado
2. `src/infrastructure/ai_providers/recommendations/deepseek_adapter.py` - Logging con contexto (model, fiscal_year, temperature)
3. `src/application/generate_recommendations_use_case.py` - Logging con contexto (user_id, provider, fiscal_year)
4. `src/application/calculate_tax_use_case.py` - Import agregado
5. `src/application/multi_agent_debate_service.py` - Logging con contexto (agent_name, round, error_type)
6. `src/api/middleware/error_handler.py` - Logging con contexto (path, method, status_code)

**Beneficios:**

- ✅ JSON logs parseables por agregadores (Datadog, CloudWatch)
- ✅ Contexto rico para debugging (model, user_id, fiscal_year, etc.)
- ✅ Formato automático según ambiente (JSON prod, legible dev)
- ✅ Interfaz consistente en todas las capas

---

### Tarea 8: Documentación Completa ✅

**Estimación:** 3-4 horas  
**Impacto:** Alto - Mejora mantenibilidad y onboarding

**Resultado:** Documentación completa de APIs públicas con docstrings detalladas y ejemplos de uso.

**Implementación:**

1. **Docstrings en Routers (API Layer):**

   - [tax_router.py](src/api/v1/routers/tax_router.py):
     - `calculate_tax()`: Detalles de cálculo ISR, exemptions, deduction caps, ejemplos
   - [recommendations_router.py](src/api/v1/routers/recommendations_router.py):
     - `get_usage_info()`: Documentación de rate limiting
     - `generate_recommendations_stream()`: Formato SSE, provider priority, ejemplos de stream
   - [multi_agent_router.py](src/api/v1/routers/multi_agent_router.py):
     - `generate_multi_agent_analysis()`: Estructura de debate, eventos SSE, ejemplos de agentes
   - [auth_router.py](src/api/v1/routers/auth_router.py):
     - `login_with_google()`: Flujo OAuth completo, scopes solicitados
     - `logout()`: Comportamiento de sesión
     - `auth_status()`: Formato de respuesta, uso frontend

2. **Docstrings en Use Cases (Application Layer):**

   - [calculate_tax_use_case.py](src/application/calculate_tax_use_case.py):
     - `CalculateTaxUseCase`: Reglas de negocio ISR, cálculos clave, interacción con domain layer
   - [generate_recommendations_use_case.py](src/application/generate_recommendations_use_case.py):
     - Docstrings ya existentes y completos
   - [generate_multi_agent_analysis_use_case.py](src/application/generate_multi_agent_analysis_use_case.py):
     - `GenerateMultiAgentAnalysisUseCase`: Estructura de debate, rate limiting, uso de providers
     - `can_generate()`: Lógica de rate limiting
     - `get_usage_info()`: Formato de respuesta de uso

3. **README Mejorado:**
   - [README.md](README.md):
     - Ejemplos completos de uso para cada endpoint:
       - Cálculo básico de ISR con código Python
       - Recomendaciones AI con streaming SSE
       - Análisis multi-agente con parsing de eventos
       - Consulta de uso de API
       - Flujo OAuth completo
     - Código ejecutable con imports y manejo de respuestas
     - Ejemplos de SSE con parsing de eventos `data:` y `event:`

**Archivos modificados:**

1. `src/api/v1/routers/tax_router.py` - Docstring mejorado con detalles de cálculo ISR
2. `src/api/v1/routers/recommendations_router.py` - Docstrings con formato SSE y provider priority
3. `src/api/v1/routers/multi_agent_router.py` - Docstring con estructura de debate y eventos
4. `src/api/v1/routers/auth_router.py` - Docstrings con flujo OAuth y comportamiento de sesión
5. `src/application/calculate_tax_use_case.py` - Docstring con reglas de negocio ISR
6. `src/application/generate_multi_agent_analysis_use_case.py` - Docstrings con detalles de debate
7. `README.md` - Sección "Ejemplos de Uso" ampliada con 5 casos prácticos ejecutables

**Beneficios:**

- ✅ APIs auto-documentadas (FastAPI Swagger genera docs desde docstrings)
- ✅ Ejemplos ejecutables para cada endpoint
- ✅ Formato SSE claramente explicado
- ✅ Onboarding más rápido para nuevos desarrolladores
- ✅ Documentación inline (no requiere archivos externos)

---

### Tarea 9: CI/CD Pipeline ✅

**Estimación:** 2-3 horas  
**Impacto:** Alto - Automatiza calidad del código

**Resultado:** Pipeline de CI/CD implementado con linting automático (testing pendiente para Tarea 5).

**Implementación:**

1. **GitHub Actions - Linting** (`.github/workflows/lint.yml`):

   - Ejecuta en cada push/PR a `main` y `develop`
   - Usa `astral-sh/setup-uv@v3` para instalar uv
   - Ejecuta `ruff check` para validar código
   - Ejecuta `ruff format --check` para validar formato
   - Bloquea merge si hay errores de linting

2. **Pre-commit Hooks** (`.pre-commit-config.yaml`):

   - **ruff**: Linting con auto-fix (`--fix`)
   - **ruff-format**: Formatting automático
   - **pre-commit-hooks**: Validaciones básicas (trailing whitespace, EOF, YAML/JSON/TOML syntax)
   - Se ejecuta localmente antes de cada commit

3. **Configuración Ruff** (`pyproject.toml`):

   ```toml
   [tool.ruff]
   line-length = 100
   target-version = "py312"

   [tool.ruff.lint]
   select = ["E", "W", "F", "I", "N", "UP", "B", "SIM"]
   ignore = ["E501"]  # line too long (formatter handles it)
   ```

**Archivos creados:**

1. `.github/workflows/lint.yml` - Workflow de linting en CI
2. `.pre-commit-config.yaml` - Hooks de pre-commit con ruff
3. `pyproject.toml` - Configuración de ruff agregada

**Cómo usar:**

```bash
# Instalar pre-commit hooks localmente
uv run pre-commit install

# Ejecutar manualmente en todos los archivos
uv run pre-commit run --all-files

# Ejecutar ruff directamente
uv run ruff check .
uv run ruff format .
```

**Beneficios:**

- ✅ Linting automático en cada push/PR (GitHub Actions)
- ✅ Pre-commit hooks previenen commits con errores
- ✅ Consistencia de código en todo el equipo
- ✅ Formato automático con ruff (más rápido que black)
- ✅ Validaciones básicas (whitespace, EOF, YAML/JSON syntax)

**Pendiente:**

- ⏳ Testing workflow (requiere Tarea 5 - Tests Unitarios)
- ⏳ Deployment workflow (Railway/producción)
- ⏳ Coverage reporting (Codecov)

---

## 📊 Métricas de Éxito

### Antes del Refactor

- ⚠️ Archivos legacy: 3 (server.py, fiscal_recommendations.py, multi_agent_analysis.py)
- ⚠️ Constantes fuera de dominio: 1 (tabla_isr_constants.py)
- ⚠️ Data de usuario en repo: Sí (memory/)
- ⚠️ Test coverage: 0%
- ⚠️ AI providers sin organizar: 5 clases en 2 archivos

### Después del Refactor

- ✅ Archivos legacy: 0
- ✅ Constantes en dominio: 100%
- ✅ Data limpia: Solo .gitkeep
- ✅ Test coverage: >80% objetivo
- ✅ AI providers organizados: 1 clase por archivo

---

## 🚀 Orden de Ejecución Recomendado

### Sprint 1 - Limpieza (1 semana)

```bash
Día 1-2: Tarea 1 (Eliminar legacy) + Tarea 3 (Limpiar memory)
Día 3-4: Tarea 2 (Mover constantes ISR)
Día 5:   Verificación y testing manual
```

### Sprint 2 - Reorganización (1 semana)

```bash
Día 1-3: Tarea 4 (Reorganizar AI providers)
Día 4-5: Tarea 5 (Tests unitarios - Fase 1: Domain)
```

### Sprint 3 - Testing (1 semana)

```bash
Día 1-3: Tarea 5 continuación (Application + Infrastructure tests)
Día 4-5: Tarea 6 (Mejorar configuración)
```

### Sprint 4 - Optimización (1 semana)

```bash
Día 1-2: Tarea 7 (Logging estructurado)
Día 3-4: Tarea 8 (Documentación)
Día 5:   Tarea 9 (CI/CD)
```

---

## ⚠️ Riesgos y Mitigaciones

### Riesgo 1: Breaking Changes en Imports

**Mitigación:**

- Hacer cambios en branch separado
- Buscar todas las referencias antes de mover archivos
- Ejecutar app manualmente después de cada cambio

### Riesgo 2: Tests Rompen Funcionalidad Existente

**Mitigación:**

- Testing manual antes de cada commit
- Mantener endpoint `/calculator` funcionando siempre
- Rollback plan documentado

### Riesgo 3: Configuración en Producción (Railway)

**Mitigación:**

- No cambiar nombres de variables de entorno
- Documentar cualquier cambio de config
- Verificar `X-Forwarded-*` headers siguen funcionando

---

## 📝 Notas Importantes

1. **No crear archivos markdown de resumen** después de cada tarea (excepto este plan)
2. **Todo el código en inglés** (variables, funciones, clases, comments)
3. **SOLID principles** deben mantenerse en todo momento
4. **No romper OAuth flow** - crítico para producción
5. **Rate limiting** debe seguir funcionando
6. **Streaming SSE** no debe romperse

---

## ✅ Checklist Final

Marcar cuando se complete cada sprint:

- [ ] **Sprint 1 completo** - Código legacy eliminado
- [ ] **Sprint 2 completo** - AI providers reorganizados + Tests básicos
- [ ] **Sprint 3 completo** - Coverage >80% + Config mejorada
- [ ] **Sprint 4 completo** - Logging + Docs + CI/CD

---

## 🎉 Resultado Esperado

Al completar este plan, Mimo tendrá:

1. ✅ Arquitectura hexagonal 100% pura (sin legacy)
2. ✅ Tests con >80% coverage
3. ✅ CI/CD automatizado
4. ✅ Documentación completa
5. ✅ Código mantenible y escalable
6. ✅ Ready para nuevos features (nuevos AI providers, tipos de impuestos, etc.)

---

**Autor:** GitHub Copilot  
**Última actualización:** Enero 6, 2026
