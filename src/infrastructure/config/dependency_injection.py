from functools import lru_cache
from typing import List
from src.infrastructure.config.settings import get_settings
from src.infrastructure.persistence.sqlite_usage_repository import SqliteUsageRepository
from src.domain.ports.repositories import UsageRepository
from src.domain.ports.ai_providers import RecommendationProvider, MultiAgentProvider
from src.application.generate_recommendations_use_case import (
    GenerateRecommendationsUseCase,
)
from src.application.generate_multi_agent_analysis_use_case import (
    GenerateMultiAgentAnalysisUseCase,
)


class DependencyContainer:
    """
    Dependency injection container.
    Manages creation and lifecycle of application dependencies.
    """

    def __init__(self):
        self._settings = get_settings()
        self._usage_repository: UsageRepository | None = None
        self._recommendation_providers: List[RecommendationProvider] | None = None
        self._recommendations_use_case: GenerateRecommendationsUseCase | None = None
        self._multi_agent_providers: List[MultiAgentProvider] | None = None
        self._multi_agent_use_case: GenerateMultiAgentAnalysisUseCase | None = None

    def get_usage_repository(self) -> UsageRepository:
        """Get or create usage repository instance"""
        if self._usage_repository is None:
            self._usage_repository = SqliteUsageRepository(
                db_path=self._settings.database_url
            )
        return self._usage_repository

    def get_recommendation_providers(self) -> List[RecommendationProvider]:
        """
        Get list of recommendation providers in priority order.
        Uses lazy imports to avoid circular dependencies.
        """
        if self._recommendation_providers is None:
            from src.infrastructure.ai_providers.recommendation_adapters import (
                DeepSeekRecommendationAdapter,
                GeminiRecommendationAdapter,
                FallbackRecommendationAdapter,
            )

            providers: List[RecommendationProvider] = []

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

            # Priority 3: Fallback (always available)
            providers.append(FallbackRecommendationAdapter())

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

    def get_multi_agent_providers(self) -> List[MultiAgentProvider]:
        """
        Get list of multi-agent providers in priority order.
        Uses lazy imports to avoid circular dependencies.
        """
        if self._multi_agent_providers is None:
            from src.infrastructure.ai_providers.multi_agent_adapters import (
                DeepSeekMultiAgentAdapter,
                GeminiMultiAgentAdapter,
            )

            providers: List[MultiAgentProvider] = []

            # Priority 1: DeepSeek
            if self._settings.has_deepseek_configured():
                try:
                    providers.append(DeepSeekMultiAgentAdapter(self._settings))
                except Exception as e:
                    print(f"⚠️  Could not initialize DeepSeek multi-agent: {e}")

            # Priority 2: Gemini
            if self._settings.has_gemini_configured():
                try:
                    providers.append(GeminiMultiAgentAdapter(self._settings))
                except Exception as e:
                    print(f"⚠️  Could not initialize Gemini multi-agent: {e}")

            self._multi_agent_providers = providers

        return self._multi_agent_providers

    def get_multi_agent_use_case(self) -> GenerateMultiAgentAnalysisUseCase:
        """Get or create multi-agent analysis use case instance"""
        if self._multi_agent_use_case is None:
            self._multi_agent_use_case = GenerateMultiAgentAnalysisUseCase(
                providers=self.get_multi_agent_providers(),
                usage_repository=self.get_usage_repository(),
                daily_limit=self._settings.daily_recommendations_limit,
            )
        return self._multi_agent_use_case

    def reset(self) -> None:
        """Reset container (useful for testing)"""
        self._usage_repository = None
        self._recommendation_providers = None
        self._recommendations_use_case = None
        self._multi_agent_providers = None
        self._multi_agent_use_case = None


@lru_cache
def get_container() -> DependencyContainer:
    """Get singleton dependency container"""
    return DependencyContainer()
