"""Application lifecycle and interview pipeline tracking service."""

import sqlite3
from typing import Any, Dict, List, Optional

from src.db.repositories.applications import ApplicationRepository
from src.db.repositories.companies import CompanyRepository
from src.db.repositories.students import StudentRepository
from src.services.eligibility import EligibilityService


class TrackerService:
    """Manages placement application workflows, interview pipelines, and candidate funnels."""

    VALID_TRANSITIONS = {
        "applied": {"shortlisted", "rejected", "withdrawn"},
        "shortlisted": {"oa_cleared", "interview_scheduled", "rejected", "withdrawn"},
        "oa_cleared": {"interview_scheduled", "offered", "rejected", "withdrawn"},
        "interview_scheduled": {"interview_scheduled", "oa_cleared", "offered", "rejected", "withdrawn"},
        "offered": {"withdrawn"},
        "rejected": set(),
        "withdrawn": set(),
    }

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.app_repo = ApplicationRepository(conn)
        self.student_repo = StudentRepository(conn)
        self.company_repo = CompanyRepository(conn)

    def apply_to_job(
        self,
        student_id: int,
        job_id: int,
        notes: Optional[str] = None,
        enforce_eligibility: bool = True,
    ) -> Dict[str, Any]:
        """Submit a job application with eligibility verification.

        Raises:
            ValueError: If student or job does not exist, or if student is not eligible.
        """
        student = self.student_repo.get_by_id(student_id)
        if not student:
            raise ValueError(f"Student with ID {student_id} not found.")

        job = self.company_repo.get_job_by_id(job_id)
        if not job:
            raise ValueError(f"Job posting with ID {job_id} not found.")

        if job.get("status") != "open":
            raise ValueError(f"Job posting '{job['role_title']}' is currently '{job.get('status')}', not open.")

        # Check existing application
        existing = self.app_repo.get_by_student_and_job(student_id, job_id)
        if existing:
            raise ValueError(f"Student already has an active application (ID {existing['id']}) for this job.")

        # Eligibility check
        if enforce_eligibility:
            eval_result = EligibilityService.evaluate(student, job)
            if not eval_result["is_eligible"]:
                reasons = "; ".join(eval_result["disqualification_reasons"])
                raise ValueError(f"Student is not eligible for this job: {reasons}")

        return self.app_repo.apply(student_id, job_id, notes=notes)

    def advance_stage(
        self,
        application_id: int,
        next_status: str,
        current_stage: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Advance an application to its next pipeline state."""
        app = self.app_repo.get_by_id(application_id)
        if not app:
            raise ValueError(f"Application with ID {application_id} not found.")

        current_status = app["status"]
        allowed = self.VALID_TRANSITIONS.get(current_status, set())

        if next_status not in allowed and next_status != current_status:
            raise ValueError(
                f"Invalid transition from '{current_status}' to '{next_status}'. "
                f"Allowed target states: {allowed or 'None'}"
            )

        updated = self.app_repo.update_status(
            application_id=application_id,
            status=next_status,
            current_stage=current_stage,
            notes=notes,
        )
        return updated  # type: ignore

    def schedule_interview_round(
        self,
        application_id: int,
        round_type: str,
        scheduled_at: Optional[str] = None,
        interviewer_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Schedule the next chronological interview round for an application."""
        app = self.app_repo.get_by_id(application_id)
        if not app:
            raise ValueError(f"Application with ID {application_id} not found.")

        existing_rounds = self.app_repo.list_rounds_for_application(application_id)
        next_round_number = len(existing_rounds) + 1

        return self.app_repo.schedule_round(
            application_id=application_id,
            round_number=next_round_number,
            round_type=round_type,
            scheduled_at=scheduled_at,
            interviewer_notes=interviewer_notes,
        )

    def record_interview_outcome(
        self,
        round_id: int,
        status: str,
        feedback: Optional[str] = None,
        interviewer_notes: Optional[str] = None,
        auto_update_application: bool = True,
    ) -> Dict[str, Any]:
        """Record the outcome of an interview round and optionally update application status."""
        round_record = self.app_repo.update_round_result(
            round_id=round_id,
            status=status,
            feedback=feedback,
            interviewer_notes=interviewer_notes,
        )
        if not round_record:
            raise ValueError(f"Interview round with ID {round_id} not found.")

        if auto_update_application:
            app_id = round_record["application_id"]
            if status == "failed":
                self.app_repo.update_status(
                    application_id=app_id,
                    status="rejected",
                    current_stage=f"Rejected in Round {round_record['round_number']} ({round_record['round_type']})",
                )
            elif status == "cleared":
                self.app_repo.update_status(
                    application_id=app_id,
                    status="interview_scheduled",
                    current_stage=f"Cleared Round {round_record['round_number']} ({round_record['round_type']})",
                )

        return round_record

    def get_student_placement_summary(self, student_id: int) -> Dict[str, Any]:
        """Compute an end-to-end placement summary and metrics for a student."""
        student = self.student_repo.get_by_id(student_id)
        if not student:
            raise ValueError(f"Student with ID {student_id} not found.")

        applications = self.app_repo.list_applications(student_id=student_id)
        upcoming_interviews = self.app_repo.list_upcoming_interviews(student_id=student_id)

        status_counts: Dict[str, int] = {
            "applied": 0,
            "shortlisted": 0,
            "oa_cleared": 0,
            "interview_scheduled": 0,
            "offered": 0,
            "rejected": 0,
            "withdrawn": 0,
        }

        offers: List[Dict[str, Any]] = []

        for app in applications:
            st = app.get("status", "applied")
            status_counts[st] = status_counts.get(st, 0) + 1
            if st == "offered":
                offers.append({
                    "application_id": app["id"],
                    "company_name": app["company_name"],
                    "role_title": app["role_title"],
                    "ctc_lpa": app["ctc_lpa"],
                })

        offers.sort(key=lambda x: x["ctc_lpa"], reverse=True)

        return {
            "student_id": student["id"],
            "student_name": student["name"],
            "usn": student["usn"],
            "cgpa": student["cgpa"],
            "branch": student["branch"],
            "total_applications": len(applications),
            "status_breakdown": status_counts,
            "upcoming_interviews_count": len(upcoming_interviews),
            "offers_count": len(offers),
            "highest_offer_ctc_lpa": offers[0]["ctc_lpa"] if offers else None,
            "offers": offers,
            "recent_applications": applications[:5],
        }

    def get_drive_funnel(self, job_id: int) -> Dict[str, Any]:
        """Compute candidate conversion funnel statistics for a job drive."""
        job = self.company_repo.get_job_by_id(job_id)
        if not job:
            raise ValueError(f"Job posting with ID {job_id} not found.")

        applications = self.app_repo.list_applications(job_id=job_id)

        funnel = {
            "job_id": job["id"],
            "role_title": job["role_title"],
            "company_name": job["company_name"],
            "ctc_lpa": job["ctc_lpa"],
            "total_applicants": len(applications),
            "shortlisted_or_beyond": 0,
            "interviewing": 0,
            "offered": 0,
            "rejected": 0,
        }

        for app in applications:
            st = app["status"]
            if st != "applied":
                funnel["shortlisted_or_beyond"] += 1
            if st == "interview_scheduled":
                funnel["interviewing"] += 1
            if st == "offered":
                funnel["offered"] += 1
            if st == "rejected":
                funnel["rejected"] += 1

        return funnel
