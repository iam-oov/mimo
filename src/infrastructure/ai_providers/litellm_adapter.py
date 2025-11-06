"""
LiteLLM adapter for unified multi-model support.
Allows each agent to use different AI providers seamlessly.
"""

from typing import Generator, Optional
import logging
import os

from src.infrastructure.ai_providers.multi_agent_prompts import AgentModelConfig

logger = logging.getLogger(__name__)


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
        self._setup_api_keys()

    def _setup_api_keys(self):
        """
        Setup API keys for different providers.
        LiteLLM uses standard environment variables.
        """
        # Map provider to required env variable
        provider_env_map = {
            "deepseek": "DEEPSEEK_API_KEY",
            "openai": "OPENAI_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
        }

        provider = self.model_config.provider
        env_var = provider_env_map.get(provider)

        if env_var and not os.getenv(env_var):
            logger.warning(
                f"API key for {provider} not found in environment variable {env_var}"
            )

        # Set DeepSeek base URL if using DeepSeek
        if provider == "deepseek":
            if not os.getenv("DEEPSEEK_BASE_URL"):
                os.environ["DEEPSEEK_BASE_URL"] = "https://api.deepseek.com"

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
                f"LiteLLM generation error with {self.model_config.provider}/{self.model_config.model}: {e}"
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
                f"LiteLLM generation error with {self.model_config.provider}/{self.model_config.model}: {e}"
            )
            raise

    def is_available(self) -> bool:
        """
        Check if the configured provider is available.

        Returns:
            True if API key exists for the provider
        """
        provider_env_map = {
            "deepseek": "DEEPSEEK_API_KEY",
            "openai": "OPENAI_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
        }

        env_var = provider_env_map.get(self.model_config.provider)
        if env_var:
            return bool(os.getenv(env_var))

        # Unknown provider, assume available
        return True

    def get_model_info(self) -> str:
        """
        Get human-readable model information.

        Returns:
            Model info string
        """
        return f"{self.model_config.provider}/{self.model_config.model} (temp={self.model_config.temperature})"


def create_agent_adapter(agent_id: str) -> Optional[LiteLLMAdapter]:
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
    from src.infrastructure.ai_providers.multi_agent_prompts import (
        get_agent_model_config,
    )

    model_config = get_agent_model_config(agent_id)

    if not model_config:
        logger.error(f"No model configuration found for agent: {agent_id}")
        return None

    adapter = LiteLLMAdapter(model_config)

    if not adapter.is_available():
        logger.warning(
            f"Provider {model_config.provider} not available for agent {agent_id}"
        )
        return None

    logger.info(f"Created adapter for {agent_id}: {adapter.get_model_info()}")
    return adapter
