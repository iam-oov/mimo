"""
Multi-agent analysis use case.
Orchestrates fiscal expert debate with rate limiting.
"""

from dataclasses import dataclass
from typing import Dict, Any, Generator, Optional
from datetime import date

from src.domain.ports.repositories import UsageRepository
from src.domain.ports.ai_providers import MultiAgentProvider
from src.application.multi_agent_debate_service import MultiAgentDebateService


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
    voting_results: Optional[Dict[str, Any]]
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

        # Note: This method collects all streaming events into a single response
        # For streaming UI, use execute_stream() instead
        debate_service = MultiAgentDebateService()

        # Collect all events
        expert_profiles = []
        rounds_data = []
        conclusion = ""
        full_transcript = ""

        for event in debate_service.run_analysis_stream(
            calculation_result=request.calculation_result,
            user_data=request.user_data,
            fiscal_year=request.fiscal_year,
        ):
            event_type = event.get("type")

            if event_type == "agent_intro":
                expert_profiles = event.get("agents", [])
            elif event_type == "synthesis_complete":
                conclusion = event.get("full_text", "")

        # Increment usage after successful generation
        today = date.today()
        self.usage_repository.increment_usage(user_id, today)

        return MultiAgentAnalysisResponse(
            expert_profiles=expert_profiles,
            moderator_name="Moderador Fiscal",
            rounds=[],  # Simplified for non-streaming
            voting_results=None,  # New debate system doesn't use voting
            conclusion=conclusion,
            full_transcript=full_transcript,
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

        # Create debate service and run streaming analysis
        debate_service = MultiAgentDebateService()

        # Yield each event from the streaming analysis
        yield from debate_service.run_analysis_stream(
            calculation_result=request.calculation_result,
            user_data=request.user_data,
            fiscal_year=request.fiscal_year,
        )

        # Increment usage after successful generation
        today = date.today()
        self.usage_repository.increment_usage(user_id, today)
