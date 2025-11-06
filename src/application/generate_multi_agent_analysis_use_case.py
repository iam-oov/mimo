"""
Multi-agent analysis use case.
Orchestrates fiscal expert debate with rate limiting.
"""

from dataclasses import dataclass
from typing import Dict, Any, Generator, Optional
from datetime import date

from src.domain.ports.repositories import UsageRepository
from src.domain.ports.ai_providers import MultiAgentProvider


# Lazy import to avoid circular dependencies
_multi_agent_module = None


def _get_multi_agent_module():
    """Lazy load multi_agent_analysis module."""
    global _multi_agent_module
    if _multi_agent_module is None:
        import multi_agent_analysis

        _multi_agent_module = multi_agent_analysis
    return _multi_agent_module


@dataclass
class MultiAgentAnalysisRequest:
    """Request for multi-agent analysis."""

    calculation_result: Any
    user_data: Dict[str, Any]
    fiscal_year: int


@dataclass
class MultiAgentAnalysisResponse:
    """Response from multi-agent analysis."""

    expert_profiles: list[Dict[str, str]]
    moderator_name: str
    rounds: list[Dict[str, Any]]
    voting_results: Dict[str, Any]
    conclusion: str
    full_transcript: str


class GenerateMultiAgentAnalysisUseCase:
    """
    Use case for generating multi-agent fiscal analysis.
    Handles rate limiting and provider selection.
    """

    def __init__(
        self,
        providers: list[MultiAgentProvider],
        usage_repository: UsageRepository,
        daily_limit: int = 3,
    ):
        self.providers = providers
        self.usage_repository = usage_repository
        self._daily_limit = daily_limit

    def can_generate(self, user_id: str) -> bool:
        """Check if user can generate more analyses today."""
        today = date.today()
        usage_count = self.usage_repository.get_usage_count(user_id, today)
        return usage_count < self._daily_limit

    def get_usage_info(self, user_id: str) -> Dict[str, int]:
        """Get current usage information for user."""
        today = date.today()
        usage_count = self.usage_repository.get_usage_count(user_id, today)

        return {
            "usage_count": usage_count,
            "remaining_usage": max(0, self._daily_limit - usage_count),
            "daily_limit": self._daily_limit,
        }

    def _get_available_provider(self) -> Optional[MultiAgentProvider]:
        """Get first available provider from the list."""
        for provider in self.providers:
            if provider.is_available():
                return provider
        return None

    def execute(
        self, request: MultiAgentAnalysisRequest, user_id: str
    ) -> MultiAgentAnalysisResponse:
        """
        Execute multi-agent analysis (non-streaming).

        Args:
            request: Analysis request with calculation and user data
            user_id: User identifier for rate limiting

        Returns:
            Complete analysis with all rounds and conclusion

        Raises:
            ValueError: If user exceeded rate limit or no provider available
        """
        # Check rate limit
        if not self.can_generate(user_id):
            raise ValueError("Daily analysis limit reached")

        # Get available provider
        provider = self._get_available_provider()
        if provider is None:
            raise ValueError("No AI provider available for multi-agent analysis")

        # Get the multi_agent_analysis module
        module = _get_multi_agent_module()

        # Run the analysis using legacy service
        result = module.MultiAgentAnalysisService.run_analysis(
            calculation_result=request.calculation_result,
            user_data=request.user_data,
            fiscal_year=request.fiscal_year,
        )

        # Increment usage after successful generation
        today = date.today()
        self.usage_repository.increment_usage(user_id, today)

        return MultiAgentAnalysisResponse(
            expert_profiles=result.expert_profiles,
            moderator_name=result.moderator_name,
            rounds=result.rounds,
            voting_results=result.voting_results,
            conclusion=result.conclusion,
            full_transcript=result.full_transcript,
        )

    def execute_stream(
        self, request: MultiAgentAnalysisRequest, user_id: str
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Execute multi-agent analysis with streaming output.

        Args:
            request: Analysis request with calculation and user data
            user_id: User identifier for rate limiting

        Yields:
            Stream events with type and content

        Raises:
            ValueError: If user exceeded rate limit or no provider available
        """
        # Check rate limit
        if not self.can_generate(user_id):
            raise ValueError("Daily analysis limit reached")

        # Get available provider
        provider = self._get_available_provider()
        if provider is None:
            raise ValueError("No AI provider available for multi-agent analysis")

        # Get the multi_agent_analysis module
        module = _get_multi_agent_module()

        # Yield each event from the streaming analysis
        yield from module.MultiAgentAnalysisService.run_analysis_stream(
            calculation_result=request.calculation_result,
            user_data=request.user_data,
            fiscal_year=request.fiscal_year,
        )

        # Increment usage after successful generation
        today = date.today()
        self.usage_repository.increment_usage(user_id, today)
