"""MCP Prompts package for PlacementPilot."""

from src.mcp_server.prompts.placement_prompts import (
    get_interview_prep_prompt,
    get_job_analysis_prompt,
    get_follow_up_email_prompt,
)

__all__ = [
    "get_interview_prep_prompt",
    "get_job_analysis_prompt",
    "get_follow_up_email_prompt",
]
