"""Official Model Context Protocol (MCP) Server for PlacementPilot.

Exposes tools, resources, and reusable prompt templates for local placement preparation,
candidate profile management, and recruitment drive tracking using the official MCP Python SDK.
"""

from typing import Any, Dict, List, Optional
from mcp.server.mcpserver import MCPServer
from mcp.types import PromptMessage

from config.settings import settings
from src.mcp_server import prompts, resources, tools

# Initialize official MCP Server instance
server = MCPServer(
    name=settings.MCP_SERVER_NAME,
    version=settings.MCP_SERVER_VERSION,
    instructions="PlacementPilot MCP server: local assistant for campus placements, drives, and student prep.",
)


# ==============================================================================
# MCP TOOLS (Minimum 6 required; 8 implemented)
# ==============================================================================

@server.tool(name="register_student")
def tool_register_student(
    usn: str,
    name: str,
    email: str,
    branch: str,
    cgpa: float,
    graduation_year: int,
    skills: Optional[List[str]] = None,
    resume_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Register or update a candidate student profile with academic and skill details."""
    return tools.register_student(
        usn=usn,
        name=name,
        email=email,
        branch=branch,
        cgpa=cgpa,
        graduation_year=graduation_year,
        skills=skills,
        resume_path=resume_path,
    )


@server.tool(name="add_job_opening")
def tool_add_job_opening(
    company_name: str,
    role_title: str,
    ctc_lpa: float,
    min_cgpa: float = 0.0,
    allowed_branches: Optional[List[str]] = None,
    required_skills: Optional[List[str]] = None,
    job_description: Optional[str] = None,
    location: str = "On-site",
    application_deadline: Optional[str] = None,
) -> Dict[str, Any]:
    """Register a new campus recruitment drive with eligibility cutoffs and required competencies."""
    return tools.add_job_opening(
        company_name=company_name,
        role_title=role_title,
        ctc_lpa=ctc_lpa,
        min_cgpa=min_cgpa,
        allowed_branches=allowed_branches,
        required_skills=required_skills,
        job_description=job_description,
        location=location,
        application_deadline=application_deadline,
    )


@server.tool(name="check_job_eligibility")
def tool_check_job_eligibility(student_id: int, job_id: int) -> Dict[str, Any]:
    """Evaluate whether a student satisfies the CGPA, branch, and skill criteria for a job."""
    return tools.check_job_eligibility(student_id=student_id, job_id=job_id)


@server.tool(name="apply_for_job")
def tool_apply_for_job(
    student_id: int,
    job_id: int,
    notes: Optional[str] = None,
    enforce_eligibility: bool = True,
) -> Dict[str, Any]:
    """Submit a job application for a student with automatic eligibility verification."""
    return tools.apply_for_job(
        student_id=student_id,
        job_id=job_id,
        notes=notes,
        enforce_eligibility=enforce_eligibility,
    )


@server.tool(name="schedule_interview")
def tool_schedule_interview(
    application_id: int,
    round_type: str,
    scheduled_at: Optional[str] = None,
    interviewer_notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Schedule an interview round for an active job application and update pipeline status."""
    return tools.schedule_interview(
        application_id=application_id,
        round_type=round_type,
        scheduled_at=scheduled_at,
        interviewer_notes=interviewer_notes,
    )


@server.tool(name="update_interview_outcome")
def tool_update_interview_outcome(
    round_id: int,
    status: str,
    feedback: Optional[str] = None,
    interviewer_notes: Optional[str] = None,
    auto_advance_application: bool = True,
) -> Dict[str, Any]:
    """Record an interview round outcome ('cleared' / 'failed') with qualitative feedback."""
    return tools.update_interview_outcome(
        round_id=round_id,
        status=status,
        feedback=feedback,
        interviewer_notes=interviewer_notes,
        auto_advance_application=auto_advance_application,
    )


@server.tool(name="get_student_placement_summary")
def tool_get_student_placement_summary(student_id: int) -> Dict[str, Any]:
    """Retrieve complete placement metrics, application status breakdown, and received offers."""
    return tools.get_student_placement_summary(student_id=student_id)


@server.tool(name="get_interview_prep_plan")
def tool_get_interview_prep_plan(student_id: int, job_id: int) -> Dict[str, Any]:
    """Diagnose candidate skill gaps for a drive and generate a tailored interview question syllabus."""
    return tools.get_interview_prep_plan(student_id=student_id, job_id=job_id)


# ==============================================================================
# MCP RESOURCES
# ==============================================================================

@server.resource("placement://students/{student_id}/profile")
def resource_student_profile(student_id: int) -> str:
    """Read student academic record, contact information, and graduation status."""
    return resources.get_student_profile_resource(int(student_id))


@server.resource("placement://students/{student_id}/applications")
def resource_student_applications(student_id: int) -> str:
    """Read student placement applications and scheduled interview rounds."""
    return resources.get_student_applications_resource(int(student_id))


@server.resource("placement://students/{student_id}/skills")
def resource_student_skills(student_id: int) -> str:
    """Read student declared skills, verified practice counts, and mock interview performance."""
    return resources.get_student_skills_resource(int(student_id))


@server.resource("placement://jobs/active")
def resource_active_jobs() -> str:
    """Read the active campus recruitment drives catalog."""
    return resources.get_active_jobs_resource()


# ==============================================================================
# MCP PROMPTS
# ==============================================================================

@server.prompt("interview_preparation")
def prompt_interview_prep(student_id: int, job_id: int) -> List[PromptMessage]:
    """Generate a mock technical/behavioral interview prompt tailored to the student and job opening."""
    return prompts.get_interview_prep_prompt(int(student_id), int(job_id))


@server.prompt("job_analysis")
def prompt_job_analysis(job_id: int) -> List[PromptMessage]:
    """Generate a campus placement drive analysis prompt evaluating role difficulty and student readiness."""
    return prompts.get_job_analysis_prompt(int(job_id))


@server.prompt("follow_up_email")
def prompt_follow_up_email(application_id: int, round_id: int) -> List[PromptMessage]:
    """Generate a professional post-interview follow-up/thank-you email prompt for the candidate."""
    return prompts.get_follow_up_email_prompt(int(application_id), int(round_id))


def main() -> None:
    """Main entrypoint running the PlacementPilot MCP server on STDIO transport."""
    server.run(transport="stdio")


if __name__ == "__main__":
    main()

