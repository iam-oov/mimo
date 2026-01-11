from functools import lru_cache

from src.multi_agent.application.generate_multi_agent_analysis_use_case import (
    GenerateMultiAgentAnalysisUseCase,
)
from src.multi_agent.application.multi_agent_chat_use_case import MultiAgentChatUseCase
from src.multi_agent.domain.ports.memory import MemoryStore
from src.multi_agent.domain.ports.multi_agent_provider import MultiAgentProvider
from src.multi_agent.infrastructure.memory.simple_memory import SimpleMemoryStore
from src.multi_agent.infrastructure.providers.deepseek_adapter import (
    DeepSeekMultiAgentAdapter,
)
from src.multi_agent.infrastructure.providers.gemini_adapter import (
    GeminiMultiAgentAdapter,
)
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
from src.shared.infrastructure.persistence.postgres_usage_repository import (
    PostgresUsageRepository,
)
from src.shared.infrastructure.persistence.sqlite_usage_repository import (
    SqliteUsageRepository,
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
        self._multi_agent_providers: list[MultiAgentProvider] | None = None
        self._multi_agent_use_case: GenerateMultiAgentAnalysisUseCase | None = None
        self._chat_use_case: MultiAgentChatUseCase | None = None
        self._memory_store: MemoryStore | None = None

    def get_usage_repository(self) -> UsageRepository:
        """Get or create usage repository instance (PostgreSQL or SQLite)"""
        if self._usage_repository is None:
            if self._settings.is_postgres:
                self._usage_repository = PostgresUsageRepository(
                    database_url=self._settings.database_url
                )
            else:
                self._usage_repository = SqliteUsageRepository(
                    db_path=self._settings.database_url
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

    def get_memory_store(self) -> MemoryStore:
        """Get or create memory store (simple keyword-based)."""
        if self._memory_store is None:
            # Base path for memory storage
            self._memory_store = SimpleMemoryStore(base_path="./memory")
        return self._memory_store

    def get_multi_agent_providers(self) -> list[MultiAgentProvider]:
        """Get list of multi-agent providers in priority order."""
        if self._multi_agent_providers is None:
            providers: list[MultiAgentProvider] = []

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

    def get_chat_use_case(self) -> MultiAgentChatUseCase:
        """Get or create multi-agent chat use case instance"""
        if self._chat_use_case is None:
            self._chat_use_case = MultiAgentChatUseCase(
                usage_repository=self.get_usage_repository(),
                daily_limit=self._settings.daily_recommendations_limit,
                memory_store=self.get_memory_store(),
            )
        return self._chat_use_case

    def reset(self) -> None:
        """Reset container (useful for testing)"""
        self._usage_repository = None
        self._recommendation_providers = None
        self._recommendations_use_case = None
        self._multi_agent_providers = None
        self._multi_agent_use_case = None
        self._chat_use_case = None
        self._memory_store = None
        self._chat_use_case = None


@lru_cache
def get_container() -> DependencyContainer:
    """Get singleton dependency container"""
    return DependencyContainer()
