"""MCP Tools package for PlacementPilot."""

from src.mcp_server.tools.student_tools import register_student
from src.mcp_server.tools.job_tools import add_job_opening, check_job_eligibility
from src.mcp_server.tools.application_tools import (
    apply_for_job,
    schedule_interview,
    update_interview_outcome,
    get_student_placement_summary,
)
from src.mcp_server.tools.prep_tools import (
    get_interview_prep_plan,
    log_mock_interview_evaluation,
)

__all__ = [
    "register_student",
    "add_job_opening",
    "check_job_eligibility",
    "apply_for_job",
    "schedule_interview",
    "update_interview_outcome",
    "get_student_placement_summary",
    "get_interview_prep_plan",
    "log_mock_interview_evaluation",
]
