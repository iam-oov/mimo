"""
Tests for the GenerateRecommendationsUseCase.
"""

from collections.abc import Generator
from dataclasses import dataclass
from datetime import date
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.recommendations.application.generate_recommendations_use_case import (
    GenerateRecommendationsRequest,
    GenerateRecommendationsUseCase,
)
from src.recommendations.domain.ports.recommendation_provider import (
    RecommendationProvider,
)
from src.shared.domain.ports.repositories import UsageRepository
from src.tax_calculation.domain.entities.tax_calculation import TaxCalculation


class MockProvider(RecommendationProvider):
    """Mock recommendation provider for testing."""

    def __init__(self, name: str = "MockProvider", available: bool = True):
        self._name = name
        self._available = available
        self._chunks = ["Hello ", "World ", "!"]

    def generate_recommendations_stream(
        self, calculation_result: Any, user_data: dict[str, Any], fiscal_year: int
    ) -> Generator[str, None, None]:
        for chunk in self._chunks:
            yield chunk

    def is_available(self) -> bool:
        return self._available

    def get_provider_name(self) -> str:
        return self._name


class MockUsageRepository(UsageRepository):
    """Mock usage repository for testing."""

    def __init__(self):
        self._usage: dict[tuple[str, date], int] = {}

    def get_usage_count(self, user_id: str, usage_date: date) -> int:
        return self._usage.get((user_id, usage_date), 0)

    def increment_usage(self, user_id: str, usage_date: date) -> None:
        key = (user_id, usage_date)
        self._usage[key] = self._usage.get(key, 0) + 1

    def reset_usage(self, user_id: str, usage_date: date) -> None:
        key = (user_id, usage_date)
        if key in self._usage:
            del self._usage[key]

    def get_remaining_usage(
        self, user_id: str, usage_date: date, daily_limit: int
    ) -> int:
        current = self.get_usage_count(user_id, usage_date)
        return max(0, daily_limit - current)


class TestGenerateRecommendationsRequest:
    """Tests for the request DTO."""

    @pytest.fixture
    def sample_calculation(self) -> TaxCalculation:
        return TaxCalculation(
            gross_annual_income=200000.0,
            taxable_bonus=5000.0,
            taxable_vacation_premium=2000.0,
            total_taxable_income=207000.0,
            authorized_deductions=30000.0,
            personal_deductions=15000.0,
            ppr_deductions=10000.0,
            education_deductions=5000.0,
            taxable_base=177000.0,
            determined_tax=25000.0,
            withheld_tax=28000.0,
            balance_in_favor=3000.0,
            balance_to_pay=0.0,
        )

    def test_request_creation(self, sample_calculation):
        """Request should be created with all fields."""
        request = GenerateRecommendationsRequest(
            user_id="user123",
            calculation=sample_calculation,
            user_data={"deduction_data": {}},
            fiscal_year=2024,
        )

        assert request.user_id == "user123"
        assert request.calculation == sample_calculation
        assert request.fiscal_year == 2024


class TestUseCaseInitialization:
    """Tests for use case initialization."""

    def test_initialization_with_providers(self):
        """Use case should initialize with providers list."""
        providers = [MockProvider("Provider1"), MockProvider("Provider2")]
        repo = MockUsageRepository()

        use_case = GenerateRecommendationsUseCase(providers, repo, daily_limit=5)

        assert use_case._providers == providers
        assert use_case._daily_limit == 5

    def test_initialization_with_default_limit(self):
        """Use case should have default daily limit of 3."""
        providers = [MockProvider()]
        repo = MockUsageRepository()

        use_case = GenerateRecommendationsUseCase(providers, repo)

        assert use_case._daily_limit == 3


class TestCanGenerate:
    """Tests for the can_generate method."""

    def test_can_generate_when_no_usage(self):
        """User with no usage should be able to generate."""
        providers = [MockProvider()]
        repo = MockUsageRepository()
        use_case = GenerateRecommendationsUseCase(providers, repo, daily_limit=3)

        result = use_case.can_generate("user123")

        assert result is True

    def test_can_generate_when_under_limit(self):
        """User under limit should be able to generate."""
        providers = [MockProvider()]
        repo = MockUsageRepository()
        repo.increment_usage("user123", date.today())
        repo.increment_usage("user123", date.today())
        use_case = GenerateRecommendationsUseCase(providers, repo, daily_limit=3)

        result = use_case.can_generate("user123")

        assert result is True

    def test_cannot_generate_when_at_limit(self):
        """User at limit should not be able to generate."""
        providers = [MockProvider()]
        repo = MockUsageRepository()
        for _ in range(3):
            repo.increment_usage("user123", date.today())
        use_case = GenerateRecommendationsUseCase(providers, repo, daily_limit=3)

        result = use_case.can_generate("user123")

        assert result is False

    def test_cannot_generate_when_over_limit(self):
        """User over limit should not be able to generate."""
        providers = [MockProvider()]
        repo = MockUsageRepository()
        for _ in range(5):
            repo.increment_usage("user123", date.today())
        use_case = GenerateRecommendationsUseCase(providers, repo, daily_limit=3)

        result = use_case.can_generate("user123")

        assert result is False


