# Mimo - Calculadora de Saldo a Favor ISR

## Project Overview

Mimo is a **Mexican tax calculator** for individuals (personas físicas) that computes annual tax balance (saldo a favor/a pagar) and generates AI-powered personalized fiscal recommendations through "Mimo el Gatito Fiscal" 🐱 - a cat-themed tax advisor.

**Tech Stack:** FastAPI + Jinja2 templates + Google OAuth + SQLite + AI providers (Gemini/DeepSeek)

## Critical Instructions

**⚠️ NEVER CREATE SUMMARY MARKDOWN FILES**: Do not create `.md` files documenting changes, summaries, or work completed unless explicitly requested by the user. This wastes tokens and clutters the workspace.

## Architecture & Key Components

### 1. Tax Calculation Engine (`server.py`)

- **`TaxCalculator`**: Core calculator implementing Mexican ISR (Impuesto Sobre la Renta) rules
  - Computes taxable bonus/vacation premium with UMA-based exemptions
  - Applies deduction caps: 5 UMAs OR 15% of gross income (whichever is lower)
  - Uses monthly ISR tax brackets from `tabla_isr_constants.py`
- **`TaxCalculationResult`**: Pydantic model with validation and helper methods (`get_effective_tax_rate()`, `is_refund_due()`)
- **Data Flow:** User input → `TaxInputData` validation → `TaxCalculator` → `TaxCalculationResult` → JSON response

### 2. ISR Tax Tables (`tabla_isr_constants.py`)

- **Hardcoded constants** (no JSON files at runtime) for fiscal years 2024-2025
- Contains UMA values, exemption limits, deduction caps, tuition limits per education level
- Access via: `get_tabla_isr(fiscal_year)` returns `TablaISR` dataclass
- **Monthly tax brackets** with cuota_fija and porcentaje_excedente for progressive taxation

### 3. AI Recommendations (`fiscal_recommendations.py`)

- **Factory Pattern:** `RecommendationFactory.create_service()` prioritizes DeepSeek → Gemini → Fallback
- **Strategy Pattern:** `RecommendationGenerator` interface with 3 implementations:
  - `DeepSeekRecommendationGenerator` (preferred, streaming via OpenAI-compatible API)
  - `GeminiRecommendationGenerator` (fallback, uses `google.generativeai`)
  - `FallbackRecommendationGenerator` (static markdown recommendations)
- **Shared prompt building:** `build_prompt()` creates detailed prompts with exact UMA calculations and limits
- **Personality:** Recommendations must include cat puns ("purr-fecto", "gat-rantizo") and greetings based on time of day
- **Critical:** Must avoid recommending maxed-out deductions by checking current values against official limits

### 4. Authentication & Rate Limiting (`server.py`)

