"""
Tests for recommendation provider adapters.
"""

from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.recommendations.domain.ports.recommendation_provider import (
    RecommendationProvider,
)
from src.recommendations.infrastructure.providers.fallback_adapter import (
    FallbackRecommendationAdapter,
)


class TestRecommendationProviderInterface:
    """Tests for the RecommendationProvider ABC interface."""

    def test_interface_requires_generate_recommendations_stream(self):
        """Interface should require generate_recommendations_stream method."""

        class IncompleteProvider(RecommendationProvider):
            def is_available(self) -> bool:
                return True

            def get_provider_name(self) -> str:
                return "Incomplete"

        with pytest.raises(TypeError, match="generate_recommendations_stream"):
            IncompleteProvider()

    def test_interface_requires_is_available(self):
        """Interface should require is_available method."""

        class IncompleteProvider(RecommendationProvider):
            def generate_recommendations_stream(
                self, calculation_result: Any, user_data: dict, fiscal_year: int
            ) -> Generator[str, None, None]:
                yield "test"

            def get_provider_name(self) -> str:
                return "Incomplete"

        with pytest.raises(TypeError, match="is_available"):
            IncompleteProvider()

    def test_interface_requires_get_provider_name(self):
        """Interface should require get_provider_name method."""

        class IncompleteProvider(RecommendationProvider):
            def generate_recommendations_stream(
                self, calculation_result: Any, user_data: dict, fiscal_year: int
            ) -> Generator[str, None, None]:
                yield "test"

            def is_available(self) -> bool:
                return True

        with pytest.raises(TypeError, match="get_provider_name"):
            IncompleteProvider()


class TestFallbackRecommendationAdapter:
    """Tests for the FallbackRecommendationAdapter."""

    @pytest.fixture
    def adapter(self) -> FallbackRecommendationAdapter:
        return FallbackRecommendationAdapter()

    @pytest.fixture
    def sample_calculation(self):
        """Create a mock calculation result."""
        mock = MagicMock()
        mock.gross_annual_income = 200000.0
        mock.taxable_bonus = 5000.0
        mock.taxable_vacation_premium = 2000.0
        mock.determined_tax = 25000.0
        mock.withheld_tax = 28000.0
        mock.balance_in_favor = 3000.0
        return mock

    def test_fallback_is_always_available(self, adapter):
        """Fallback adapter should always be available."""
        assert adapter.is_available() is True

    def test_fallback_provider_name(self, adapter):
        """Fallback adapter should return correct name."""
        assert adapter.get_provider_name() == "Fallback"

    def test_fallback_returns_generator(self, adapter, sample_calculation):
        """Fallback should return a generator."""
        result = adapter.generate_recommendations_stream(
            calculation_result=sample_calculation,
            user_data={},
            fiscal_year=2024,
        )

        assert hasattr(result, "__iter__")
        assert hasattr(result, "__next__")

    def test_fallback_yields_recommendations(self, adapter, sample_calculation):
        """Fallback should yield recommendation text."""
        result = adapter.generate_recommendations_stream(
            calculation_result=sample_calculation,
            user_data={},
            fiscal_year=2024,
        )

        recommendations = list(result)

        assert len(recommendations) == 1
        assert len(recommendations[0]) > 0

    def test_fallback_contains_fiscal_year(self, adapter, sample_calculation):
        """Fallback recommendations should include fiscal year."""
        result = adapter.generate_recommendations_stream(
            calculation_result=sample_calculation,
            user_data={},
            fiscal_year=2024,
        )

        content = "".join(result)

        assert "2024" in content

    def test_fallback_contains_health_tips(self, adapter, sample_calculation):
        """Fallback should include health deduction tips."""
        result = adapter.generate_recommendations_stream(
            calculation_result=sample_calculation,
            user_data={},
            fiscal_year=2024,
        )

        content = "".join(result)

        assert "Salud" in content or "médico" in content.lower()

    def test_fallback_contains_ppr_info(self, adapter, sample_calculation):
        """Fallback should include PPR information."""
        result = adapter.generate_recommendations_stream(
            calculation_result=sample_calculation,
            user_data={},
            fiscal_year=2024,
        )

        content = "".join(result)

        assert "PPR" in content or "Retiro" in content

    def test_fallback_works_for_2024(self, adapter, sample_calculation):
        """Fallback should work for fiscal year 2024."""
        result = adapter.generate_recommendations_stream(
            calculation_result=sample_calculation,
            user_data={},
            fiscal_year=2024,
        )

        content = "".join(result)

        assert len(content) > 500
        assert "2024" in content

    def test_fallback_works_for_2025(self, adapter, sample_calculation):
        """Fallback should work for fiscal year 2025."""
        result = adapter.generate_recommendations_stream(
            calculation_result=sample_calculation,
            user_data={},
            fiscal_year=2025,
        )

        content = "".join(result)

        assert len(content) > 500
        assert "2025" in content

    def test_fallback_works_for_2026(self, adapter, sample_calculation):
        """Fallback should work for fiscal year 2026."""
        result = adapter.generate_recommendations_stream(
            calculation_result=sample_calculation,
            user_data={},
            fiscal_year=2026,
        )

        content = "".join(result)

        assert len(content) > 500
        assert "2026" in content

    def test_fallback_uses_correct_uma_for_year(self, adapter, sample_calculation):
        """Fallback should use correct UMA values based on fiscal year."""
        # 2024 UMA annual = 39,606.36 → 5 UMAs = 198,031.80
        result_2024 = adapter.generate_recommendations_stream(
            calculation_result=sample_calculation,
            user_data={},
            fiscal_year=2024,
        )
        content_2024 = "".join(result_2024)

        # 2026 UMA annual = 42,714.15 → 5 UMAs = 213,570.75
        result_2026 = adapter.generate_recommendations_stream(
            calculation_result=sample_calculation,
            user_data={},
            fiscal_year=2026,
        )
        content_2026 = "".join(result_2026)

        # Content should be different due to different UMA values
        assert "198,031" in content_2024 or "198031" in content_2024
        assert "213,570" in content_2026 or "213570" in content_2026

    def test_fallback_is_markdown_formatted(self, adapter, sample_calculation):
        """Fallback output should be formatted as Markdown."""
        result = adapter.generate_recommendations_stream(
            calculation_result=sample_calculation,
            user_data={},
            fiscal_year=2024,
        )

        content = "".join(result)

        assert "#" in content  # Headers
        assert "*" in content  # Lists


