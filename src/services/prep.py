"""Placement preparation, skill gap analysis, and mock interview service."""

import sqlite3
from typing import Any, Dict, List, Optional

from src.db.repositories.companies import CompanyRepository
from src.db.repositories.questions import QuestionRepository
from src.db.repositories.students import StudentRepository
from src.services.eligibility import EligibilityService


class PrepService:
    """Provides personalized interview preparation plans and mock interview tracking."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.student_repo = StudentRepository(conn)
        self.company_repo = CompanyRepository(conn)
        self.question_repo = QuestionRepository(conn)

    def analyze_skill_gaps(self, student_id: int, job_id: int) -> Dict[str, Any]:
        """Analyze gaps between student's skillset and job requirements, recommending study questions."""
        student = self.student_repo.get_by_id(student_id)
        if not student:
            raise ValueError(f"Student with ID {student_id} not found.")

        job = self.company_repo.get_job_by_id(job_id)
        if not job:
            raise ValueError(f"Job posting with ID {job_id} not found.")

        eval_res = EligibilityService.evaluate(student, job)
        missing_skills = eval_res["missing_skills"]
        company_name = job.get("company_name", "")

        # Find questions matching missing skills or the hiring company
        recommended_questions: List[Dict[str, Any]] = []

        # 1. Company-tagged questions
        if company_name:
            comp_qs = self.question_repo.list_questions(company=company_name, limit=5)
            recommended_questions.extend(comp_qs)

        # 2. Topic-based questions for missing skills
        for skill in missing_skills:
            skill_qs = self.question_repo.list_questions(topic=skill, limit=3)
            for q in skill_qs:
                if q["id"] not in {rq["id"] for rq in recommended_questions}:
                    recommended_questions.append(q)

        # Fallback to general questions if recommendations are sparse
        if len(recommended_questions) < 3:
            random_fallback = self.question_repo.get_random_questions(limit=3)
            for q in random_fallback:
                if q["id"] not in {rq["id"] for rq in recommended_questions}:
                    recommended_questions.append(q)

        return {
            "student_id": student["id"],
            "student_name": student["name"],
            "target_role": job["role_title"],
            "company_name": company_name,
            "skill_match_percentage": eval_res["skill_match_percentage"],
            "matched_skills": eval_res["matched_skills"],
            "missing_skills": missing_skills,
            "recommended_questions": recommended_questions[:8],
        }

    def generate_mock_interview_plan(
        self,
        student_id: int,
        target_company: Optional[str] = None,
        num_questions: int = 5,
    ) -> Dict[str, Any]:
        """Generate a balanced set of interview questions (DSA, Core CS, Behavioral) for practice."""
        student = self.student_repo.get_by_id(student_id)
        if not student:
            raise ValueError(f"Student with ID {student_id} not found.")

        selected_questions: List[Dict[str, Any]] = []

        # Try company-specific questions first if target company is given
        if target_company:
            company_qs = self.question_repo.list_questions(company=target_company, limit=num_questions)
            selected_questions.extend(company_qs)

        # Ensure representation across key categories
        categories = ["DSA", "Core_CS", "Behavioral_HR", "System_Design", "Database"]
        for cat in categories:
            if len(selected_questions) >= num_questions:
                break
            cat_qs = self.question_repo.list_questions(category=cat, limit=2)
            for q in cat_qs:
                if q["id"] not in {sq["id"] for sq in selected_questions}:
                    selected_questions.append(q)
                    if len(selected_questions) >= num_questions:
                        break

        # If still short, sample random questions
        if len(selected_questions) < num_questions:
            extra = self.question_repo.get_random_questions(limit=num_questions - len(selected_questions))
            for q in extra:
                if q["id"] not in {sq["id"] for sq in selected_questions}:
                    selected_questions.append(q)

        return {
            "student_id": student["id"],
            "student_name": student["name"],
            "target_company": target_company or "General Tech Company",
            "plan_questions": selected_questions,
            "instructions": "Answer each question clearly. Use the STAR method for behavioral questions and explain time/space complexity for technical questions.",
        }

    def log_and_evaluate_mock(
        self,
        student_id: int,
        topic: str,
        score: float,
        feedback: str,
        transcript: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log mock interview results and return historical progress."""
        student = self.student_repo.get_by_id(student_id)
        if not student:
            raise ValueError(f"Student with ID {student_id} not found.")

        session = self.question_repo.log_mock_interview(
            student_id=student_id,
            topic=topic,
            score=score,
            feedback=feedback,
            transcript=transcript,
        )

        all_sessions = self.question_repo.list_mock_interviews_for_student(student_id)
        scores = [s["score"] for s in all_sessions if s["score"] is not None]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

        return {
            "session": session,
            "total_mock_sessions": len(all_sessions),
            "average_score": avg_score,
            "readiness_verdict": "High Readiness" if avg_score >= 80 else ("Moderate" if avg_score >= 60 else "Needs Practice"),
        }

