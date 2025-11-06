"""
Multi-agent analysis router.
API endpoints for multi-agent fiscal debate.
"""

import json

from fastapi import APIRouter, HTTPException, Depends
from sse_starlette.sse import EventSourceResponse

from src.api.v1.schemas.multi_agent_schemas import (
    MultiAgentAnalysisRequest as MultiAgentAnalysisRequestSchema,
    MultiAgentAnalysisResponse as MultiAgentAnalysisResponseSchema,
    UsageInfoResponse,
    ExpertProfileSchema,
    DebateRoundSchema,
    VotingResultsSchema,
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


@router.post("/multi-agent-analysis", response_model=MultiAgentAnalysisResponseSchema)
async def generate_multi_agent_analysis(
    request_data: MultiAgentAnalysisRequestSchema,
    user_id: str = Depends(get_user_id),
    use_case: GenerateMultiAgentAnalysisUseCase = Depends(get_multi_agent_use_case),
):
    """
    Generate multi-agent fiscal analysis (non-streaming).

    Requires authentication. Rate limited to 3 analyses per day.

    Args:
        request_data: Analysis request with calculation result and user data

    Returns:
        Complete analysis with expert debate, voting, and conclusion

    Raises:
        HTTPException: 401 if not authenticated, 429 if rate limit exceeded,
                       400 if invalid data, 500 if generation fails
    """
    # Check rate limit
    if not use_case.can_generate(user_id):
        usage_info = use_case.get_usage_info(user_id)
        raise HTTPException(
            status_code=429,
            detail=f"Daily limit reached. You have used {usage_info['usage_count']}/{usage_info['daily_limit']} analyses today.",
        )

    try:
        # Create use case request
        use_case_request = MultiAgentAnalysisRequest(
            calculation_result=request_data.calculation_result,
            user_data=request_data.user_data,
            fiscal_year=request_data.fiscal_year,
        )

        # Execute analysis
        result = use_case.execute(use_case_request, user_id)

        # Get updated usage info
        usage_info = use_case.get_usage_info(user_id)

        # Convert response
        return MultiAgentAnalysisResponseSchema(
            expert_profiles=[
                ExpertProfileSchema(**profile) for profile in result.expert_profiles
            ],
            moderator_name=result.moderator_name,
            rounds=[DebateRoundSchema(**round_data) for round_data in result.rounds],
            voting_results=VotingResultsSchema(**result.voting_results),
            conclusion=result.conclusion,
            full_transcript=result.full_transcript,
            usage_info=usage_info,
        )

    except ValueError as e:
        error_msg = str(e)
        if "limit reached" in error_msg.lower():
            raise HTTPException(status_code=429, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate multi-agent analysis: {str(e)}",
        )


@router.post("/multi-agent-analysis/stream")
async def stream_multi_agent_analysis(
    request_data: MultiAgentAnalysisRequestSchema,
    user_id: str = Depends(get_user_id),
    use_case: GenerateMultiAgentAnalysisUseCase = Depends(get_multi_agent_use_case),
):
    """
    Generate multi-agent analysis with Server-Sent Events streaming.

    Requires authentication. Rate limited to 3 analyses per day.

    Args:
        request_data: Analysis request with calculation result and user data

    Returns:
        SSE stream with real-time debate events

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