class TestDeepSeekAdapter:
    """Tests for DeepSeekRecommendationAdapter availability check."""

    def test_deepseek_not_available_without_api_key(self):
        """DeepSeek should not be available without API key."""
        with patch(
            "src.recommendations.infrastructure.providers.deepseek_adapter.get_settings"
        ) as mock_settings:
            mock_settings.return_value.has_deepseek_configured.return_value = False

            from src.recommendations.infrastructure.providers.deepseek_adapter import (
                DeepSeekRecommendationAdapter,
            )

            adapter = DeepSeekRecommendationAdapter()

            assert adapter.is_available() is False

    def test_deepseek_provider_name(self):
        """DeepSeek should return correct provider name."""
        with patch(
            "src.recommendations.infrastructure.providers.deepseek_adapter.get_settings"
        ) as mock_settings:
            mock_settings.return_value.deepseek_api_key = None
            mock_settings.return_value.deepseek_model = "deepseek-chat"
            mock_settings.return_value.deepseek_base_url = "https://api.deepseek.com"
            mock_settings.return_value.deepseek_temperature = 0.6

            from src.recommendations.infrastructure.providers.deepseek_adapter import (
                DeepSeekRecommendationAdapter,
            )

            adapter = DeepSeekRecommendationAdapter()

            assert adapter.get_provider_name() == "DeepSeek"


class TestGeminiAdapter:
    """Tests for GeminiRecommendationAdapter availability check."""

    def test_gemini_not_available_without_api_key(self):
        """Gemini should not be available without API key."""
        with patch(
            "src.recommendations.infrastructure.providers.gemini_adapter.get_settings"
        ) as mock_settings:
            mock_settings.return_value.has_gemini_configured.return_value = False
            mock_settings.return_value.gemini_api_key = None

            from src.recommendations.infrastructure.providers.gemini_adapter import (
                GeminiRecommendationAdapter,
            )

            adapter = GeminiRecommendationAdapter()

            assert adapter.is_available() is False

    def test_gemini_provider_name(self):
        """Gemini should return correct provider name."""
        with patch(
            "src.recommendations.infrastructure.providers.gemini_adapter.get_settings"
        ) as mock_settings:
            mock_settings.return_value.gemini_api_key = None

            from src.recommendations.infrastructure.providers.gemini_adapter import (
                GeminiRecommendationAdapter,
            )

            adapter = GeminiRecommendationAdapter()

            assert adapter.get_provider_name() == "Gemini"


class TestProviderPriority:
    """Tests for provider priority ordering."""

    def test_fallback_is_always_last_resort(self):
        """Fallback should work when other providers fail."""
        fallback = FallbackRecommendationAdapter()

        # Fallback is always available
        assert fallback.is_available() is True

        # And always returns recommendations
        mock_calc = MagicMock()
        mock_calc.gross_annual_income = 100000.0
        result = list(fallback.generate_recommendations_stream(mock_calc, {}, 2024))

        assert len(result) > 0
        assert len(result[0]) > 0
