"""Application and Interview Schedule repository for SQLite CRUD operations."""

import sqlite3
from typing import Any, Dict, List, Optional


class ApplicationRepository:
    """Data access repository for student job applications and interview schedules."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # --- Application Operations ---

    def apply(
        self,
        student_id: int,
        job_id: int,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit an application for a student to a job posting."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO applications (student_id, job_id, status, current_stage, notes)
            VALUES (?, ?, 'applied', 'Application Submitted', ?);
            """,
            (student_id, job_id, notes),
        )
        application_id = cursor.lastrowid
        return self.get_by_id(application_id)  # type: ignore

    def get_by_id(self, application_id: int) -> Optional[Dict[str, Any]]:
        """Fetch application with student and job/company details."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT
                a.*,
                s.usn AS student_usn,
                s.name AS student_name,
                s.email AS student_email,
                s.branch AS student_branch,
                s.cgpa AS student_cgpa,
                j.role_title,
                j.ctc_lpa,
                j.location AS job_location,
                c.id AS company_id,
                c.name AS company_name
            FROM applications a
            JOIN students s ON a.student_id = s.id
            JOIN jobs j ON a.job_id = j.id
            JOIN companies c ON j.company_id = c.id
            WHERE a.id = ?;
            """,
            (application_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_by_student_and_job(self, student_id: int, job_id: int) -> Optional[Dict[str, Any]]:
        """Fetch an application by the student and job compound key."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id FROM applications WHERE student_id = ? AND job_id = ?;
            """,
            (student_id, job_id),
        )
        row = cursor.fetchone()
        return self.get_by_id(row["id"]) if row else None

    def list_applications(
        self,
        student_id: Optional[int] = None,
        job_id: Optional[int] = None,
        company_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List applications with optional filters."""
        query = """
            SELECT
                a.*,
                s.usn AS student_usn,
                s.name AS student_name,
                s.branch AS student_branch,
                s.cgpa AS student_cgpa,
                j.role_title,
                j.ctc_lpa,
                c.id AS company_id,
                c.name AS company_name
            FROM applications a
            JOIN students s ON a.student_id = s.id
            JOIN jobs j ON a.job_id = j.id
            JOIN companies c ON j.company_id = c.id
            WHERE 1=1
        """
        params: List[Any] = []

        if student_id:
            query += " AND a.student_id = ?"
            params.append(student_id)
        if job_id:
            query += " AND a.job_id = ?"
            params.append(job_id)
        if company_id:
            query += " AND c.id = ?"
            params.append(company_id)
        if status:
            query += " AND a.status = ?"
            params.append(status)

        query += " ORDER BY a.updated_at DESC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        cursor = self.conn.cursor()
        cursor.execute(query, tuple(params))
        return [dict(row) for row in cursor.fetchall()]

    def update_status(
        self,
        application_id: int,
        status: str,
        current_stage: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update the status and current stage of an application."""
        valid_statuses = {"applied", "shortlisted", "oa_cleared", "interview_scheduled", "offered", "rejected", "withdrawn"}
        if status not in valid_statuses:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {valid_statuses}")

        updates = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
        params: List[Any] = [status]

        if current_stage is not None:
            updates.append("current_stage = ?")
            params.append(current_stage)
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)

        params.append(application_id)
        sql = f"UPDATE applications SET {', '.join(updates)} WHERE id = ?;"
        cursor = self.conn.cursor()
        cursor.execute(sql, tuple(params))
        return self.get_by_id(application_id)

    def delete(self, application_id: int) -> bool:
        """Delete an application and its interview rounds."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM applications WHERE id = ?;", (application_id,))
        return cursor.rowcount > 0

    # --- Interview Schedules & Rounds Operations ---

    def schedule_round(
        self,
        application_id: int,
        round_number: int,
        round_type: str,
        scheduled_at: Optional[str] = None,
        interviewer_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Schedule a new interview round for an application."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO interview_rounds (application_id, round_number, round_type, scheduled_at, interviewer_notes)
            VALUES (?, ?, ?, ?, ?);
            """,
            (application_id, round_number, round_type, scheduled_at, interviewer_notes),
        )
        round_id = cursor.lastrowid

        # Update application stage automatically
        self.update_status(
            application_id,
            status="interview_scheduled",
            current_stage=f"Round {round_number}: {round_type}",
        )

        return self.get_round_by_id(round_id)  # type: ignore

    def get_round_by_id(self, round_id: int) -> Optional[Dict[str, Any]]:
        """Fetch an interview round by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM interview_rounds WHERE id = ?;", (round_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_rounds_for_application(self, application_id: int) -> List[Dict[str, Any]]:
        """List all interview rounds for a specific application in chronological order."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM interview_rounds
            WHERE application_id = ?
            ORDER BY round_number ASC;
            """,
            (application_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def update_round_result(
        self,
        round_id: int,
        status: str,
        feedback: Optional[str] = None,
        interviewer_notes: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update interview round outcome (pending, cleared, failed, cancelled)."""
        valid_statuses = {"pending", "cleared", "failed", "cancelled"}
        if status not in valid_statuses:
            raise ValueError(f"Invalid round status '{status}'. Must be one of: {valid_statuses}")

        updates = ["status = ?"]
        params: List[Any] = [status]

        if feedback is not None:
            updates.append("feedback = ?")
            params.append(feedback)
        if interviewer_notes is not None:
            updates.append("interviewer_notes = ?")
            params.append(interviewer_notes)

        params.append(round_id)
        sql = f"UPDATE interview_rounds SET {', '.join(updates)} WHERE id = ?;"
        cursor = self.conn.cursor()
        cursor.execute(sql, tuple(params))
        return self.get_round_by_id(round_id)

    def list_upcoming_interviews(self, student_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """List all pending interview rounds with company and role info."""
        query = """
            SELECT
                r.*,
                a.student_id,
                s.name AS student_name,
                s.usn AS student_usn,
                j.role_title,
                c.name AS company_name
            FROM interview_rounds r
            JOIN applications a ON r.application_id = a.id
            JOIN students s ON a.student_id = s.id
            JOIN jobs j ON a.job_id = j.id
            JOIN companies c ON j.company_id = c.id
            WHERE r.status = 'pending'
        """
        params: List[Any] = []
        if student_id:
            query += " AND a.student_id = ?"
            params.append(student_id)

        query += " ORDER BY r.scheduled_at ASC NULLS LAST;"

        cursor = self.conn.cursor()
        cursor.execute(query, tuple(params))
        return [dict(row) for row in cursor.fetchall()]

