# Mimo - Calculadora de Saldo a Favor ISR

## Project Overview

Mimo is a **Mexican tax calculator** for individuals (personas físicas) that computes annual tax balance (saldo a favor/a pagar) and generates AI-powered personalized fiscal recommendations through "Mimo el Gatito Fiscal" 🐱 - a cat-themed tax advisor.

**Tech Stack:** FastAPI + Jinja2 templates + Google OAuth + PostgreSQL + AI providers (Gemini/DeepSeek)

## Critical Instructions

**⚠️ NEVER CREATE SUMMARY MARKDOWN FILES**: Do not create `.md` files documenting changes, summaries, or work completed unless explicitly requested by the user. This wastes tokens and clutters the workspace.

## Architecture & Key Components

**Module-First Architecture (Hexagonal + Domain-Driven Design)**

Mimo uses a **module-first architecture** where each bounded context (tax_calculation, recommendations, multi_agent, auth) is organized as an independent module with hexagonal layers inside:

```
src/
├── tax_calculation/          # Tax calculation bounded context
│   ├── domain/               # Business logic (entities, services, value objects)
│   ├── application/          # Use cases (orchestration)
│   └── infrastructure/
│       └── api/              # REST adapter (tax_router.py)
├── recommendations/          # AI recommendations bounded context
│   ├── domain/               # Recommendation domain logic
│   ├── application/          # Recommendation use cases
│   └── infrastructure/
│       ├── api/              # REST adapter (recommendations_router.py)
│       ├── providers/        # AI provider adapters (driven ports)
│       └── prompts/          # Prompt templates
├── auth/                     # Authentication bounded context (infrastructure-only)
│   └── infrastructure/
│       ├── api/              # REST adapter (auth_router.py)
│       ├── oauth_service.py  # Google OAuth service
│       └── dependencies.py   # Auth dependencies
└── shared/                   # Shared kernel (cross-cutting concerns)
    ├── domain/
    │   ├── constants/        # ISR tables, tax constants
    │   └── value_objects/    # Shared value objects
    └── infrastructure/
        ├── api/              # Middleware, schemas
        ├── config/           # Settings, dependency injection
        ├── logging/          # Structured logger
        └── persistence/      # Database repositories (PostgreSQL in prod, SQLite in tests)
```

**Key Principles:**

