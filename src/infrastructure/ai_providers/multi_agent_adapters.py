"""
Multi-agent analysis adapters.
Direct implementations of DeepSeek and Gemini providers for multi-agent analysis.
"""

from typing import Generator, List, Dict
import logging

from src.domain.ports.ai_providers import MultiAgentProvider
from src.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)


def _convert_prompt_to_messages(prompt: str) -> List[Dict[str, str]]:
    """Convert a single prompt string to messages format."""
    return [{"role": "user", "content": prompt}]


class DeepSeekMultiAgentAdapter(MultiAgentProvider):
    """Adapter for DeepSeek multi-agent provider using OpenAI-compatible API."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = settings.deepseek_api_key
        self.model = settings.deepseek_model
        self.base_url = settings.deepseek_base_url

    def generate_stream(self, prompt: str) -> Generator[str, None, None]:
        """Generate streaming response from DeepSeek."""
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            messages = _convert_prompt_to_messages(prompt)

            stream = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.6,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"DeepSeek multi-agent generation error: {e}")
            raise

    def is_available(self) -> bool:
        """Check if DeepSeek is configured and available."""
        return self.settings.has_deepseek_configured()

    def get_model_name(self) -> str:
        """Return the model name for DeepSeek."""
        return self.settings.deepseek_model


class GeminiMultiAgentAdapter(MultiAgentProvider):
    """Adapter for Gemini multi-agent provider."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = settings.gemini_api_key

    def generate_stream(self, prompt: str) -> Generator[str, None, None]:
        """Generate streaming response from Gemini."""
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")

            # Extract content from messages format if needed
            if isinstance(prompt, str):
                content = prompt
            else:
                messages = _convert_prompt_to_messages(prompt)
                content = messages[0]["content"]

            response = model.generate_content(content, stream=True)

            for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Gemini multi-agent generation error: {e}")
            raise

    def is_available(self) -> bool:
        """Check if Gemini is configured and available."""
        return self.settings.has_gemini_configured()

    def get_model_name(self) -> str:
        """Return the model name for Gemini."""
        return "gemini-1.5-flash"
