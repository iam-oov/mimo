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
4. [ ] Actualizar `__init__.py` para exports limpios
5. [ ] Actualizar imports en:
   - `src/infrastructure/config/dependency_injection.py`
   - `src/application/generate_recommendations_use_case.py`
   - `src/application/generate_multi_agent_analysis_use_case.py`
6. [ ] Verificar que todo funciona
7. [ ] Commit: `refactor: organize AI providers by feature`

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

### Tarea 6: Mejorar Configuración

**Estimación:** 1-2 horas

**Mejoras propuestas:**

1. [ ] Separar configs por ambiente:

   ```python
   # settings.py
   class Settings(BaseSettings):
       environment: str = "development"

       @property
       def is_production(self) -> bool:
           return self.environment == "production"

       @property
       def log_level(self) -> str:
           return "INFO" if self.is_production else "DEBUG"
   ```

2. [ ] Agregar validaciones de settings:

   ```python
   @model_validator(mode='after')
   def validate_ai_provider_configured(self) -> 'Settings':
       if not (self.has_deepseek_configured() or self.has_gemini_configured()):
           raise ValueError("At least one AI provider must be configured")
       return self
   ```

3. [ ] Crear configs específicas:
   ```
   config/
   ├── settings.py        # Base
   ├── development.py     # Dev overrides
   ├── production.py      # Prod overrides
   └── testing.py         # Test config
   ```

---

### Tarea 7: Logging Estructurado

**Estimación:** 2 horas

**Implementar:**

```python
# infrastructure/logging/logger.py
import logging
import json
from datetime import datetime

class StructuredLogger:
    """JSON structured logging for production"""

    @staticmethod
    def log(level: str, message: str, **context):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **context
        }

        if settings.is_production:
            print(json.dumps(log_entry))
        else:
            print(f"[{level}] {message} | {context}")
```

**Integrar en:**

- [ ] AI provider adapters (track AI calls)
- [ ] Use cases (track business operations)
- [ ] Middleware (track HTTP requests)

---

### Tarea 8: Documentación Completa

**Estimación:** 3-4 horas

**Generar:**

1. [ ] Docstrings en todos los módulos públicos
2. [ ] API documentation con Sphinx
3. [ ] Diagramas de arquitectura:
   - Diagrama de capas hexagonales
   - Flujo de datos (cálculo ISR)
   - Flujo multi-agente
4. [ ] Contributing guide
5. [ ] ADRs (Architecture Decision Records)

---

### Tarea 9: CI/CD Pipeline

**Estimación:** 2-3 horas

**GitHub Actions workflows:**

`.github/workflows/test.yml`:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install uv
        uses: astral-sh/setup-uv@v1
      - name: Run tests
        run: |
          uv sync
          uv run pytest --cov
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

`.github/workflows/lint.yml`:

```yaml
name: Lint
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install uv
        uses: astral-sh/setup-uv@v1
      - name: Run ruff
        run: |
          uv run ruff check .
          uv run ruff format --check .
```

**Pre-commit hooks:**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
```

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
