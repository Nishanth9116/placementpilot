"""MCP Tools for application pipeline tracking and interview management."""

from typing import Any, Dict, Optional

from src.db.connection import get_db_connection
from src.services.tracker import TrackerService


def apply_for_job(
    student_id: int,
    job_id: int,
    notes: Optional[str] = None,
    enforce_eligibility: bool = True,
) -> Dict[str, Any]:
    """Submit a job application on behalf of a student with optional eligibility enforcement.

    Args:
        student_id: Primary key of the student.
        job_id: Primary key of the job posting.
        notes: Optional student application statement or referral note.
        enforce_eligibility: When True, rejects application if student CGPA or branch does not match.

    Returns:
        Structured application record.
    """
    if student_id <= 0:
        raise ValueError("Student ID must be a positive integer.")
    if job_id <= 0:
        raise ValueError("Job ID must be a positive integer.")

    with get_db_connection() as conn:
        tracker = TrackerService(conn)
        application = tracker.apply_to_job(
            student_id=student_id,
            job_id=job_id,
            notes=notes,
            enforce_eligibility=enforce_eligibility,
        )
        return {
            "status": "applied",
            "application_id": application["id"],
            "application": application,
        }


def schedule_interview(
    application_id: int,
    round_type: str,
    scheduled_at: Optional[str] = None,
    interviewer_notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Schedule an interview round for a student's active job application.

    Args:
        application_id: Primary key of the application.
        round_type: Category of interview (e.g., 'Online Assessment', 'Technical Round 1', 'HR').
        scheduled_at: Date and time of the round (e.g. '2026-11-20 10:00:00').
        interviewer_notes: Guidelines, meeting link, or instructions for the round.

    Returns:
        Scheduled interview round details.
    """
    if application_id <= 0:
        raise ValueError("Application ID must be a positive integer.")
    if not round_type or not round_type.strip():
        raise ValueError("Round type cannot be empty.")

    with get_db_connection() as conn:
        tracker = TrackerService(conn)
        round_rec = tracker.schedule_interview_round(
            application_id=application_id,
            round_type=round_type.strip(),
            scheduled_at=scheduled_at,
            interviewer_notes=interviewer_notes,
        )
        return {
            "status": "scheduled",
            "round_id": round_rec["id"],
            "round_number": round_rec["round_number"],
            "round": round_rec,
        }


def update_interview_outcome(
    round_id: int,
    status: str,
    feedback: Optional[str] = None,
    interviewer_notes: Optional[str] = None,
    auto_advance_application: bool = True,
) -> Dict[str, Any]:
    """Record interview evaluation outcome and automatically transition candidate pipeline state.

    Args:
        round_id: Primary key of the interview round.
        status: Evaluation verdict ('cleared', 'failed', 'pending', 'cancelled').
        feedback: Qualitative feedback on problem solving, coding, or communication.
        interviewer_notes: Internal interviewer comments or score notes.
        auto_advance_application: When True, marks application as rejected if failed or updates stage if cleared.

    Returns:
        Updated interview round record.
    """
    if round_id <= 0:
        raise ValueError("Round ID must be a positive integer.")
    valid_statuses = {"cleared", "failed", "pending", "cancelled"}
    if status.lower() not in valid_statuses:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {valid_statuses}")

    with get_db_connection() as conn:
        tracker = TrackerService(conn)
        round_rec = tracker.record_interview_outcome(
            round_id=round_id,
            status=status.lower(),
            feedback=feedback,
            interviewer_notes=interviewer_notes,
            auto_update_application=auto_advance_application,
        )
        return {
            "status": "updated",
            "round_id": round_rec["id"],
            "round_status": round_rec["status"],
            "round": round_rec,
        }


def get_student_placement_summary(student_id: int) -> Dict[str, Any]:
    """Retrieve the end-to-end placement dashboard and conversion statistics for a student.

    Args:
        student_id: Primary key of the student.

    Returns:
        Summary containing total applications, stage breakdown, upcoming interviews, and offers received.
    """
    if student_id <= 0:
        raise ValueError("Student ID must be a positive integer.")

    with get_db_connection() as conn:
        tracker = TrackerService(conn)
        summary = tracker.get_student_placement_summary(student_id)
        return summary

