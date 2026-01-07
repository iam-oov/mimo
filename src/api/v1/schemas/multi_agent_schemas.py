"""
Multi-agent analysis API schemas.
Pydantic models for multi-agent debate endpoints.
"""

from typing import Any

from pydantic import BaseModel, Field


class ExpertProfileSchema(BaseModel):
    """Schema for an expert's profile."""

    name: str = Field(..., description="Expert's name")
    profession: str = Field(..., description="Professional title")
    personality: str = Field(..., description="Personality type")
    expertise: str = Field(..., description="Area of expertise")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Osvaldo",
                    "profession": "Auditor Fiscal",
                    "personality": "Conservador",
                    "expertise": "Revisión de cumplimiento y riesgos fiscales",
                }
            ]
        }
    }


class InterventionSchema(BaseModel):
    """Schema for a single expert intervention."""

    agent: str = Field(..., description="Name of the agent")
    profession: str = Field(..., description="Professional title")
    content: str = Field(..., description="Intervention content")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "agent": "Osvaldo",
                    "profession": "Auditor Fiscal",
                    "content": "Recomiendo enfocarse en documentar todas las deducciones médicas...",
                }
            ]
        }
    }


class DebateRoundSchema(BaseModel):
    """Schema for a complete debate round."""

    round_number: int = Field(..., description="Round number (1-3)")
    interventions: list[InterventionSchema] = Field(
        ..., description="All interventions in this round"
    )
    moderator_summary: str = Field(..., description="Moderator's summary of the round")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "round_number": 1,
                    "interventions": [
                        {
                            "agent": "Osvaldo",
                            "profession": "Auditor Fiscal",
                            "content": "La estrategia más segura es...",
                        }
                    ],
                    "moderator_summary": "Los expertos coinciden en...",
                }
            ]
        }
    }


class VotingResultsSchema(BaseModel):
    """Schema for voting results."""

    votes: list[dict[str, str]] = Field(default=[], description="Individual votes from each expert")
    vote_counts: dict[str, int] = Field(default={}, description="Vote count by expert name")
    winner: str = Field(default="", description="Name of winning expert")
    winning_strategy: str = Field(default="", description="Description of winning strategy")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "votes": [
                        {"voter": "Osvaldo", "voted_for": "Erika"},
                        {"voter": "Erika", "voted_for": "Sofia"},
                    ],
                    "vote_counts": {"Erika": 2, "Sofia": 1},
                    "winner": "Erika",
                    "winning_strategy": "Maximizar deducciones PPR y educativas",
                }
            ]
        }
    }


class MultiAgentAnalysisRequest(BaseModel):
    """Request for multi-agent fiscal analysis."""

    calculation_result: dict[str, Any] = Field(..., description="Tax calculation result")
    user_data: dict[str, Any] = Field(..., description="User's tax information")
    fiscal_year: int = Field(..., ge=2024, le=2030, description="Fiscal year")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "calculation_result": {
                        "gross_annual_income": 158760.00,
                        "balance_in_favor": 3651.14,
                    },
                    "user_data": {"contribuyente": {"nombre_o_referencia": "Juan Pérez"}},
                    "fiscal_year": 2024,
                }
            ]
        }
    }


class MultiAgentAnalysisResponse(BaseModel):
    """Response from multi-agent analysis."""

    expert_profiles: list[ExpertProfileSchema] = Field(
        ..., description="Profiles of participating experts"
    )
    moderator_name: str = Field(..., description="Name of the moderator")
    rounds: list[DebateRoundSchema] = Field(default=[], description="All debate rounds")
    voting_results: VotingResultsSchema | None = Field(
        default=None, description="Voting results (optional)"
    )
    conclusion: str = Field(..., description="Final conclusion")
    full_transcript: str = Field(default="", description="Complete conversation transcript")
    usage_info: dict[str, int] = Field(..., description="Usage tracking information")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "expert_profiles": [
                        {
                            "name": "Osvaldo",
                            "profession": "Auditor Fiscal",
                            "personality": "Conservador",
                            "expertise": "Revisión de cumplimiento",
                        }
                    ],
                    "moderator_name": "Moderador Fiscal",
                    "rounds": [],
                    "voting_results": {
                        "votes": [],
                        "vote_counts": {},
                        "winner": "Osvaldo",
                        "winning_strategy": "Estrategia conservadora",
                    },
                    "conclusion": "La estrategia recomendada es...",
                    "full_transcript": "Moderador: Bienvenidos...",
                    "usage_info": {
                        "usage_count": 1,
                        "remaining_usage": 2,
                        "daily_limit": 3,
                    },
                }
            ]
        }
    }


class UsageInfoResponse(BaseModel):
    """Response for usage information check."""

    usage_count: int = Field(..., description="Number of analyses used today")
    remaining_usage: int = Field(..., description="Remaining analyses for today")
    daily_limit: int = Field(..., description="Total daily limit")

    model_config = {
        "json_schema_extra": {
            "examples": [{"usage_count": 1, "remaining_usage": 2, "daily_limit": 3}]
        }
    }
