"""MCP Resources providing URI-based access to placement records and metrics."""

import json
from src.db.connection import get_db_connection
from src.db.repositories.applications import ApplicationRepository
from src.db.repositories.companies import CompanyRepository
from src.db.repositories.questions import QuestionRepository
from src.db.repositories.students import StudentRepository


def get_student_profile_resource(student_id: int) -> str:
    """Resource returning detailed academic and contact profile for a student."""
    with get_db_connection() as conn:
        repo = StudentRepository(conn)
        student = repo.get_by_id(student_id)
        if not student:
            return json.dumps({"error": f"Student with ID {student_id} not found."})
        return json.dumps({
            "id": student["id"],
            "usn": student["usn"],
            "name": student["name"],
            "email": student["email"],
            "branch": student["branch"],
            "cgpa": student["cgpa"],
            "graduation_year": student["graduation_year"],
            "skills": student["skills"],
            "resume_path": student["resume_path"],
            "created_at": student["created_at"],
        }, default=str, indent=2)


def get_student_applications_resource(student_id: int) -> str:
    """Resource returning all job applications and interview rounds for a student."""
    with get_db_connection() as conn:
        student_repo = StudentRepository(conn)
        app_repo = ApplicationRepository(conn)

        student = student_repo.get_by_id(student_id)
        if not student:
            return json.dumps({"error": f"Student with ID {student_id} not found."})

        apps = app_repo.list_applications(student_id=student_id)
        detailed_apps = []
        for app in apps:
            rounds = app_repo.list_rounds_for_application(app["id"])
            item = dict(app)
            item["interview_rounds"] = rounds
            detailed_apps.append(item)

        return json.dumps({
            "student_id": student["id"],
            "student_name": student["name"],
            "total_applications": len(detailed_apps),
            "applications": detailed_apps,
        }, default=str, indent=2)


def get_student_skills_resource(student_id: int) -> str:
    """Resource returning student declared skills and mock interview preparation metrics."""
    with get_db_connection() as conn:
        student_repo = StudentRepository(conn)
        q_repo = QuestionRepository(conn)

        student = student_repo.get_by_id(student_id)
        if not student:
            return json.dumps({"error": f"Student with ID {student_id} not found."})

        mocks = q_repo.list_mock_interviews_for_student(student_id)
        scores = [m["score"] for m in mocks if m["score"] is not None]
        avg_score = round(sum(scores) / len(scores), 1) if scores else None

        return json.dumps({
            "student_id": student["id"],
            "student_name": student["name"],
            "declared_skills": student["skills"],
            "total_mock_sessions": len(mocks),
            "average_mock_score": avg_score,
            "recent_sessions": mocks[:3],
        }, default=str, indent=2)


def get_active_jobs_resource() -> str:
    """Resource returning all currently active campus placement drives."""
    with get_db_connection() as conn:
        repo = CompanyRepository(conn)
        jobs = repo.list_jobs(status="open")
        return json.dumps({
            "total_open_drives": len(jobs),
            "drives": jobs,
        }, default=str, indent=2)
