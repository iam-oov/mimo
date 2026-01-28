import asyncio

import httpx

try:
    import anthropic
except ImportError:
    anthropic = None  # type: ignore

try:
    from google import genai
except ImportError:
    genai = None  # type: ignore

from src.shared.domain.exceptions import ConfigurationError
from src.shared.infrastructure.config.settings import Settings
from src.shared.infrastructure.logging.structured_logger import get_logger

logger = get_logger(__name__)


async def validate_api_keys(settings: Settings) -> None:
    """
    Validate all configured API keys work.

    Tests each configured AI provider with a minimal request to ensure:
    - API key is valid
    - API endpoint is reachable
    - Provider service is operational

    Args:
        settings: Application settings with API keys

    Raises:
        ConfigurationError: If any configured API key is invalid or provider is unreachable

    Note:
        Only validates configured providers. If a provider is not configured
        (API key is None), it is skipped.
    """
    validation_errors: list[str] = []
    validated_providers: list[str] = []

    # Validate Anthropic Claude (preferred provider)
    if settings.has_anthropic_configured():
        try:
            await _validate_anthropic(settings)
            validated_providers.append("Anthropic Claude")
            logger.info(
                "✅ Anthropic API key validated",
                model=settings.anthropic_model,
            )
        except Exception as e:
            error_msg = f"Anthropic API key invalid or service unavailable: {str(e)}"
            validation_errors.append(error_msg)
            logger.error(
                "❌ Anthropic validation failed",
                error=str(e),
                model=settings.anthropic_model,
            )

    # Validate DeepSeek
    if settings.has_deepseek_configured():
        try:
            await _validate_deepseek(settings)
            validated_providers.append("DeepSeek")
            logger.info(
                "✅ DeepSeek API key validated",
                model=settings.deepseek_model,
            )
        except Exception as e:
            error_msg = f"DeepSeek API key invalid or service unavailable: {str(e)}"
            validation_errors.append(error_msg)
            logger.error(
                "❌ DeepSeek validation failed",
                error=str(e),
                model=settings.deepseek_model,
            )

    # Validate Gemini
    if settings.has_gemini_configured():
        try:
            await _validate_gemini(settings)
            validated_providers.append("Google Gemini")
            logger.info(
                "✅ Gemini API key validated",
                model=settings.gemini_model,
            )
        except Exception as e:
            error_msg = f"Gemini API key invalid or service unavailable: {str(e)}"
            validation_errors.append(error_msg)
            logger.error(
                "❌ Gemini validation failed",
                error=str(e),
                model=settings.gemini_model,
            )

    # Validate OpenAI
    if settings.has_openai_configured():
        try:
            await _validate_openai(settings)
            validated_providers.append("OpenAI")
            logger.info(
                "✅ OpenAI API key validated",
                model=settings.openai_model,
            )
        except Exception as e:
            error_msg = f"OpenAI API key invalid or service unavailable: {str(e)}"
            validation_errors.append(error_msg)
            logger.error(
                "❌ OpenAI validation failed",
                error=str(e),
                model=settings.openai_model,
            )

    # If ALL configured providers failed, raise error
    if validation_errors and not validated_providers:
        error_summary = "\n".join(f"  - {err}" for err in validation_errors)
        raise ConfigurationError(
            message="No AI providers available. Please check API keys.",
            internal_details=f"All API key validations failed:\n{error_summary}",
        )

    # If some providers failed but at least one works, log warning
    if validation_errors:
        logger.warning(
            "⚠️ Some AI providers failed validation",
            failed_count=len(validation_errors),
            validated_providers=validated_providers,
            errors=validation_errors,
        )
    else:
        logger.info(
            "✅ All configured AI providers validated",
            providers=validated_providers,
        )


async def _validate_anthropic(settings: Settings) -> None:
    """
    Validate Anthropic Claude API key with minimal request.

    Args:
        settings: Application settings

    Raises:
        Exception: If validation fails
    """
    if anthropic is None:
        raise ImportError("anthropic package not installed")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    # Minimal test request (uses very few tokens)
    # Anthropic SDK is sync, so we run in executor to avoid blocking
    await asyncio.to_thread(
        lambda: client.messages.create(
            model=settings.anthropic_model,
            max_tokens=5,
            messages=[{"role": "user", "content": "test"}],
        )
    )


async def _validate_deepseek(settings: Settings) -> None:
    """
    Validate DeepSeek API key with minimal request.

    Args:
        settings: Application settings

    Raises:
        Exception: If validation fails
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{settings.deepseek_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.deepseek_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.deepseek_model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 5,
            },
        )
        response.raise_for_status()


async def _validate_gemini(settings: Settings) -> None:
    """
    Validate Google Gemini API key with minimal request.

    Args:
        settings: Application settings

    Raises:
        Exception: If validation fails
    """
    if genai is None:
        raise ImportError("google-genai package not installed")

    client = genai.Client(api_key=settings.gemini_api_key)

    # Minimal test request (new API is async-compatible)
    response = await asyncio.to_thread(
        lambda: client.models.generate_content(
            model=settings.gemini_model,
            contents="test",
            config=genai.types.GenerateContentConfig(
                max_output_tokens=5,
                temperature=settings.gemini_temperature,
            ),
        )
    )

    # Verify response is valid
    _ = response.text


async def _validate_openai(settings: Settings) -> None:
    """
    Validate OpenAI API key with minimal request.

    Args:
        settings: Application settings

    Raises:
        Exception: If validation fails
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.openai_model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 5,
            },
        )
        response.raise_for_status()
