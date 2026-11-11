"""MCP Tools for student profile registration and management."""

from typing import Any, Dict, List, Optional

from src.db.connection import get_db_connection
from src.db.repositories.students import StudentRepository


def register_student(
    usn: str,
    name: str,
    email: str,
    branch: str,
    cgpa: float,
    graduation_year: int,
    skills: Optional[List[str]] = None,
    resume_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Register or update a candidate student profile in PlacementPilot.

    Args:
        usn: Unique University Seat / Roll Number (e.g., '1PI21CS001').
        name: Full student name.
        email: Student official or contact email.
        branch: Academic department or branch code (e.g., 'CSE', 'ECE', 'ISE').
        cgpa: Cumulative Grade Point Average (0.0 to 10.0 scale).
        graduation_year: Expected or actual year of graduation (e.g., 2025).
        skills: List of technical competencies and programming languages.
        resume_path: Optional local path to the student's resume.

    Returns:
        Structured student profile dictionary.
    """
    if not usn or not usn.strip():
        raise ValueError("USN cannot be empty.")
    if not name or not name.strip():
        raise ValueError("Student name cannot be empty.")
    if not email or "@" not in email:
        raise ValueError(f"Invalid email address '{email}'.")
    if not (0.0 <= cgpa <= 10.0):
        raise ValueError(f"CGPA must be between 0.0 and 10.0. Received {cgpa}.")
    if graduation_year < 2000 or graduation_year > 2100:
        raise ValueError(f"Invalid graduation year {graduation_year}.")

    with get_db_connection() as conn:
        repo = StudentRepository(conn)
        existing = repo.get_by_usn(usn.strip())
        if existing:
            # Update existing student
            updated = repo.update(
                student_id=existing["id"],
                name=name.strip(),
                email=email.strip(),
                branch=branch.strip().upper(),
                cgpa=cgpa,
                graduation_year=graduation_year,
                skills=skills or [],
                resume_path=resume_path,
            )
            return {"status": "updated", "student": updated}
        else:
            created = repo.create(
                usn=usn.strip(),
                name=name.strip(),
                email=email.strip(),
                branch=branch.strip().upper(),
                cgpa=cgpa,
                graduation_year=graduation_year,
                skills=skills or [],
                resume_path=resume_path,
            )
            return {"status": "created", "student": created}

