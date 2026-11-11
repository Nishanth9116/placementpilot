"""Company and Job repository for SQLite CRUD operations."""

import json
import sqlite3
from typing import Any, Dict, List, Optional


class CompanyRepository:
    """Data access repository for companies and campus recruitment job drives."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # --- Company Operations ---

    def create_company(
        self,
        name: str,
        website: Optional[str] = None,
        industry: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new hiring company."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO companies (name, website, industry, description)
            VALUES (?, ?, ?, ?);
            """,
            (name, website, industry, description),
        )
        company_id = cursor.lastrowid
        return self.get_company_by_id(company_id)  # type: ignore

    def get_company_by_id(self, company_id: int) -> Optional[Dict[str, Any]]:
        """Fetch company by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM companies WHERE id = ?;", (company_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_company_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Fetch company by name."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM companies WHERE LOWER(name) = LOWER(?);", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_companies(self, industry: Optional[str] = None) -> List[Dict[str, Any]]:
        """List registered companies."""
        query = "SELECT * FROM companies WHERE 1=1"
        params: List[Any] = []
        if industry:
            query += " AND industry = ?"
            params.append(industry)
        query += " ORDER BY name ASC;"

        cursor = self.conn.cursor()
        cursor.execute(query, tuple(params))
        return [dict(row) for row in cursor.fetchall()]

    def update_company(
        self,
        company_id: int,
        name: Optional[str] = None,
        website: Optional[str] = None,
        industry: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update company information."""
        updates: List[str] = []
        params: List[Any] = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if website is not None:
            updates.append("website = ?")
            params.append(website)
        if industry is not None:
            updates.append("industry = ?")
            params.append(industry)
        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if not updates:
            return self.get_company_by_id(company_id)

        params.append(company_id)
        sql = f"UPDATE companies SET {', '.join(updates)} WHERE id = ?;"
        cursor = self.conn.cursor()
        cursor.execute(sql, tuple(params))
        return self.get_company_by_id(company_id)

    def delete_company(self, company_id: int) -> bool:
        """Delete company and all associated jobs/applications via CASCADE."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM companies WHERE id = ?;", (company_id,))
        return cursor.rowcount > 0

    # --- Job Posting Operations ---

    def create_job(
        self,
        company_id: int,
        role_title: str,
        ctc_lpa: float,
        job_description: Optional[str] = None,
        location: str = "On-site",
        min_cgpa: float = 0.0,
        allowed_branches: Optional[List[str]] = None,
        required_skills: Optional[List[str]] = None,
        application_deadline: Optional[str] = None,
        status: str = "open",
    ) -> Dict[str, Any]:
        """Create a job posting for a company."""
        branches_json = json.dumps([b.upper() for b in (allowed_branches or [])])
        skills_json = json.dumps(required_skills or [])

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO jobs (
                company_id, role_title, job_description, ctc_lpa, location,
                min_cgpa, allowed_branches, required_skills, application_deadline, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                company_id,
                role_title,
                job_description,
                ctc_lpa,
                location,
                min_cgpa,
                branches_json,
                skills_json,
                application_deadline,
                status,
            ),
        )
        job_id = cursor.lastrowid
        return self.get_job_by_id(job_id)  # type: ignore

    def get_job_by_id(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a job posting along with company name."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT j.*, c.name AS company_name, c.website AS company_website
            FROM jobs j
            JOIN companies c ON j.company_id = c.id
            WHERE j.id = ?;
            """,
            (job_id,),
        )
        row = cursor.fetchone()
        return self._format_job_row(row) if row else None

    def list_jobs(
        self,
        company_id: Optional[int] = None,
        status: Optional[str] = None,
        min_ctc: Optional[float] = None,
        branch: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List job drives with optional filters."""
        query = """
            SELECT j.*, c.name AS company_name, c.website AS company_website
            FROM jobs j
            JOIN companies c ON j.company_id = c.id
            WHERE 1=1
        """
        params: List[Any] = []

        if company_id:
            query += " AND j.company_id = ?"
            params.append(company_id)
        if status:
            query += " AND j.status = ?"
            params.append(status)
        if min_ctc is not None:
            query += " AND j.ctc_lpa >= ?"
            params.append(min_ctc)

        query += " ORDER BY j.ctc_lpa DESC, j.created_at DESC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        cursor = self.conn.cursor()
        cursor.execute(query, tuple(params))
        jobs = [self._format_job_row(row) for row in cursor.fetchall()]

        if branch:
            branch_upper = branch.upper()
            jobs = [j for j in jobs if not j["allowed_branches"] or branch_upper in j["allowed_branches"]]

        return jobs

    def update_job(
        self,
        job_id: int,
        role_title: Optional[str] = None,
        job_description: Optional[str] = None,
        ctc_lpa: Optional[float] = None,
        location: Optional[str] = None,
        min_cgpa: Optional[float] = None,
        allowed_branches: Optional[List[str]] = None,
        required_skills: Optional[List[str]] = None,
        application_deadline: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update job drive details."""
        updates: List[str] = []
        params: List[Any] = []

        if role_title is not None:
            updates.append("role_title = ?")
            params.append(role_title)
        if job_description is not None:
            updates.append("job_description = ?")
            params.append(job_description)
        if ctc_lpa is not None:
            updates.append("ctc_lpa = ?")
            params.append(ctc_lpa)
        if location is not None:
            updates.append("location = ?")
            params.append(location)
        if min_cgpa is not None:
            updates.append("min_cgpa = ?")
            params.append(min_cgpa)
        if allowed_branches is not None:
            updates.append("allowed_branches = ?")
            params.append(json.dumps([b.upper() for b in allowed_branches]))
        if required_skills is not None:
            updates.append("required_skills = ?")
            params.append(json.dumps(required_skills))
        if application_deadline is not None:
            updates.append("application_deadline = ?")
            params.append(application_deadline)
        if status is not None:
            updates.append("status = ?")
            params.append(status)

        if not updates:
            return self.get_job_by_id(job_id)

        params.append(job_id)
        sql = f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?;"
        cursor = self.conn.cursor()
        cursor.execute(sql, tuple(params))
        return self.get_job_by_id(job_id)

    def delete_job(self, job_id: int) -> bool:
        """Delete a job posting and cascade delete its applications."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM jobs WHERE id = ?;", (job_id,))
        return cursor.rowcount > 0

    @staticmethod
    def _format_job_row(row: sqlite3.Row) -> Dict[str, Any]:
        data = dict(row)
        for key in ("allowed_branches", "required_skills"):
            if key in data and isinstance(data[key], str):
                try:
                    data[key] = json.loads(data[key])
                except json.JSONDecodeError:
                    data[key] = []
        return data

