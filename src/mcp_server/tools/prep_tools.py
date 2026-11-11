"""MCP Tools for placement preparation, skill gap analysis, and mock interviews."""

from typing import Any, Dict, Optional

from src.db.connection import get_db_connection
from src.services.prep import PrepService


def get_interview_prep_plan(student_id: int, job_id: int) -> Dict[str, Any]:
    """Diagnose candidate skill gaps for a job and generate a curated question study plan.

    Args:
        student_id: Primary key of the student.
        job_id: Primary key of the job posting.

    Returns:
        Analysis including missing skills, matched skills, and tailored practice questions.
    """
    if student_id <= 0:
        raise ValueError("Student ID must be a positive integer.")
    if job_id <= 0:
        raise ValueError("Job ID must be a positive integer.")

    with get_db_connection() as conn:
        prep = PrepService(conn)
        plan = prep.analyze_skill_gaps(student_id=student_id, job_id=job_id)
        return plan


def log_mock_interview_evaluation(
    student_id: int,
    topic: str,
    score: float,
    feedback: str,
    transcript: Optional[str] = None,
) -> Dict[str, Any]:
    """Record a mock interview practice session and evaluate candidate readiness.

    Args:
        student_id: Primary key of the student.
        topic: Practice subject (e.g. 'Dynamic Programming', 'OS & Concurrency', 'Behavioral HR').
        score: Score out of 100.0.
        feedback: Diagnostic feedback on strengths and improvement areas.
        transcript: Optional full session dialogue or code notes.

    Returns:
        Logged session details and overall cumulative candidate readiness verdict.
    """
    if student_id <= 0:
        raise ValueError("Student ID must be a positive integer.")
    if not topic or not topic.strip():
        raise ValueError("Topic cannot be empty.")
    if not (0.0 <= score <= 100.0):
        raise ValueError(f"Score must be between 0.0 and 100.0. Received {score}.")

    with get_db_connection() as conn:
        prep = PrepService(conn)
        result = prep.log_and_evaluate_mock(
            student_id=student_id,
            topic=topic.strip(),
            score=score,
            feedback=feedback,
            transcript=transcript,
        )
        return result

