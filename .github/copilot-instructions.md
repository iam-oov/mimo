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

### 3. AI Recommendations & Multi-Agent System (Hexagonal + LiteLLM)

- **Provider Factory:** `RecommendationFactory.create_service()` prioritizes Claude Sonnet 4.5 (Anthropic) → DeepSeek → Gemini → Fallback
- **Strategy Pattern:** `RecommendationProvider` interface with 4 implementations:
  - `ClaudeRecommendationAdapter` (preferred, streaming via Anthropic SDK, model: `claude-sonnet-4.5`)
  - `DeepSeekRecommendationAdapter` (OpenAI-compatible API)
  - `GeminiRecommendationAdapter` (Google Gemini API)
  - `FallbackRecommendationAdapter` (static markdown recommendations)
- **Prompt building:** `build_fiscal_recommendation_prompt()` in `prompts.py` (single-agent) and `multi_agent_prompts.py` (multi-agent) generate detailed, structured prompts with exact UMA calculations, deduction caps, and Markdown formatting
- **Personality:** Recommendations must include cat puns ("purr-fecto", "gat-rantizo") and time-based greetings for Mimo
- **Critical:** Never recommend maxed-out deductions; always check current values vs official limits
- **Model selection:** All adapters can be swapped via LiteLLM; default is Claude Sonnet 4.5 for production, DeepSeek for fallback, GPT-4.1 for cost-sensitive/free tier

### 4. Multi-Agent Analysis System (modular, prompt-driven, LiteLLM-ready)

- **Architecture:** 3 AI agents (configurable) with distinct personalities and professions debate tax optimization strategies
- **Personality Types:** Conservative, Aggressive, Analytical, Pragmatic, Innovative (see `Personality` enum in `multi_agent_prompts.py`)
- **Professions:** Auditor, Tax Planner, Accountant, Financial Advisor, Fiscal Lawyer, Business Consultant (see `Profession` enum)
- **Prompt System:**
  - Each agent gets a unique system prompt via `build_agent_system_prompt()` (combines personality, profession, and agent name)
  - Debate context built with `build_debate_context()` (fiscal data, deduction space, etc.)
  - Each round uses `build_round_prompt()` (initial, response, consensus)
  - Synthesis/final summary uses `build_synthesis_prompt()`
- **Model Routing:**
  - Each agent can use a different model/provider (DeepSeek, Claude, Gemini, OpenAI, etc.) via `AgentModelConfig` and `LiteLLMAdapter`
  - Default: All agents use Claude Sonnet 4.5 (Anthropic) for best reasoning and compliance; fallback to DeepSeek or GPT-4.1 for cost-sensitive scenarios
  - Model config per agent in `DEFAULT_AGENT_MODELS` (see `multi_agent_prompts.py`)
- **Debate Flow:**
  1. Round 1: Each agent proposes a strategy (150-250 chars, enforced by prompt)
  2. Round 2: Agents respond to others' proposals (no repetition, unique perspective)
  3. Round 3: Consensus & prioritization with voting
  4. Final synthesis with implementation roadmap (moderator agent)
- **Streaming:** All agent responses and synthesis are streamed (SSE)
- **Language Style:** Use simple, everyday language ("lo que pagas" not "base gravable"); avoid technical jargon
- **Extensibility:** Add new personalities/professions by updating enums and config dicts; add new models by updating `AgentModelConfig`

### 5. Authentication & Rate Limiting (`server.py`)

- **Google OAuth 2.0:** `/auth/google` → `/auth/callback` stores user in session
- **Railway/Proxy-aware:** `get_effective_redirect_uri()` uses `X-Forwarded-Proto` and `X-Forwarded-Host` headers
- **Daily limits:** SQLite tracks `recommendation_usage` per user_id per date (default: 3/day, configurable via `DAILY_RECOMMENDATIONS_LIMIT`)
- Rate limiting applies to BOTH `/api/recommendations` and `/api/multi-agent-analysis` endpoints
- User ID: `user["sub"]` (Google's unique identifier) or falls back to email
- Usage tracking: Increment AFTER successful generation, not before (prevents charging for failures)

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
  - `/api/multi-agent-analysis/stream` - SSE with events: `agent_intro`, `round_start`, `agent_turn`, `synthesis`, `complete`
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
- **Prompt-driven:** All AI/agent output is controlled by prompt templates (never hardcoded in adapters)
- **Model extensibility:** Add new models/providers by updating `AgentModelConfig` and `.env` API keys; no code changes required in adapters

## Key Files Reference

- `server.py` - Main FastAPI app with all endpoints (986 lines)
  - Tax calculation: `TaxCalculator`, `TaxCalculationResult`, `/api/calculate`
  - AI recommendations: `/api/recommendations`, `/api/recommendations/stream`
  - Multi-agent analysis: `/api/multi-agent-analysis` (Server-Sent Events)
  - OAuth: `/auth/google`, `/auth/callback`, `/logout`
- `tabla_isr_constants.py` - Tax tables and constants (170 lines)
  - Hardcoded fiscal data for 2024-2025 (no runtime JSON files)
  - Access via `get_tabla_isr(fiscal_year)` returns `TablaISR` dataclass
- `fiscal_recommendations.py` - Single-agent AI recommendation system (597 lines)
  - Factory + Strategy pattern with 3 providers (DeepSeek/Gemini/Fallback)
  - Shared prompt building via `build_prompt()`
- `multi_agent_analysis.py` - Multi-agent debate system (972 lines)
  - 3 agents with randomized personalities/professions
  - Streaming debate with rounds and synthesis
- `templates/calculator.html` - Single-page calculator UI with HTMX
- `pyproject.toml` - Dependencies managed by **uv** (not pip)

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

**Add new AI provider (for single-agent recommendations):**

1. Create new class implementing `RecommendationGenerator` ABC in `fiscal_recommendations.py`
2. Implement `generate_recommendations_stream()` method (must be a generator)
3. Update `RecommendationFactory.create_service()` to include new provider in priority chain
4. Add required API key to environment variables
5. Follow existing patterns: DeepSeek/Gemini implementations as reference

**Add new AI provider (for multi-agent analysis):**

1. Create new class implementing `LanguageModelProvider` ABC in `multi_agent_analysis.py`
2. Implement `generate_stream()` method (must be a generator)
3. Update `ModelProviderFactory.create()` to include new provider in fallback chain
4. Add required API key to environment variables
5. Follow existing patterns: DeepSeekProvider/GeminiProvider as reference

**Modify multi-agent debate structure:**

- Change number of agents: Modify `MultiAgentAnalysisService._create_agents()` method
- Add new personality types: Update `Personality` enum and `PERSONALITY_CONFIGS` dict
- Add new professions: Update `Profession` enum and `PROFESSION_CONFIGS` dict
- Adjust debate rounds: Modify `_run_debate_rounds()` method
- Change character limits: Set `DEBATE_MIN_CHARACTER` and `DEBATE_MAX_CHARACTER` env vars
