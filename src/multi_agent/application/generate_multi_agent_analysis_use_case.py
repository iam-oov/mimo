"""
Multi-agent analysis use case.
Orchestrates fiscal expert debate with rate limiting.
"""

from collections.abc import Generator
from dataclasses import dataclass
from datetime import date
from typing import Any

from src.multi_agent.application.multi_agent_debate_service import MultiAgentDebateService
from src.multi_agent.domain.ports.multi_agent_provider import MultiAgentProvider
from src.shared.domain.ports.repositories import UsageRepository


@dataclass
class MultiAgentAnalysisRequest:
    """Request for multi-agent analysis."""

    calculation_result: Any
    user_data: dict[str, Any]
    fiscal_year: int


@dataclass
class MultiAgentAnalysisResponse:
    """Response from multi-agent analysis."""

    expert_profiles: list[dict[str, str]]
    moderator_name: str
    rounds: list[dict[str, Any]]
    voting_results: dict[str, Any] | None
    conclusion: str
    full_transcript: str


class GenerateMultiAgentAnalysisUseCase:
    """
    Use case for generating multi-agent fiscal analysis with debate.

    Orchestrates a debate between 3 AI fiscal experts (with randomized personalities and professions)
    to analyze tax situations and generate actionable optimization strategies. Handles rate limiting,
    provider selection, and usage tracking.

    **Business Rules:**
    - Rate limit: 3 analyses per user per day (resets at midnight)
    - Provider fallback: Uses first available provider from priority list
    - Debate structure: 3 rounds (initial proposals, responses, consensus) + synthesis
    - Agent selection: Random personalities (Conservative, Aggressive, etc.) + professions (Auditor, Tax Planner, etc.)

    **Use Cases:**
    - execute(): Non-streaming analysis (collects all events, returns complete response)
    - execute_stream(): Streaming analysis (yields SSE events in real-time)

    Attributes:
        providers: List of multi-agent AI providers (priority order)
        usage_repository: Repository for tracking daily usage
        _daily_limit: Maximum analyses per user per day (default: 3)
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
        """
        Check if user can generate more analyses today (rate limiting).

        Args:
            user_id: Unique user identifier (from Google OAuth)

        Returns:
            True if user has remaining usage quota, False if daily limit reached
        """
        today = date.today()
        usage_count = self.usage_repository.get_usage_count(user_id, today)
        return usage_count < self._daily_limit

    def get_usage_info(self, user_id: str) -> dict[str, int]:
        """
        Get current usage statistics for user.

        Args:
            user_id: Unique user identifier

        Returns:
            Dictionary with:
            - usage_count: Number of analyses generated today
            - remaining_usage: Remaining analyses available
            - daily_limit: Total daily limit
        """
        today = date.today()
        usage_count = self.usage_repository.get_usage_count(user_id, today)

        return {
            "usage_count": usage_count,
            "remaining_usage": max(0, self._daily_limit - usage_count),
            "daily_limit": self._daily_limit,
        }

    def _get_available_provider(self) -> MultiAgentProvider | None:
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
    ) -> Generator[dict[str, Any], None, None]:
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
