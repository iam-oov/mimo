"""
Multi-agent chat router.
API endpoints for interactive agent chat.
"""

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from src.auth.infrastructure.dependencies import get_user_id
from src.multi_agent.application.multi_agent_chat_use_case import (
    AgentChatRequest,
    MultiAgentChatUseCase,
)
from src.multi_agent.infrastructure.litellm.adapter import create_agent_adapter
from src.shared.infrastructure.config.dependency_injection import get_container

router = APIRouter(prefix="/api/chat", tags=["multi-agent-chat"])


class ChatMessageRequest(BaseModel):
    """Request schema for chat message."""

    agent_id: str = Field(
        ..., description="Selected agent ID (agent_1, agent_2, agent_3)"
    )
    message: str = Field(..., description="User's question/message")
    calculation_result: dict[str, Any] = Field(
        ..., description="Tax calculation result"
    )
    user_data: dict[str, Any] = Field(..., description="User's fiscal data")
    fiscal_year: int = Field(..., description="Fiscal year")
    conversation_history: list[dict[str, str]] = Field(
        default=[], description="Previous messages"
    )


class AgentInfoResponse(BaseModel):
    """Agent profile response."""

    agent_id: str
    name: str
    personality: str
    profession: str
    expertise: str


class GetAgentsRequest(BaseModel):
    """Request schema for getting available agents."""

    calculation_result: dict[str, Any] = Field(
        ..., description="Tax calculation result"
    )
    user_data: dict[str, Any] = Field(..., description="User's fiscal data")
    fiscal_year: int = Field(..., description="Fiscal year")


def get_chat_use_case() -> MultiAgentChatUseCase:
    """Get chat use case from DI container."""
    container = get_container()
    return container.get_chat_use_case()


@router.post("/agents", response_model=list[AgentInfoResponse])
async def get_available_agents(
    request: GetAgentsRequest,
    user_id: str = Depends(get_user_id),
    use_case: MultiAgentChatUseCase = Depends(get_chat_use_case),
):
    """
    Get available agents for chat session.
    Returns 3 agents with different personalities/professions.
    """
    try:
        agents = use_case.get_available_agents(
            request.calculation_result,
            request.user_data,
            request.fiscal_year,
            user_id=user_id,
        )
        return [
            AgentInfoResponse(
                agent_id=agent.agent_id,
                name=agent.name,
                personality=agent.personality,
                profession=agent.profession,
                expertise=agent.expertise,
            )
            for agent in agents
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agents: {str(e)}")


@router.post("/message")
async def send_chat_message(
    request: ChatMessageRequest,
    user_id: str = Depends(get_user_id),
    use_case: MultiAgentChatUseCase = Depends(get_chat_use_case),
):
    """
    Send message to selected agent and get streaming response.

    Returns SSE stream with agent's response chunks.
    """
    # Check rate limit
    if not use_case.can_generate(user_id):
        usage_info = use_case.get_usage_info(user_id)
        raise HTTPException(
            status_code=429,
            detail=f"Daily limit reached. You have used {usage_info['usage_count']}/{usage_info['daily_limit']} messages today.",
        )

    # Validate agent adapter is available BEFORE creating SSE stream
    # This ensures we return proper HTTP error codes instead of 200 with error in stream
    adapter = create_agent_adapter(request.agent_id)
    if not adapter:
        raise HTTPException(
            status_code=503,
            detail=f"El agente {request.agent_id} no está disponible. Verifica la configuración de API keys.",
        )

    async def event_generator():
        """Generate SSE events from agent response stream."""
        try:
            # Create use case request
            chat_request = AgentChatRequest(
                agent_id=request.agent_id,
                user_message=request.message,
                calculation_result=request.calculation_result,
                user_data=request.user_data,
                fiscal_year=request.fiscal_year,
                conversation_history=request.conversation_history,
            )

            # Stream agent response
            for chunk in use_case.generate_response_stream(chat_request, user_id):
                yield {
                    "event": "message",
                    "data": json.dumps({"type": "chunk", "content": chunk}),
                }

            # Send completion event
            yield {
                "event": "message",
                "data": json.dumps({"type": "complete"}),
            }

            # Send updated usage info
            usage_info = use_case.get_usage_info(user_id)
            yield {
                "event": "usage",
                "data": json.dumps(usage_info),
            }

        except ValueError as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}),
            }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": f"Chat failed: {str(e)}"}),
            }

    return EventSourceResponse(event_generator())
