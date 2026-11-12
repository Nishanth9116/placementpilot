"""Student repository for SQLite CRUD operations."""

import json
import sqlite3
from typing import Any, Dict, List, Optional


class StudentRepository:
    """Data access repository for students."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(
        self,
        usn: str,
        name: str,
        email: str,
        branch: str,
        cgpa: float,
        graduation_year: int = 2025,
        skills: Optional[List[str]] = None,
        resume_path: Optional[str] = None,
        phone: Optional[str] = None,
        department: Optional[str] = None,
        year_of_study: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Insert a new student profile."""
        skills_json = json.dumps(skills or [])
        clean_dept = (department or branch).strip()
        clean_branch = (branch or department).strip().upper()
        clean_year_study = str(year_of_study or graduation_year)

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO students (
                usn, name, email, phone, branch, department, year_of_study,
                cgpa, graduation_year, skills, resume_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                usn.strip(),
                name.strip(),
                email.strip(),
                phone.strip() if phone else None,
                clean_branch,
                clean_dept,
                clean_year_study,
                cgpa,
                graduation_year,
                skills_json,
                resume_path,
            ),
        )
        student_id = cursor.lastrowid
        return self.get_by_id(student_id)  # type: ignore

    def get_by_id(self, student_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a student by primary key ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM students WHERE id = ?;", (student_id,))
        row = cursor.fetchone()
        return self._format_row(row) if row else None

    def get_by_usn(self, usn: str) -> Optional[Dict[str, Any]]:
        """Fetch a student by university roll number (USN)."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM students WHERE LOWER(usn) = LOWER(?);", (usn.strip(),))
        row = cursor.fetchone()
        return self._format_row(row) if row else None

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Fetch a student by email address."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM students WHERE LOWER(email) = LOWER(?);", (email.strip(),))
        row = cursor.fetchone()
        return self._format_row(row) if row else None

    def authenticate(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Find a student by either USN/Register Number or Email."""
        clean_id = identifier.strip()
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM students 
            WHERE LOWER(usn) = LOWER(?) OR LOWER(email) = LOWER(?);
            """,
            (clean_id, clean_id),
        )
        row = cursor.fetchone()
        return self._format_row(row) if row else None

    def list_all(
        self,
        branch: Optional[str] = None,
        department: Optional[str] = None,
        min_cgpa: Optional[float] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List students with optional branch, department, and CGPA filters."""
        query = "SELECT * FROM students WHERE 1=1"
        params: List[Any] = []

        target_dept = department or branch
        if target_dept:
            query += " AND (LOWER(branch) = LOWER(?) OR LOWER(department) = LOWER(?))"
            params.extend([target_dept.strip(), target_dept.strip()])
        if min_cgpa is not None:
            query += " AND cgpa >= ?"
            params.append(min_cgpa)

        query += " ORDER BY cgpa DESC, name ASC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        cursor = self.conn.cursor()
        cursor.execute(query, tuple(params))
        return [self._format_row(row) for row in cursor.fetchall()]

    def update(
        self,
        student_id: int,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        branch: Optional[str] = None,
        department: Optional[str] = None,
        year_of_study: Optional[str] = None,
        cgpa: Optional[float] = None,
        graduation_year: Optional[int] = None,
        skills: Optional[List[str]] = None,
        resume_path: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update fields of an existing student."""
        updates: List[str] = []
        params: List[Any] = []

        if name is not None:
            updates.append("name = ?")
            params.append(name.strip())
        if email is not None:
            updates.append("email = ?")
            params.append(email.strip())
        if phone is not None:
            updates.append("phone = ?")
            params.append(phone.strip())
        if branch is not None:
            updates.append("branch = ?")
            params.append(branch.strip().upper())
        if department is not None:
            updates.append("department = ?")
            params.append(department.strip())
            if branch is None:
                updates.append("branch = ?")
                params.append(department.strip().upper())
        if year_of_study is not None:
            updates.append("year_of_study = ?")
            params.append(str(year_of_study))
        if cgpa is not None:
            updates.append("cgpa = ?")
            params.append(cgpa)
        if graduation_year is not None:
            updates.append("graduation_year = ?")
            params.append(graduation_year)
        if skills is not None:
            updates.append("skills = ?")
            params.append(json.dumps(skills))
        if resume_path is not None:
            updates.append("resume_path = ?")
            params.append(resume_path)

        if not updates:
            return self.get_by_id(student_id)

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(student_id)

        sql = f"UPDATE students SET {', '.join(updates)} WHERE id = ?;"
        cursor = self.conn.cursor()
        cursor.execute(sql, tuple(params))
        return self.get_by_id(student_id)

    def delete(self, student_id: int) -> bool:
        """Delete student and all associated cascade records."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM students WHERE id = ?;", (student_id,))
        return cursor.rowcount > 0

    @staticmethod
    def _format_row(row: sqlite3.Row) -> Dict[str, Any]:
        data = dict(row)
        if "skills" in data and isinstance(data["skills"], str):
            try:
                data["skills"] = json.loads(data["skills"])
            except json.JSONDecodeError:
                data["skills"] = []
        # Ensure department defaults to branch if empty
        if not data.get("department"):
            data["department"] = data.get("branch", "")
        # Ensure year_of_study defaults to graduation_year if empty
        if not data.get("year_of_study") and data.get("graduation_year"):
            data["year_of_study"] = str(data["graduation_year"])
        return data