- **Hexagonal Architecture:** Domain at center, application layer for use cases, infrastructure for adapters (both driving like REST API and driven like databases/AI providers)
- **Module Independence:** Each module has clear boundaries and minimal coupling
- **Import Rules:** Always import from specific modules, NEVER use `__init__.py` for exports
  - ✅ `from src.tax_calculation.domain.entities.tax_calculation import TaxCalculation`
  - ❌ `from src.tax_calculation.domain import TaxCalculation` (don't populate `__init__.py`)
- **Shared Kernel:** Common code (ISR tables, config, logging, persistence) in `shared/` module

### 1. Tax Calculation Module (`src/tax_calculation/`)

- **Domain Layer:**
  - `TaxCalculationService`: Core calculator implementing Mexican ISR (Impuesto Sobre la Renta) rules
    - Computes taxable bonus/vacation premium with UMA-based exemptions
    - Applies deduction caps: 5 UMAs OR 15% of gross income (whichever is lower)
    - Uses monthly ISR tax brackets from shared `isr_tables`
  - `TaxCalculation`: Domain entity with validation and helper methods
  - `TaxpayerInfo`, `IncomeData`, `DeductionData`: Value objects
- **Application Layer:**
  - `CalculateTaxUseCase`: Orchestrates tax calculation flow
- **Infrastructure Layer:**
  - `tax_router.py`: REST API adapter (driving port)
- **Data Flow:** User input → Validation → Use Case → Domain Service → Entity → JSON response

- **Data Flow:** User input → Validation → Use Case → Domain Service → Entity → JSON response

### 2. Shared Module (`src/shared/`)

**Domain Layer:**

- **ISR Tax Tables** (`shared/domain/constants/isr_tables.py`):
  - Hardcoded constants (no JSON files at runtime) for fiscal years 2024-2025
  - Contains UMA values, exemption limits, deduction caps, tuition limits per education level
  - Access via: `get_tabla_isr(fiscal_year)` returns `TablaISR` dataclass
  - Monthly tax brackets with cuota_fija and porcentaje_excedente for progressive taxation

**Infrastructure Layer:**

- **API Schemas** (`shared/infrastructure/api/schemas/`): Request/response models for all endpoints
- **Middleware** (`shared/infrastructure/api/middleware/`): Error handlers, logging middleware
- **Config** (`shared/infrastructure/config/`): Settings, dependency injection container
- **Logging** (`shared/infrastructure/logging/`): Structured logger (JSON in prod, readable in dev)
- **Persistence** (`shared/infrastructure/persistence/`): Database repositories for usage tracking (PostgreSQL in production, SQLite for tests)

### 3. Recommendations Module (`src/recommendations/`)

- **AI Recommendations & Multi-Provider System:**
  - **Provider Factory:** Prioritizes Claude Sonnet 4.5 (Anthropic) → DeepSeek → Gemini → Fallback
  - **Strategy Pattern:** `RecommendationProvider` interface with 4 implementations:
    - `ClaudeRecommendationAdapter` (preferred, streaming via Anthropic SDK, model: `claude-sonnet-4.5`)
    - `DeepSeekRecommendationAdapter` (OpenAI-compatible API)
    - `GeminiRecommendationAdapter` (Google Gemini API)
    - `FallbackRecommendationAdapter` (static markdown recommendations)
  - **Prompt Templates:** `infrastructure/prompts/recommendation_prompts.py`
  - **Personality:** Recommendations must include cat puns ("purr-fecto", "gat-rantizo") and time-based greetings
  - **Critical:** Never recommend maxed-out deductions; always check current values vs official limits
- **Application Layer:**
  - `GenerateRecommendationsUseCase`: Orchestrates recommendation generation with rate limiting
- **Infrastructure Layer:**
  - `recommendations_router.py`: REST API adapter
  - `providers/`: AI provider implementations (driven adapters)

  - `providers/`: AI provider implementations (driven adapters)

### 4. Auth Module (`src/auth/`)

- **Infrastructure-only module** (no domain/application layers - pure infrastructure concern)
- **Google OAuth 2.0:** `/auth/google` → `/auth/callback` stores user in session
- **Railway/Proxy-aware:** `get_effective_redirect_uri()` uses `X-Forwarded-Proto` and `X-Forwarded-Host` headers
- **Daily limits:** PostgreSQL tracks `recommendation_usage` per user_id per date (default: 3/day, configurable via `DAILY_RECOMMENDATIONS_LIMIT`)
- User ID: `user["sub"]` (Google's unique identifier) or falls back to email
- Usage tracking: Increment AFTER successful generation, not before (prevents charging for failures)
- **Infrastructure Layer:**
  - `auth_router.py`: REST API adapter
  - `oauth_service.py`: Google OAuth service
  - `dependencies.py`: Auth dependencies (get_user_id, get_current_user)

## Development Workflows

### Running the Server

```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

- Uses **uv** (fast Python package manager) - not pip!
- FastAPI auto-reload enabled for development
- Access at `http://localhost:8000/calculator`

### Environment Variables Required

```bash
# OAuth (required for AI recommendations)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=  # Can be omitted; auto-detected in production

# Session security
SECRET_KEY=  # For SessionMiddleware

# AI Providers (at least one required for AI recommendations)
DEEPSEEK_API_KEY=  # Preferred
GEMINI_API_KEY=    # Fallback

# Optional overrides
DAILY_RECOMMENDATIONS_LIMIT=3  # Default
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TEMPERATURE=0.6
```

### Database

- **PostgreSQL** (production) - Requires `DATABASE_URL` environment variable
- **SQLite** (tests only) - Used in integration tests for repository testing
- Single table: `recommendation_usage (user_id TEXT, date TEXT, count INTEGER)`
- Schema auto-initializes via `initialize_database()` on startup

### Project-Specific Conventions

#### Mexican Tax Domain Knowledge

- **UMA** (Unidad de Medida y Actualización): Official Mexican unit for calculating tax limits
  - Example: 5 UMAs ≈ $198,031.80 for general deductions in 2024
- **Aguinaldo** (Christmas bonus): Partially exempt up to 30 UMAs daily
- **Prima vacacional** (vacation premium): Partially exempt up to 15 UMAs daily
- **Deduction hierarchy:** Personal → PPR → Education, then apply 5 UMA / 15% cap proportionally
- **Prompt-driven logic:** All AI/agent output is controlled by prompt templates in `prompts.py` and `multi_agent_prompts.py` (no hardcoded logic in adapters)
- **Model selection:**
  - **Production:** Use Claude Sonnet 4.5 (Anthropic) for all agents and single-agent recommendations (best for compliance, reasoning, and Spanish)
  - **Fallback:** Use DeepSeek (OpenAI-compatible) or GPT-4.1 (0x) for cost-sensitive or free-tier scenarios
  - **LiteLLM:** All model routing is handled via `LiteLLMAdapter` and `AgentModelConfig` (see `multi_agent_prompts.py`)
  - **Extensible:** Add new models/providers by updating `DEFAULT_AGENT_MODELS` and `.env` API keys

### API Response Patterns

- **Tax calculation:** Standard JSON with all fields from `TaxCalculationResult`
- **Recommendations:**
  - `/api/recommendations/stream` - Server-Sent Events (SSE) with chunks: `{"type":"chunk","content":"..."}` then `{"type":"complete","markdown":"..."}`
- **Usage tracking:** Always increment AFTER successful generation, not before
- **Model info:** Each response includes which model/provider was used (for auditability)

### Error Handling

- AI failures return **fallback recommendations** (list of generic tips), NOT errors
- Google OAuth clock skew tolerance: 10 seconds (`clock_skew_in_seconds=10`)
- 401 errors require login, 429 for rate limiting

### Code Style & Architecture Principles

**CRITICAL: All code MUST be written in English** (variables, functions, classes, comments)

**SOLID Principles (Mandatory):**

- **Single Responsibility:** Each class/function has ONE clear purpose
  - Example: `TaxCalculator` only calculates taxes, `RecommendationProvider` only generates recommendations, `LiteLLMAdapter` only handles model routing
- **Open/Closed:** Extend via interfaces, not modification
  - Example: Add new AI providers by implementing `RecommendationProvider` or updating `AgentModelConfig`, not editing existing adapters
- **Liskov Substitution:** All `RecommendationProvider` and agent adapters are interchangeable
- **Interface Segregation:** Use ABC/Protocol for clean contracts
  - Example: `RecommendationProvider` and `LiteLLMAdapter` define streaming interface
- **Dependency Inversion:** Depend on abstractions, not concrete implementations
  - Example: `RecommendationService` depends on `RecommendationProvider` interface, not specific adapters

**Code Quality:**

- **Minimal comments:** Code should be self-documenting through clear naming
  - ❌ Avoid: `# Calculate tax` before obvious calculation
  - ✅ Only comment: Complex business logic, non-obvious tax rules, "why" not "what"
- **Type hints required:** `Dict[str, Any]`, `Optional[X]`, `Generator[str, None, None]`, etc.
- **Pydantic models:** All API inputs/outputs with `model_config` examples
- **Naming conventions:**
  - Constants: `SCREAMING_SNAKE_CASE`
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Private methods: `_leading_underscore`
- **`__init__.py` files:** Must be completely empty
  - ❌ Never add imports, exports, or `__all__` declarations
  - ✅ Always import directly from the module: `from src.shared.domain.constants.isr_tables import get_tabla_isr`
  - ✅ Example for tax module: `from src.tax_calculation.domain.entities.tax_calculation import TaxCalculation`
  - ✅ Example for router: `from src.tax_calculation.infrastructure.api.tax_router import router as tax_router`
  - Reason: Explicit imports are clearer and avoid circular dependency issues
- **Prompt-driven:** All AI/agent output is controlled by prompt templates (never hardcoded in adapters)
- **Model extensibility:** Add new models/providers by updating `AgentModelConfig` and `.env` API keys; no code changes required in adapters

## Key Files Reference

- `src/main.py` - Main FastAPI app entry point
  - All routers imported directly: `from src.{module}.infrastructure.api.{router} import router`
  - Lifespan context manager handles startup/shutdown
- `src/tax_calculation/domain/services/tax_calculation_service.py` - Tax calculation business logic
  - Implements Mexican ISR rules with UMA-based exemptions
- `src/tax_calculation/application/calculate_tax_use_case.py` - Tax calculation use case
  - Orchestrates tax calculation flow with TaxCalculationService
- `src/tax_calculation/infrastructure/api/tax_router.py` - Tax API endpoints
  - `/api/calculate` endpoint for tax calculations
- `src/recommendations/infrastructure/api/recommendations_router.py` - Recommendations API
  - `/api/recommendations/stream` for AI recommendations
- `src/auth/infrastructure/api/auth_router.py` - OAuth endpoints
  - `/auth/google`, `/auth/callback`, `/auth/logout`, `/auth/status`
- `src/shared/domain/constants/isr_tables.py` - Tax tables and constants
  - Hardcoded fiscal data for 2024-2025 (no runtime JSON files)
  - Access via `get_tabla_isr(fiscal_year)` returns `TablaISR` dataclass
- `src/shared/infrastructure/config/settings.py` - Application settings
  - Pydantic settings with environment variable loading
- `src/shared/infrastructure/config/dependency_injection.py` - DI container
  - Provides use cases and repositories with proper dependency injection
- `templates/calculator.html` - Single-page calculator UI with HTMX
- `pyproject.toml` - Dependencies managed by **uv** (not pip)

## Testing & Debugging

- **Comprehensive test suite** exists in `tests/` (300+ tests)
  - `tests/integration/`: Full API request/response cycle tests (tax router, rate limiting)
  - `tests/unit/`: Domain logic tests (tax calculation, prompts, providers)
  - Run all: `uv run pytest tests/ -v`
  - Run specific: `uv run pytest tests/integration/test_tax_router.py -v`
- Manual testing via web UI at `/calculator`
- Check AI recommendations with test user data: monthly income $12,600 → annual ~$151,200
- Debug rate limiting: Query PostgreSQL directly or use `/api/recommendations/usage` endpoint
- Railway deployment: Verify `X-Forwarded-*` headers in OAuth redirects

## Common Tasks

**Add a new fiscal year:**

1. Add constants to `src/shared/domain/constants/isr_tables.py` (UMA values, tax brackets)
2. Update `TABLAS_ISR` dict
3. Update `fiscal_year` Field validation in schemas (ge/le range)

**Modify AI prompt behavior:**

- Edit prompt builders in `src/recommendations/infrastructure/prompts/recommendation_prompts.py`
- Test with streaming endpoint to see real-time output
- Remember: Must include cat personality and time-based greetings

**Add new deduction type:**

1. Add field to `TaxpayerInfo`/`IncomeData`/`DeductionData` in `src/tax_calculation/domain/value_objects/tax_data.py`
2. Modify `_calculate_authorized_deductions()` in `src/tax_calculation/domain/services/tax_calculation_service.py`
3. Update prompts to mention new deduction
4. Add corresponding field in `src/shared/infrastructure/api/schemas/tax_schemas.py`
5. Add input field in `templates/calculator.html`

**Change rate limiting:**

- Set `DAILY_RECOMMENDATIONS_LIMIT` env var (no code changes needed)
- For per-feature limits, modify repository in `src/shared/infrastructure/persistence/`

**Add new AI provider (for single-agent recommendations):**

1. Create new adapter implementing `RecommendationProvider` in `src/recommendations/infrastructure/providers/`
2. Implement `generate_recommendations_stream()` method (must be a generator)
3. Update provider factory in dependency injection
4. Add required API key to environment variables
5. Follow existing patterns: DeepSeek/Gemini/Claude implementations as reference