- **Google OAuth 2.0:** `/auth/google` → `/auth/callback` stores user in session
- **Railway/Proxy-aware:** `get_effective_redirect_uri()` uses `X-Forwarded-Proto` and `X-Forwarded-Host` headers
- **Daily limits:** SQLite tracks `recommendation_usage` per user_id per date (default: 3/day, configurable via `DAILY_RECOMMENDATIONS_LIMIT`)
- User ID: `user["sub"]` (Google's unique identifier) or falls back to email

### 5. Reference Files (Not Part of Main App)

- **`dynamic_conversation.py`:** Personal reference/guide file demonstrating SOLID principles
  - Shows Protocol-based abstractions, factory pattern, dependency injection
  - **DO NOT MODIFY** or reference in main application code
  - Use as inspiration for architecture patterns only

## Development Workflows

### Running the Server

```bash
uv run uvicorn server:app --host 0.0.0.0 --port 8000 --reload
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

- **SQLite** (`recommendations.db`) auto-initializes on startup via `initialize_database()`
- Single table: `recommendation_usage (user_id TEXT, date TEXT, count INTEGER)`
- No migrations - schema created if not exists

## Project-Specific Conventions

### Mexican Tax Domain Knowledge

- **UMA** (Unidad de Medida y Actualización): Official Mexican unit for calculating tax limits
  - Example: 5 UMAs ≈ $198,031.80 for general deductions in 2024
- **Aguinaldo** (Christmas bonus): Partially exempt up to 30 UMAs daily
- **Prima vacacional** (vacation premium): Partially exempt up to 15 UMAs daily
- **Deduction hierarchy:** Personal → PPR → Education, then apply 5 UMA / 15% cap proportionally

### API Response Patterns

- **Tax calculation:** Standard JSON with all fields from `TaxCalculationResult`
- **Recommendations:** Two modes:
  1. `/api/recommendations` - Accumulates full response, returns `recommendations_markdown` + `usage_info`
  2. `/api/recommendations/stream` - Server-Sent Events (SSE) with chunks: `{"type":"chunk","content":"..."}` then `{"type":"complete","markdown":"..."}`
- **Usage tracking:** Always increment AFTER successful generation, not before

### Error Handling

- AI failures return **fallback recommendations** (list of generic tips), NOT errors
- Google OAuth clock skew tolerance: 10 seconds (`clock_skew_in_seconds=10`)
- 401 errors require login, 429 for rate limiting

### Code Style & Architecture Principles

**CRITICAL: All code MUST be written in English** (variables, functions, classes, comments)

**SOLID Principles (Mandatory):**

- **Single Responsibility:** Each class/function has ONE clear purpose
  - Example: `TaxCalculator` only calculates taxes, `RecommendationGenerator` only generates recommendations
- **Open/Closed:** Extend via interfaces, not modification
  - Example: Add new AI providers by implementing `RecommendationGenerator`, not editing existing ones
- **Liskov Substitution:** All `RecommendationGenerator` implementations are interchangeable
- **Interface Segregation:** Use ABC/Protocol for clean contracts
  - Example: `RecommendationGenerator` abstract class defines streaming interface
- **Dependency Inversion:** Depend on abstractions, not concrete implementations
  - Example: `RecommendationService` depends on `RecommendationGenerator` interface, not specific providers

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

## Key Files Reference

- `server.py` - Main FastAPI app with all endpoints (861 lines)
- `tabla_isr_constants.py` - Tax tables and constants (170 lines)
- `fiscal_recommendations.py` - AI recommendation system (597 lines)
- `templates/calculator.html` - Single-page calculator UI
- `pyproject.toml` - Defines dependencies (uses uv for package management)
- `dynamic_conversation.py` - **Personal reference guide only** (ignore for main project)

## Testing & Debugging

- No tests currently exist
- Manual testing via web UI at `/calculator`
- Check AI recommendations with test user data: monthly income $12,600 → annual ~$151,200
- Debug rate limiting: Query `recommendations.db` directly or use `/api/recommendations/usage` endpoint
- Railway deployment: Verify `X-Forwarded-*` headers in OAuth redirects

## Common Tasks

**Add a new fiscal year:**

1. Add constants to `tabla_isr_constants.py` (UMA values, tax brackets)
2. Update `TABLAS_ISR` dict
3. Update `fiscal_year` Field validation in `TaxInputData` (ge/le range)

**Modify AI prompt behavior:**

- Edit `build_prompt()` in `fiscal_recommendations.py` (shared by all providers)
- Test with streaming endpoint to see real-time output
- Remember: Must include cat personality and time-based greetings

**Add new deduction type:**

1. Add field to `TaxInputData` Pydantic model
2. Modify `_calculate_authorized_deductions()` in `TaxCalculator`
3. Update prompt in `build_prompt()` to mention new deduction
4. Add corresponding input field in `calculator.html`

**Change rate limiting:**

- Set `DAILY_RECOMMENDATIONS_LIMIT` env var (no code changes needed)
- For per-feature limits, modify `get_user_recommendation_usage()` to accept scope parameter

**Add new AI provider:**

1. Create new class implementing `RecommendationGenerator` ABC in `fiscal_recommendations.py`
2. Implement `generate_recommendations_stream()` method (must be a generator)
3. Update `RecommendationFactory.create_service()` to include new provider in priority chain
4. Add required API key to environment variables
5. Follow existing patterns: DeepSeek/Gemini implementations as reference
