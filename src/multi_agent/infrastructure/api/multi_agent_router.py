"""
Multi-agent analysis router.
API endpoints for multi-agent fiscal debate.
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse

from src.multi_agent.application.generate_multi_agent_analysis_use_case import (
    GenerateMultiAgentAnalysisUseCase,
    MultiAgentAnalysisRequest,
)
from src.auth.infrastructure.dependencies import get_user_id
from src.shared.infrastructure.api.schemas.multi_agent_schemas import (
    MultiAgentAnalysisRequest as MultiAgentAnalysisRequestSchema,
)
from src.shared.infrastructure.api.schemas.multi_agent_schemas import (
    UsageInfoResponse,
)
from src.shared.infrastructure.config.dependency_injection import get_container

router = APIRouter(prefix="/api", tags=["multi-agent-analysis"])


def get_multi_agent_use_case() -> GenerateMultiAgentAnalysisUseCase:
    """Get multi-agent analysis use case from DI container."""
    container = get_container()
    return container.get_multi_agent_use_case()


@router.get("/multi-agent-analysis/usage", response_model=UsageInfoResponse)
async def check_multi_agent_usage(
    user_id: str = Depends(get_user_id),
    use_case: GenerateMultiAgentAnalysisUseCase = Depends(get_multi_agent_use_case),
):
    """
    Check current multi-agent analysis usage for authenticated user.

    Returns usage count, remaining usage, and daily limit.
    """
    usage_info = use_case.get_usage_info(user_id)

    return UsageInfoResponse(**usage_info)


@router.post("/multi-agent-analysis")
async def generate_multi_agent_analysis(
    request_data: MultiAgentAnalysisRequestSchema,
    user_id: str = Depends(get_user_id),
    use_case: GenerateMultiAgentAnalysisUseCase = Depends(get_multi_agent_use_case),
):
    """
    Generate multi-agent fiscal analysis with Server-Sent Events streaming.

    Creates a debate between 3 AI fiscal experts with randomized personalities and professions
    (e.g., Conservative Auditor, Aggressive Tax Planner, Analytical Accountant). Each agent analyzes
    the tax situation and proposes optimization strategies in 3 debate rounds:
    1. **Initial Proposals**: Each agent presents their strategy (150-250 chars)
    2. **Response Round**: Agents respond to others' proposals with counterarguments
    3. **Consensus Round**: Agents prioritize and vote on best strategies

    Finally, a moderator synthesizes all arguments into a unified action plan with implementation roadmap.

    **AI Models:** Uses LiteLLM adapter with Claude Sonnet 4.5 (default) or DeepSeek for each agent
    **Rate Limiting:** 3 analyses/day per user (resets at midnight)

    Args:
        request_data: Analysis request with calculation result and user data
        user_id: User identifier from Google OAuth (injected)
        use_case: Multi-agent analysis use case (injected)

    Returns:
        EventSourceResponse with Server-Sent Events:
        - `agent_intro`: List of 3 agents with personalities, professions, expertise
        - `round_start`: Start of debate round (1, 2, or 3)
        - `agent_turn`: Agent begins speaking
        - `agent_chunk`: Streaming text content from agent
        - `agent_complete`: Agent finished their turn
        - `synthesis_start`: Final synthesis beginning
        - `synthesis_chunk`: Streaming synthesis content
        - `synthesis_complete`: Full synthesis text
        - `complete`: Debate finished
        - `usage`: Usage info (count/remaining/limit)

    Raises:
        HTTPException 401: User not authenticated
        HTTPException 429: Daily limit exceeded (3 analyses/day)

    Example SSE Events:
        ```
        event: message
        data: {"type":"agent_intro","agents":[{"name":"María González","personality":"conservative",...}]}

        event: message
        data: {"type":"round_start","round_number":1,"round_name":"Propuestas Iniciales"}

        event: message
        data: {"type":"agent_turn","agent_name":"María González",...}

        event: message
        data: {"type":"agent_chunk","content":"Recomiendo priorizar..."}
        ```
    """
    # Check rate limit
    if not use_case.can_generate(user_id):
        usage_info = use_case.get_usage_info(user_id)
        raise HTTPException(
            status_code=429,
            detail=f"Daily limit reached. You have used {usage_info['usage_count']}/{usage_info['daily_limit']} analyses today.",
        )

    async def event_generator():
        """Generate SSE events from the multi-agent analysis stream."""
        try:
            # Create use case request
            use_case_request = MultiAgentAnalysisRequest(
                calculation_result=request_data.calculation_result,
                user_data=request_data.user_data,
                fiscal_year=request_data.fiscal_year,
            )

            # Stream analysis events
            for event in use_case.execute_stream(use_case_request, user_id):
                yield {
                    "event": "message",
                    "data": json.dumps(event),
                }

            # Send final usage info
            usage_info = use_case.get_usage_info(user_id)
            yield {
                "event": "usage",
                "data": json.dumps(usage_info),
            }

        except ValueError as e:
            error_msg = str(e)
            yield {
                "event": "error",
                "data": json.dumps({"error": error_msg}),
            }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": f"Analysis failed: {str(e)}"}),
            }

    return EventSourceResponse(event_generator())
