"""MCP Tools for hiring companies, job postings, and eligibility checks."""

from typing import Any, Dict, List, Optional

from src.db.connection import get_db_connection
from src.db.repositories.companies import CompanyRepository
from src.db.repositories.students import StudentRepository
from src.services.eligibility import EligibilityService


def add_job_opening(
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
    """Register a new campus recruitment drive with eligibility criteria.

    Args:
        company_name: Name of hiring organization.
        role_title: Position designation (e.g., 'Software Engineer').
        ctc_lpa: Annual compensation package in Lakhs Per Annum (LPA).
        min_cgpa: Minimum CGPA required to apply (0.0 to 10.0 scale). Defaults to 0.0.
        allowed_branches: Eligible engineering/degree branches (e.g., ['CSE', 'ECE']).
        required_skills: Key technical skills evaluated during the hiring process.
        job_description: Overview of role responsibilities and qualifications.
        location: Work location (e.g., 'Bangalore', 'Remote', 'On-site').
        application_deadline: Cutoff date in YYYY-MM-DD format.

    Returns:
        Structured job posting details including company metadata.
    """
    if not company_name or not company_name.strip():
        raise ValueError("Company name cannot be empty.")
    if not role_title or not role_title.strip():
        raise ValueError("Role title cannot be empty.")
    if ctc_lpa < 0.0:
        raise ValueError(f"CTC cannot be negative. Received {ctc_lpa}.")
    if not (0.0 <= min_cgpa <= 10.0):
        raise ValueError(f"Minimum CGPA must be between 0.0 and 10.0. Received {min_cgpa}.")

    with get_db_connection() as conn:
        repo = CompanyRepository(conn)
        company = repo.get_company_by_name(company_name.strip())
        if not company:
            company = repo.create_company(name=company_name.strip())

        job = repo.create_job(
            company_id=company["id"],
            role_title=role_title.strip(),
            job_description=job_description,
            ctc_lpa=ctc_lpa,
            location=location,
            min_cgpa=min_cgpa,
            allowed_branches=[b.strip().upper() for b in (allowed_branches or [])],
            required_skills=required_skills or [],
            application_deadline=application_deadline,
        )
        return {"status": "created", "job": job}


def check_job_eligibility(student_id: int, job_id: int) -> Dict[str, Any]:
    """Evaluate whether a student satisfies the academic and skill criteria for a job.

    Args:
        student_id: Primary key of the student.
        job_id: Primary key of the job posting.

    Returns:
        Full eligibility analysis breakdown including CGPA check, branch match,
        skill match percentage, matched skills, and missing skills.
    """
    if student_id <= 0:
        raise ValueError("Student ID must be a positive integer.")
    if job_id <= 0:
        raise ValueError("Job ID must be a positive integer.")

    with get_db_connection() as conn:
        student_repo = StudentRepository(conn)
        company_repo = CompanyRepository(conn)

        student = student_repo.get_by_id(student_id)
        if not student:
            raise ValueError(f"Student with ID {student_id} not found.")

        job = company_repo.get_job_by_id(job_id)
        if not job:
            raise ValueError(f"Job with ID {job_id} not found.")

        evaluation = EligibilityService.evaluate(student, job)
        return {
            "student_id": student["id"],
            "student_name": student["name"],
            "job_id": job["id"],
            "role_title": job["role_title"],
            "company_name": job["company_name"],
            "evaluation": evaluation,
        }

