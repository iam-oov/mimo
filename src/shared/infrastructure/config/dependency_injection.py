from functools import lru_cache

from src.recommendations.application.generate_recommendations_use_case import (
    GenerateRecommendationsUseCase,
)
from src.recommendations.domain.ports.recommendation_provider import (
    RecommendationProvider,
)
from src.recommendations.infrastructure.providers.deepseek_adapter import (
    DeepSeekRecommendationAdapter,
)
from src.recommendations.infrastructure.providers.gemini_adapter import (
    GeminiRecommendationAdapter,
)
from src.shared.domain.ports.repositories import UsageRepository
from src.shared.infrastructure.config.settings import get_settings
from src.tax_calculation.application.calculate_tax_use_case import (
    CalculateTaxUseCase,
)
from src.shared.infrastructure.persistence.postgres_usage_repository import (
    PostgresUsageRepository,
)


class DependencyContainer:
    """
    Dependency injection container.
    Manages creation and lifecycle of application dependencies.
    """

    def __init__(self):
        self._settings = get_settings()
        self._usage_repository: UsageRepository | None = None
        self._recommendation_providers: list[RecommendationProvider] | None = None
        self._recommendations_use_case: GenerateRecommendationsUseCase | None = None
        self._calculate_tax_use_case: CalculateTaxUseCase | None = None

    def get_usage_repository(self) -> UsageRepository:
        """Get or create usage repository instance (PostgreSQL only)"""
        if self._usage_repository is None:
            if not self._settings.is_postgres:
                raise RuntimeError(
                    "DATABASE_URL must be a PostgreSQL connection string. "
                    "SQLite is no longer supported."
                )
            self._usage_repository = PostgresUsageRepository(
                database_url=self._settings.database_url
            )
        return self._usage_repository

    def get_recommendation_providers(self) -> list[RecommendationProvider]:
        """Get list of recommendation providers in priority order."""
        if self._recommendation_providers is None:
            providers: list[RecommendationProvider] = []

            # Priority 1: DeepSeek
            if self._settings.has_deepseek_configured():
                try:
                    providers.append(DeepSeekRecommendationAdapter())
                except Exception as e:
                    print(f"⚠️  Could not initialize DeepSeek: {e}")

            # Priority 2: Gemini
            if self._settings.has_gemini_configured():
                try:
                    providers.append(GeminiRecommendationAdapter())
                except Exception as e:
                    print(f"⚠️  Could not initialize Gemini: {e}")

            self._recommendation_providers = providers

        return self._recommendation_providers

    def get_recommendations_use_case(self) -> GenerateRecommendationsUseCase:
        """Get or create recommendations use case instance"""
        if self._recommendations_use_case is None:
            self._recommendations_use_case = GenerateRecommendationsUseCase(
                providers=self.get_recommendation_providers(),
                usage_repository=self.get_usage_repository(),
                daily_limit=self._settings.daily_recommendations_limit,
            )
        return self._recommendations_use_case

    def get_calculate_tax_use_case(self) -> CalculateTaxUseCase:
        """Get or create tax calculation use case instance"""
        if self._calculate_tax_use_case is None:
            self._calculate_tax_use_case = CalculateTaxUseCase()
        return self._calculate_tax_use_case

    def reset(self) -> None:
        """Reset container (useful for testing)"""
        self._usage_repository = None
        self._recommendation_providers = None
        self._recommendations_use_case = None
        self._calculate_tax_use_case = None


@lru_cache
def get_container() -> DependencyContainer:
    """Get singleton dependency container"""
    return DependencyContainer()
