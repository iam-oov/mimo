from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from src.api.v1.schemas.recommendation_schemas import (
    RecommendationRequest,
    UsageInfoResponse,
)
from src.application.generate_recommendations_use_case import (
    GenerateRecommendationsRequest,
    GenerateRecommendationsUseCase,
)
from src.domain.entities.tax_calculation import TaxCalculation
from src.infrastructure.auth.dependencies import get_user_id
from src.infrastructure.config.dependency_injection import get_container

router = APIRouter(prefix="/api", tags=["recommendations"])


def get_recommendations_use_case() -> GenerateRecommendationsUseCase:
    """Dependency injection for recommendations use case"""
    container = get_container()
    return container.get_recommendations_use_case()


def _prepare_recommendation_data(
    req: RecommendationRequest,
) -> tuple[TaxCalculation, dict[str, Any], int]:
    """
    Prepare data for recommendations from request.
    Handles both legacy format (with calculation_result/user_data) and new format (form data).
    """
    # If calculation_result is provided (legacy format), use it directly
    if req.calculation_result is not None and req.user_data is not None:
        calculation = TaxCalculation(**req.calculation_result)
        return calculation, req.user_data, req.fiscal_year

    # Otherwise, calculate from form data (new format)
    from src.api.v1.schemas.tax_schemas import TaxCalculationRequest as TaxAPIRequest
    from src.application.calculate_tax_use_case import (
        CalculateTaxRequest,
        CalculateTaxUseCase,
    )

    # Use the TaxCalculationRequest to call the /calculate endpoint logic
    tax_api_request = TaxAPIRequest(
        taxpayer_name=req.taxpayer_name,
        fiscal_year=req.fiscal_year,
        monthly_gross_income=req.monthly_gross_income,
        monthly_net_income=req.monthly_net_income,
        bonus_days=req.bonus_days,
        vacation_days=req.vacation_days,
        vacation_premium_percentage=req.vacation_premium_percentage,
        general_deductions=req.general_deductions,
        total_tuition=req.total_tuition,
        total_ppr=req.total_ppr,
    )

    # Create use case request
    tax_use_case_request = CalculateTaxRequest(
        taxpayer_name=tax_api_request.taxpayer_name,
        fiscal_year=tax_api_request.fiscal_year,
        monthly_gross_income=tax_api_request.monthly_gross_income,
        bonus_days=tax_api_request.bonus_days,
        vacation_days=tax_api_request.vacation_days,
        vacation_premium_percentage=tax_api_request.vacation_premium_percentage,
        general_deductions=tax_api_request.general_deductions,
        ppr_deductions=tax_api_request.total_ppr,
        education_deductions=tax_api_request.total_tuition,
    )

    # Calculate taxes
    use_case = CalculateTaxUseCase()
    calc_response = use_case.execute(tax_use_case_request)

    # Build user_data dict for recommendations
    user_data = {
        "deduction_data": {
            "general_deductions": req.general_deductions,
            "ppr_deductions": req.total_ppr,
            "education_deductions": req.total_tuition,
        }
    }

    return calc_response.calculation, user_data, req.fiscal_year


@router.get("/recommendations/usage", response_model=UsageInfoResponse)
async def get_usage_info(
    user_id: str = Depends(get_user_id),
    use_case: GenerateRecommendationsUseCase = Depends(get_recommendations_use_case),
):
    """
    Check current AI recommendations usage for authenticated user.

    Returns daily usage statistics for rate limiting. Each user has a daily limit
    (default: 3 recommendations per day) that resets at midnight.

    Args:
        user_id: User identifier from Google OAuth (injected)
        use_case: Recommendations use case (injected)

    Returns:
        UsageInfoResponse with:
        - usage_count: Number of recommendations generated today
        - remaining_usage: Remaining recommendations available
        - daily_limit: Total daily limit

    Raises:
        HTTPException 401: User not authenticated (missing Google OAuth session)

    Example Response:
        ```json
        {
          "usage_count": 1,
          "remaining_usage": 2,
          "daily_limit": 3
        }
        ```
    """
    usage_info = use_case.get_usage_info(user_id)

    return UsageInfoResponse(**usage_info)


@router.post("/recommendations/stream")
async def generate_recommendations_stream(
    req: RecommendationRequest,
    user_id: str = Depends(get_user_id),
    use_case: GenerateRecommendationsUseCase = Depends(get_recommendations_use_case),
):
    """
    Generate AI-powered fiscal recommendations with real-time streaming.

    Uses Server-Sent Events (SSE) to stream AI-generated recommendations from Mimo el Gatito Fiscal 🐱,
    providing progressive feedback as the AI analyzes tax situation and generates personalized advice.

    **AI Provider Priority:**
    1. Claude Sonnet 4.5 (Anthropic) - Best for tax compliance and Spanish
    2. DeepSeek - Cost-effective fallback
    3. Gemini - Google's model
    4. Fallback - Static recommendations if all AI providers fail

    **Rate Limiting:** 3 recommendations/day per user (resets at midnight)

    Args:
        req: Recommendation request with calculation result and user data (form or legacy format)
        user_id: User identifier from Google OAuth (injected)
        use_case: Recommendations use case (injected)

    Returns:
        StreamingResponse with text/event-stream:
        - Event chunks: `data: {"type":"chunk","content":"..."}`
        - Final event: `data: {"type":"complete","markdown":"full text"}`
        - Error event: `data: {"type":"error","message":"...","code":429|500}`

    Raises:
        HTTPException 400: Invalid data or missing required fields
        HTTPException 401: User not authenticated
        HTTPException 429: Daily limit exceeded (returned in SSE stream)

    Example SSE Stream:
        ```
        data: {"type":"chunk","content":"## 🐱 Recomendaciones Fiscales\\n\\n"}

        data: {"type":"chunk","content":"Purr-fecto! Veo que..."}

        data: {"type":"complete","markdown":"## 🐱 Recomendaciones Fiscales..."}
        ```
    """
    try:
        # Prepare data from request (handles both legacy and new formats)
        calculation, user_data, fiscal_year = _prepare_recommendation_data(req)

        # Create use case request
        use_case_request = GenerateRecommendationsRequest(
            user_id=user_id,
            calculation=calculation,
            user_data=user_data,
            fiscal_year=fiscal_year,
        )

        async def event_generator():
            """Generate Server-Sent Events"""
            import json

            accumulated_text: list[str] = []

            try:
                for chunk in use_case.execute_stream(use_case_request):
                    accumulated_text.append(chunk)

                    # Send chunk event
                    event_data = json.dumps({"type": "chunk", "content": chunk})
                    yield f"data: {event_data}\n\n"

                # Send complete event
                complete_data = json.dumps(
                    {"type": "complete", "markdown": "".join(accumulated_text)}
                )
                yield f"data: {complete_data}\n\n"

            except PermissionError as e:
                error_data = json.dumps({"type": "error", "message": str(e), "code": 429})
                yield f"data: {error_data}\n\n"
            except Exception as e:
                error_data = json.dumps(
                    {
                        "type": "error",
                        "message": f"Failed to generate recommendations: {str(e)}",
                        "code": 500,
                    }
                )
                yield f"data: {error_data}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {str(e)}")