class TestGetUsageInfo:
    """Tests for the get_usage_info method."""

    def test_usage_info_for_new_user(self):
        """New user should have zero usage and full remaining."""
        providers = [MockProvider()]
        repo = MockUsageRepository()
        use_case = GenerateRecommendationsUseCase(providers, repo, daily_limit=3)

        info = use_case.get_usage_info("new_user")

        assert info["usage_count"] == 0
        assert info["remaining_usage"] == 3
        assert info["daily_limit"] == 3

    def test_usage_info_after_some_usage(self):
        """User with some usage should see correct counts."""
        providers = [MockProvider()]
        repo = MockUsageRepository()
        repo.increment_usage("user123", date.today())
        repo.increment_usage("user123", date.today())
        use_case = GenerateRecommendationsUseCase(providers, repo, daily_limit=5)

        info = use_case.get_usage_info("user123")

        assert info["usage_count"] == 2
        assert info["remaining_usage"] == 3
        assert info["daily_limit"] == 5

    def test_usage_info_at_limit(self):
        """User at limit should show zero remaining."""
        providers = [MockProvider()]
        repo = MockUsageRepository()
        for _ in range(3):
            repo.increment_usage("user123", date.today())
        use_case = GenerateRecommendationsUseCase(providers, repo, daily_limit=3)

        info = use_case.get_usage_info("user123")

        assert info["usage_count"] == 3
        assert info["remaining_usage"] == 0

    def test_usage_info_remaining_never_negative(self):
        """Remaining usage should never be negative."""
        providers = [MockProvider()]
        repo = MockUsageRepository()
        for _ in range(10):
            repo.increment_usage("user123", date.today())
        use_case = GenerateRecommendationsUseCase(providers, repo, daily_limit=3)

        info = use_case.get_usage_info("user123")

        assert info["remaining_usage"] == 0


class TestExecuteStream:
    """Tests for the execute_stream method."""

    @pytest.fixture
    def sample_calculation(self) -> TaxCalculation:
        return TaxCalculation(
            gross_annual_income=200000.0,
            taxable_bonus=5000.0,
            taxable_vacation_premium=2000.0,
            total_taxable_income=207000.0,
            authorized_deductions=30000.0,
            personal_deductions=15000.0,
            ppr_deductions=10000.0,
            education_deductions=5000.0,
            taxable_base=177000.0,
            determined_tax=25000.0,
            withheld_tax=28000.0,
            balance_in_favor=3000.0,
            balance_to_pay=0.0,
        )

    @pytest.fixture
    def sample_request(self, sample_calculation) -> GenerateRecommendationsRequest:
        return GenerateRecommendationsRequest(
            user_id="user123",
            calculation=sample_calculation,
            user_data={"deduction_data": {}},
            fiscal_year=2024,
        )

    def test_execute_stream_returns_generator(self, sample_request):
        """execute_stream should return a generator."""
        providers = [MockProvider()]
        repo = MockUsageRepository()
        use_case = GenerateRecommendationsUseCase(providers, repo)

        result = use_case.execute_stream(sample_request)

        assert hasattr(result, "__iter__")
        assert hasattr(result, "__next__")

    def test_execute_stream_yields_chunks(self, sample_request):
        """execute_stream should yield all chunks from provider."""
        providers = [MockProvider()]
        repo = MockUsageRepository()
        use_case = GenerateRecommendationsUseCase(providers, repo)

        chunks = list(use_case.execute_stream(sample_request))

        assert chunks == ["Hello ", "World ", "!"]

    def test_execute_stream_increments_usage_after_success(self, sample_request):
        """Usage should be incremented after successful generation."""
        providers = [MockProvider()]
        repo = MockUsageRepository()
        use_case = GenerateRecommendationsUseCase(providers, repo)

        # Consume the generator
        list(use_case.execute_stream(sample_request))

        usage = repo.get_usage_count("user123", date.today())
        assert usage == 1

    def test_execute_stream_raises_on_rate_limit(self, sample_request):
        """Should raise PermissionError when rate limited."""
        providers = [MockProvider()]
        repo = MockUsageRepository()
        for _ in range(3):
            repo.increment_usage("user123", date.today())
        use_case = GenerateRecommendationsUseCase(providers, repo, daily_limit=3)

        with pytest.raises(
            PermissionError, match="Daily recommendation limit exceeded"
        ):
            list(use_case.execute_stream(sample_request))

    def test_execute_stream_raises_when_no_provider(self, sample_request):
        """Should raise RuntimeError when no provider available."""
        providers = [MockProvider(available=False)]
        repo = MockUsageRepository()
        use_case = GenerateRecommendationsUseCase(providers, repo)

        with pytest.raises(RuntimeError, match="No AI provider available"):
            list(use_case.execute_stream(sample_request))

    def test_execute_stream_uses_first_available_provider(self, sample_request):
        """Should use first available provider."""
        unavailable = MockProvider("Unavailable", available=False)
        available = MockProvider("Available", available=True)
        providers = [unavailable, available]
        repo = MockUsageRepository()
        use_case = GenerateRecommendationsUseCase(providers, repo)

        # Should not raise - uses second provider
        chunks = list(use_case.execute_stream(sample_request))

        assert chunks == ["Hello ", "World ", "!"]

    def test_execute_stream_does_not_increment_on_rate_limit(self, sample_request):
        """Usage should not be incremented when rate limited."""
        providers = [MockProvider()]
        repo = MockUsageRepository()
        for _ in range(3):
            repo.increment_usage("user123", date.today())
        use_case = GenerateRecommendationsUseCase(providers, repo, daily_limit=3)

        try:
            list(use_case.execute_stream(sample_request))
        except PermissionError:
            pass

        usage = repo.get_usage_count("user123", date.today())
        assert usage == 3  # No increment


