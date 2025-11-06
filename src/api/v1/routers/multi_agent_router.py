"""
Multi-agent analysis router.
API endpoints for multi-agent fiscal debate.
"""

import json

from fastapi import APIRouter, HTTPException, Depends
from sse_starlette.sse import EventSourceResponse

from src.api.v1.schemas.multi_agent_schemas import (
    MultiAgentAnalysisRequest as MultiAgentAnalysisRequestSchema,
    UsageInfoResponse,
)
from src.application.generate_multi_agent_analysis_use_case import (
    GenerateMultiAgentAnalysisUseCase,
    MultiAgentAnalysisRequest,
)
from src.infrastructure.config.dependency_injection import get_container
from src.infrastructure.auth.dependencies import get_user_id


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

    Requires authentication. Rate limited per day.

    Args:
        request_data: Analysis request with calculation result and user data

    Returns:
        SSE stream with real-time debate events:
        - agent_intro: List of agents with profiles
        - round_start: Start of debate round
        - agent_turn: Agent starts speaking
        - agent_chunk: Streaming text content
        - agent_complete: Agent finished turn
        - synthesis_start: Final synthesis beginning
        - synthesis_chunk: Streaming synthesis content
        - synthesis_complete: Full synthesis text
        - complete: Debate finished
        - usage: Usage info

    Raises:
        HTTPException: 401 if not authenticated, 429 if rate limit exceeded
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
