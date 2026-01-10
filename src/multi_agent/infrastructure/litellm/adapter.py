"""
LiteLLM adapter for unified multi-model support.
Allows each agent to use different AI providers seamlessly.
"""

import os
from collections.abc import Generator

from src.multi_agent.infrastructure.prompts.multi_agent_prompts import AgentModelConfig
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.logging.structured_logger import StructuredLogger

logger = StructuredLogger(__name__)


class LiteLLMAdapter:
    """
    Unified adapter for multiple AI providers using LiteLLM.
    Supports DeepSeek, OpenAI, Gemini, Anthropic, and more.
    """

    def __init__(self, model_config: AgentModelConfig):
        """
        Initialize LiteLLM adapter with model configuration.

        Args:
            model_config: Configuration specifying provider, model, and parameters
        """
        self.model_config = model_config
        self._settings = get_settings()
        self._setup_api_keys()

    def _setup_api_keys(self):
        """
        Setup API keys for different providers using project settings.
        Exports keys to environment variables for LiteLLM to use.
        """
        # Export API keys from settings to environment variables for LiteLLM
        if self._settings.deepseek_api_key:
            os.environ["DEEPSEEK_API_KEY"] = self._settings.deepseek_api_key
        if self._settings.gemini_api_key:
            os.environ["GEMINI_API_KEY"] = self._settings.gemini_api_key
        if self._settings.anthropic_api_key:
            os.environ["ANTHROPIC_API_KEY"] = self._settings.anthropic_api_key

        # Set DeepSeek base URL
        if self._settings.deepseek_base_url:
            os.environ["DEEPSEEK_BASE_URL"] = self._settings.deepseek_base_url

    def _get_api_key_for_provider(self, provider: str) -> str | None:
        """Get API key for provider from settings."""
        provider_key_map = {
            "deepseek": self._settings.deepseek_api_key,
            "gemini": self._settings.gemini_api_key,
            "anthropic": self._settings.anthropic_api_key,
            "openai": os.getenv("OPENAI_API_KEY"),  # OpenAI not in settings yet
        }
        return provider_key_map.get(provider)

    def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> Generator[str, None, None]:
        """
        Generate streaming response using LiteLLM.

        Args:
            system_prompt: System prompt defining agent behavior
            user_prompt: User prompt with task/question

        Yields:
            Content chunks from the AI response

        Raises:
            Exception: If generation fails
        """
        try:
            import litellm

            # Configure LiteLLM settings
            litellm.drop_params = True  # Drop unsupported params instead of failing
            litellm.set_verbose = False  # Disable verbose logging

            # Build messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            # Get LiteLLM model string
            model = self.model_config.to_litellm_model()

            # Stream completion
            response = litellm.completion(
                model=model,
                messages=messages,
                temperature=self.model_config.temperature,
                max_tokens=self.model_config.max_tokens,
                stream=True,
            )

            # Yield content chunks
            for chunk in response:
                if hasattr(chunk, "choices") and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        yield delta.content

        except Exception as e:
            logger.error(
                "❌ LiteLLM streaming generation failed",
                provider=self.model_config.provider,
                model=self.model_config.model,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """
        Generate complete response using LiteLLM (non-streaming).

        Args:
            system_prompt: System prompt defining agent behavior
            user_prompt: User prompt with task/question

        Returns:
            Complete AI response

        Raises:
            Exception: If generation fails
        """
        try:
            import litellm

            # Configure LiteLLM settings
            litellm.drop_params = True
            litellm.set_verbose = False

            # Build messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            # Get LiteLLM model string
            model = self.model_config.to_litellm_model()

            # Complete generation
            response = litellm.completion(
                model=model,
                messages=messages,
                temperature=self.model_config.temperature,
                max_tokens=self.model_config.max_tokens,
                stream=False,
            )

            # Extract content
            if hasattr(response, "choices") and len(response.choices) > 0:
                return response.choices[0].message.content or ""

            return ""

        except Exception as e:
            logger.error(
                "❌ LiteLLM non-streaming generation failed",
                provider=self.model_config.provider,
                model=self.model_config.model,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise

    def is_available(self) -> bool:
        """
        Check if the configured provider is available.

        Returns:
            True if API key exists for the provider
        """
        api_key = self._get_api_key_for_provider(self.model_config.provider)

        if not api_key:
            logger.warning(
                "⚠️ API key missing for provider",
                provider=self.model_config.provider,
                model=self.model_config.model,
            )
            return False

        return True

    def get_model_info(self) -> str:
        """
        Get human-readable model information.

        Returns:
            Model info string
        """
        return f"{self.model_config.provider}/{self.model_config.model} (temp={self.model_config.temperature})"


def create_agent_adapter(agent_id: str) -> LiteLLMAdapter | None:
    """
    Create LiteLLM adapter for specific agent.

    Args:
        agent_id: Agent identifier (e.g., 'agent_1', 'agent_2', 'moderator')

    Returns:
        Configured LiteLLMAdapter or None if configuration missing

    Example:
        >>> adapter = create_agent_adapter('agent_1')
        >>> response = adapter.generate_stream(system_prompt, user_prompt)
    """
    from src.multi_agent.infrastructure.prompts.multi_agent_prompts import (
        get_agent_model_config,
    )

    model_config = get_agent_model_config(agent_id)

    if not model_config:
        logger.error(
            "❌ No model configuration found for agent",
            agent_id=agent_id,
        )
        return None

    adapter = LiteLLMAdapter(model_config)

    if not adapter.is_available():
        logger.error(
            "❌ Provider not available - API key missing",
            agent_id=agent_id,
            provider=model_config.provider,
            model=model_config.model,
            required_env_var=f"{model_config.provider.upper()}_API_KEY",
        )
        return None

    logger.info(
        "✅ Created adapter for agent",
        agent_id=agent_id,
        provider=model_config.provider,
        model=model_config.model,
    )
    return adapter