class TestProviderSelection:
    """Tests for provider selection logic."""

    def test_get_available_provider_returns_first_available(self):
        """Should return first available provider."""
        providers = [
            MockProvider("Provider1", available=False),
            MockProvider("Provider2", available=True),
            MockProvider("Provider3", available=True),
        ]
        repo = MockUsageRepository()
        use_case = GenerateRecommendationsUseCase(providers, repo)

        provider = use_case._get_available_provider()

        assert provider is not None
        assert provider.get_provider_name() == "Provider2"

    def test_get_available_provider_returns_none_when_none_available(self):
        """Should return None when no provider available."""
        providers = [
            MockProvider("Provider1", available=False),
            MockProvider("Provider2", available=False),
        ]
        repo = MockUsageRepository()
        use_case = GenerateRecommendationsUseCase(providers, repo)

        provider = use_case._get_available_provider()

        assert provider is None

    def test_get_available_provider_with_empty_list(self):
        """Should return None with empty provider list."""
        providers = []
        repo = MockUsageRepository()
        use_case = GenerateRecommendationsUseCase(providers, repo)

        provider = use_case._get_available_provider()

        assert provider is None


class TestErrorHandling:
    """Tests for error handling in execute_stream."""

    @pytest.fixture
    def sample_calculation(self) -> TaxCalculation:
        return TaxCalculation(
            gross_annual_income=200000.0,
            taxable_bonus=5000.0,
            taxable_vacation_premium=2000.0,
            total_taxable_income=207000.0,
            authorized_deductions=30000.0,
            personal_deductions=15000.0,
            ppr_deductions=10000.0,
            education_deductions=5000.0,
            taxable_base=177000.0,
            determined_tax=25000.0,
            withheld_tax=28000.0,
            balance_in_favor=3000.0,
            balance_to_pay=0.0,
        )

    @pytest.fixture
    def sample_request(self, sample_calculation) -> GenerateRecommendationsRequest:
        return GenerateRecommendationsRequest(
            user_id="user123",
            calculation=sample_calculation,
            user_data={"deduction_data": {}},
            fiscal_year=2024,
        )

    def test_provider_error_wrapped_in_runtime_error(self, sample_request):
        """Provider errors should be wrapped in RuntimeError."""

        class FailingProvider(MockProvider):
            def generate_recommendations_stream(self, *args, **kwargs):
                raise ValueError("API Error")
                yield  # Make it a generator

        providers = [FailingProvider()]
        repo = MockUsageRepository()
        use_case = GenerateRecommendationsUseCase(providers, repo)

        with pytest.raises(RuntimeError, match="Failed to generate recommendations"):
            list(use_case.execute_stream(sample_request))

    def test_provider_error_does_not_increment_usage(self, sample_request):
        """Usage should not be incremented when provider fails."""

        class FailingProvider(MockProvider):
            def generate_recommendations_stream(self, *args, **kwargs):
                raise ValueError("API Error")
                yield

        providers = [FailingProvider()]
        repo = MockUsageRepository()
        use_case = GenerateRecommendationsUseCase(providers, repo)

        try:
            list(use_case.execute_stream(sample_request))
        except RuntimeError:
            pass

        usage = repo.get_usage_count("user123", date.today())
        assert usage == 0
