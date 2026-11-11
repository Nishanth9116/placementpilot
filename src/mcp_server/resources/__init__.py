"""MCP Resources package for PlacementPilot."""

from src.mcp_server.resources.placement_resources import (
    get_student_profile_resource,
    get_student_applications_resource,
    get_student_skills_resource,
    get_active_jobs_resource,
)

__all__ = [
    "get_student_profile_resource",
    "get_student_applications_resource",
    "get_student_skills_resource",
    "get_active_jobs_resource",
]
